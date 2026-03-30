function typeset(el) {
  if (!window.MathJax) return;
  const ready = MathJax.startup?.promise ?? Promise.resolve();
  ready.then(() => MathJax.typesetPromise([el])).catch(() => {});
}

function renderMarkdown(el, text) {
  text = text.replace(/(\$\$[\s\S]*?\$\$)/g, '\n\n$1\n\n');
  const encoded = text.replace(/\$\$[\s\S]*?\$\$|\$[^$\n]*?\$/g, m => {
    return '\x00' + btoa(unescape(encodeURIComponent(m))) + '\x00';
  });
  let html = marked.parse(encoded, { breaks: true });
  html = html.replace(/\x00([A-Za-z0-9+/=]+)\x00/g, (_, b64) => {
    return decodeURIComponent(escape(atob(b64)));
  });
  el.innerHTML = html;
  typeset(el);
}

const problemEl = document.getElementById('problem-text');
if (problemEl) renderMarkdown(problemEl, problemEl.dataset.raw);

const buttons = document.querySelectorAll('.btn-ai');
const panel = document.getElementById('ai-panel');
const label = document.getElementById('ai-label');
const responseEl = document.getElementById('ai-response');
const confirmBtn = document.getElementById('confirm-btn');

const modeLabels = { check: 'answer check', hint: 'hint', steps: 'step-by-step', explain: 'explanation' };

buttons.forEach(btn => {
  btn.addEventListener('click', async () => {
    const mode = btn.dataset.mode;
    const answer = document.getElementById('answer').value.trim();

    buttons.forEach(b => { b.disabled = true; b.classList.remove('active'); });
    btn.classList.add('active');
    panel.classList.add('visible');
    label.textContent = modeLabels[mode];
    responseEl.className = 'ai-response';
    responseEl.innerHTML = '<span class="ai-cursor"></span>';

    const body = new FormData();
    body.append('mode', mode);
    body.append('answer', answer);

    try {
      const res = await fetch('/problem/ai', { method: 'POST', body });
      const data = await res.json();

      if (res.status === 429) {
        const mins = Math.ceil(data.wait / 60);
        panel.classList.remove('visible');
        showToast(`Too many requests - please wait ${mins} minute${mins !== 1 ? 's' : ''} before asking again.`);
        return;
      }

      if (!res.ok || data.error) {
        responseEl.textContent = data.error || 'Request failed.';
        return;
      }

      if (mode === 'check') {
        renderMarkdown(responseEl, data.text);
        if (data.verdict === 'CORRECT') {
          responseEl.classList.add('check-correct');
          if (confirmBtn) { confirmBtn.disabled = false; confirmBtn.title = ''; }
        } else if (data.verdict === 'INCORRECT') {
          responseEl.classList.add('check-wrong');
        }
      } else {
        renderMarkdown(responseEl, data.text);
      }

    } catch (e) {
      responseEl.textContent = 'Request failed.';
    } finally {
      buttons.forEach(b => { b.disabled = false; });
      btn.classList.remove('active');
    }
  });
});
