import os
import time
import uuid
import base64
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from data.user import User
from data.cache import get_problem, start as start_cache
from data.ai import check_answer, get_ai_response, NoKeyError
from collections import defaultdict
from trans_ru import ACHIEVEMENTS_RU, SUBJECTS_RU
from config import SUBJECTS, AI_COOLDOWN
from data.db_session import create_session

start_cache()

_ai_last_call: dict[str, float] = defaultdict(float)
_executor = ThreadPoolExecutor(max_workers=8)
_jobs: dict[str, dict] = {}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'very_secret')

@app.route('/')
def index():
    return redirect(url_for('profile') if current_user.is_authenticated else url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('Username and password are required.')
            return render_template('auth.html', mode='register')
        user = User.register(username, password)
        if not user:
            flash('Username already taken.')
            return render_template('auth.html', mode='register')
        login_user(user)
        return redirect(url_for('profile'))
    return render_template('auth.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = User.authenticate(username, password)
        if not user:
            flash('Invalid credentials.')
            return render_template('auth.html', mode='login')
        login_user(user)
        return redirect(url_for('profile'))
    return render_template('auth.html', mode='login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    if session.pop('answer_verified', None):
        session['correct_in_a_row'] = session.get('correct_in_a_row', 0) + 1
        p = session.get('current_problem')
        if p:
            current_user.mark_solved(p['id'], p['subject'], p['difficulty'])
    current_user.update_achievements(current_user, session)
    return render_template('profile.html', username=current_user.username, stats=current_user.get_stats(), subjects=SUBJECTS,
                        lang=current_user.get_lang(), trans=[SUBJECTS_RU, ACHIEVEMENTS_RU], achievements=current_user.get_achievements())

@app.route('/achievements')
@login_required
def achievements():
    return render_template('achievements.html', username=current_user.username,
                           lang=current_user.get_lang(), trans=[SUBJECTS_RU, ACHIEVEMENTS_RU],
                           achievements=current_user.get_achievements())

@app.route('/set_language', methods=['POST'])
@login_required
def set_language():
    current_user.set_lang()
    return jsonify({'status': 'ok'})

@app.route('/problem', methods=['GET', 'POST'])
@login_required
def problem():
    if request.method == 'POST':
        subject = ' '.join([word.capitalize() for word in request.form.get('subject', '').split()])
        difficulty = request.form.get('difficulty', 'any').lower()

        if subject not in SUBJECTS:
            flash('Invalid subject.')
            return redirect(url_for('profile'))

        if difficulty != 'any' and (not difficulty.isdigit() or int(difficulty) not in range(1, 11)):
            flash('Invalid difficulty.')
            return redirect(url_for('profile'))

        p = get_problem(subject, difficulty, current_user.get_solved(), current_user.get_lang())
        if not p:
            flash('No unsolved problems found. Cache may still be loading - try again in about 10 minutes.')
            return redirect(url_for('profile'))

        session['current_problem'] = p
        session['problem_subject'] = subject
        session['problem_difficulty'] = difficulty
        return redirect(url_for('problem'))

    p = session.get('current_problem')
    if not p:
        return redirect(url_for('profile'))
    print(p)
    return render_template('problem.html', problem=p, lang=current_user.get_lang())


@app.route('/problem/confirm', methods=['POST'])
@login_required
def problem_confirm():
    p = session.get('current_problem')
    if not p:
        return redirect(url_for('profile'))
    if not session.get('answer_verified'):
        flash('You must verify your answer before marking as solved.')
        session['correct_in_a_row'] = 0
        return redirect(url_for('problem'))
    current_user.mark_solved(p['id'], p['subject'], p['difficulty'])
    session.pop('current_problem', None)
    session.pop('answer_verified', None)
    session['correct_in_a_row'] = session.get('correct_in_a_row', 0) + 1
    flash('Problem marked as solved!')
    return redirect(url_for('profile'))

@app.route('/problem/ai', methods=['POST'])
@login_required
def problem_ai():
    p = session.get('current_problem')
    if not p:
        return jsonify({'error': 'No active problem.'}), 400

    mode = request.form.get('mode')
    user_answer = request.form.get('answer', '').strip()
    if not user_answer and mode == 'check':
        return jsonify({'error': 'No answer provided.'}), 400

    if mode not in ('check', 'hint', 'steps', 'explain'):
        return jsonify({'error': 'Invalid mode.'}), 400

    uid = str(current_user.id)
    now = time.time()
    elapsed = now - _ai_last_call[uid]
    if elapsed < AI_COOLDOWN:
        wait = int(AI_COOLDOWN - elapsed)
        return jsonify({'error': 'rate_limited', 'wait': wait}), 429

    _ai_last_call[uid] = now

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {'status': 'pending'}

    user_lang = current_user.get_lang()

    def run(job_id, p, mode, user_answer, user_lang, uid):
        try:
            if mode == 'check':
                result = check_answer(p, user_answer, user_lang)
                if result['verdict'] == 'CORRECT':
                    _jobs[job_id] = {'status': 'done', 'verdict': 'CORRECT', 'text': result['text']}
                else:
                    _jobs[job_id] = {'status': 'done', 'verdict': result['verdict'], 'text': result['text']}
            else:
                text = get_ai_response(p, mode, user_answer, user_lang)
                _jobs[job_id] = {'status': 'done', 'text': text}
        except NoKeyError:
            _jobs[job_id] = {'status': 'error', 'error': 'AI is not configured.'}
        except Exception as e:
            _jobs[job_id] = {'status': 'error', 'error': str(e)}

    _executor.submit(run, job_id, p, mode, user_answer, user_lang, uid)
    return jsonify({'job_id': job_id}), 202


@app.route('/problem/ai/poll/<job_id>', methods=['GET'])
@login_required
def problem_ai_poll(job_id):
    job = _jobs.get(job_id)
    if job is None:
        return jsonify({'error': 'Unknown job.'}), 404
    if job['status'] == 'pending':
        return jsonify({'status': 'pending'}), 202
    if job['status'] == 'error':
        _jobs.pop(job_id, None)
        return jsonify({'error': job['error']}), 503
    if job['status'] == 'done' and job.get('verdict') == 'CORRECT':
        session['answer_verified'] = True
    result = dict(job)
    _jobs.pop(job_id, None)
    return jsonify(result)

@app.route('/user/avatar')
@login_required
def user_avatar():
    return jsonify({
        'username': current_user.username,
        'avatar_color': current_user.get_avatar_color(),
        'initials': current_user.username[:2].upper()
    })

@app.route('/user/update_avatar_color', methods=['POST'])
@login_required
def update_avatar_color():
    data = request.get_json()
    color = data.get('color')
    if color:
        with create_session() as s:
            user = s.get(User, current_user.id)
            user.avatar_color = color
            s.commit()
    return jsonify({'status': 'ok'})

@app.route('/user/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')
    if not file or file.filename == '':
        return jsonify({'error': 'No file provided.'}), 400
    if not file.content_type.startswith('image/'):
        return jsonify({'error': 'File must be an image.'}), 400
    data = file.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        return jsonify({'error': 'Image must be under 2 MB.'}), 400
    data_url = 'data:' + file.content_type + ';base64,' + base64.b64encode(data).decode()
    current_user.set_avatar_image(data_url)
    return jsonify({'status': 'ok', 'data_url': data_url})

@app.route('/user/clear_avatar', methods=['POST'])
@login_required
def clear_avatar():
    current_user.clear_avatar_image()
    return jsonify({'status': 'ok'})