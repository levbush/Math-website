import json
import pickle
import random
import threading
import time
import tempfile
import os
from datetime import datetime
from huggingface_hub import hf_hub_download, list_repo_files
from config import SUBJECTS, repo_id, repo_type, REFRESH_INTERVAL, CACHE_FILE


_lock = threading.Lock()
_pool: dict[tuple, list] = {}
_tmp_dir = tempfile.mkdtemp(prefix='mathbot_cache_')

BLACKLIST = ['an educational piece', '¶', "Here's an extract", 'Welsh teams']

MAX_PROBLEMS_PER_KEY = 1000


def _is_valid(question: str) -> bool:
    return not any(phrase in question for phrase in BLACKLIST)


def _load_file(filepath: str, exclude_ids: set) -> list:
    problems = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                p = json.loads(line)
                if p['id'] not in exclude_ids and _is_valid(p['question']):
                    problems.append(p)
            except json.JSONDecodeError:
                continue
    return problems


def _download_for(subject: str, difficulty: str) -> list:
    subdir = f'{subject}/{difficulty}/' if difficulty != 'any' else f'{subject}/'

    try:
        all_files = list_repo_files(repo_id, repo_type=repo_type)
    except Exception as e:
        print(f'Cache: failed to list repo files: {e}')
        return []

    files = [
        f for f in all_files
        if f.startswith(subdir)
        and not f.endswith('/')
        and not f.endswith('whole.jsonl')
    ]

    if not files:
        print(f'Cache: no files for {subject} {difficulty}')
        return []

    random.shuffle(files)

    collected = []
    seen_ids = set()

    for file in files:
        if len(collected) >= MAX_PROBLEMS_PER_KEY:
            break

        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=file,
                repo_type=repo_type,
                local_dir=_tmp_dir
            )

            problems = _load_file(local_path, seen_ids)

            for p in problems:
                if len(collected) >= MAX_PROBLEMS_PER_KEY:
                    break
                collected.append(p)
                seen_ids.add(p['id'])

        except Exception as e:
            print(f'Cache: failed to download {file}: {e}')
            continue

    print(f'Cache: {subject} {difficulty} -> {len(collected)} problems')

    return collected


def _save_pool(pool: dict):
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(pool, f)
    except Exception as e:
        print(f'Cache: failed to save pool: {e}')


def _load_pool() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'rb') as f:
            pool = pickle.load(f)
        print(f'Cache: loaded {sum(len(v) for v in pool.values())} problems from disk')
        return pool
    except Exception as e:
        print(f'Cache: failed to load pool from disk: {e}')
        return {}


def _refresh():
    new_pool = {}

    for subject in SUBJECTS:
        for difficulty in [str(d) for d in range(1, 11)]:
            key = (subject, difficulty)
            problems = _download_for(subject, difficulty)

            new_pool[key] = problems

    with _lock:
        _pool.clear()
        _pool.update(new_pool)

    _save_pool(new_pool)


def _background_loop():
    while True:
        try:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Cache: refreshing...')
            _refresh()
            total = sum(len(v) for v in _pool.values())
            print(f'[{datetime.now().strftime("%H:%M:%S")}] Cache: done, {total} problems loaded')
        except Exception as e:
            print(f'Cache: refresh error: {e}')

        time.sleep(REFRESH_INTERVAL)


def start():
    saved = _load_pool()
    func = _background_loop

    if saved:
        with _lock:
            _pool.update(saved)

        def delayed():
            time.sleep(REFRESH_INTERVAL)
            _background_loop()

        func = delayed

    t = threading.Thread(target=func, daemon=True)
    t.start()


def get_problem(subject: str, difficulty: str, solved_ids: set) -> dict | None:
    with _lock:
        if difficulty == 'any':
            candidates = [
                p
                for (s, _), problems in _pool.items()
                if s == subject
                for p in problems
            ]
        else:
            candidates = list(_pool.get((subject, difficulty), []))

    unsolved = [p for p in candidates if p['id'] not in solved_ids]

    if not unsolved:
        return None

    return random.choice(unsolved)
