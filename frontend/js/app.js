/* Shared UI helpers: theme, toasts, dialogs, auth guard. */
(function () {
  const root = document.documentElement;
  try {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') root.dataset.theme = saved;
  } catch (_) { /* storage blocked: follow system theme */ }

  function effectiveTheme() {
    return root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  function toggleTheme() {
    const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (_) { /* ignore */ }
    document.querySelectorAll('[data-theme-toggle]').forEach(syncThemeButton);
  }

  function syncThemeButton(btn) {
    const dark = effectiveTheme() === 'dark';
    btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    btn.setAttribute('title', dark ? 'Light mode' : 'Dark mode');
    btn.textContent = dark ? '☀️' : '🌙';
  }

  function toast(message, type) {
    let region = document.getElementById('toast-region');
    if (!region) {
      region = document.createElement('div');
      region.id = 'toast-region';
      region.className = 'toast-region';
      region.setAttribute('role', 'status');
      region.setAttribute('aria-live', 'polite');
      document.body.appendChild(region);
    }
    const t = document.createElement('div');
    t.className = 'toast' + (type === 'error' ? ' error' : '');
    t.textContent = message;
    region.appendChild(t);
    setTimeout(() => t.remove(), type === 'error' ? 6000 : 3200);
  }

  function dialog(build) {
    return new Promise((resolve) => {
      const dlg = document.createElement('dialog');
      dlg.setAttribute('aria-labelledby', 'dlg-title');
      build(dlg, (value) => { dlg.close(); resolve(value); });
      dlg.addEventListener('cancel', () => resolve(null));
      dlg.addEventListener('close', () => dlg.remove());
      document.body.appendChild(dlg);
      dlg.showModal();
    });
  }

  function confirmDialog({ title, message, confirmLabel = 'Confirm', danger = false }) {
    return dialog((dlg, done) => {
      dlg.innerHTML = '<h2 id="dlg-title"></h2><p></p><div class="actions">' +
        '<button type="button" class="btn" data-x="cancel">Cancel</button>' +
        '<button type="button" class="btn btn-primary" data-x="ok"></button></div>';
      dlg.querySelector('h2').textContent = title;
      dlg.querySelector('p').textContent = message;
      const ok = dlg.querySelector('[data-x=ok]');
      ok.textContent = confirmLabel;
      if (danger) { ok.classList.remove('btn-primary'); ok.classList.add('btn-danger'); }
      dlg.querySelector('[data-x=cancel]').onclick = () => done(false);
      ok.onclick = () => done(true);
      ok.focus();
    }).then((v) => v === true);
  }

  function promptDialog({ title, label, value = '', confirmLabel = 'Save', maxLength = 100 }) {
    return dialog((dlg, done) => {
      dlg.innerHTML = '<form method="dialog"><h2 id="dlg-title"></h2><div class="field"><label for="dlg-input"></label>' +
        '<input id="dlg-input" type="text"></div><div class="actions">' +
        '<button type="button" class="btn" data-x="cancel">Cancel</button>' +
        '<button type="submit" class="btn btn-primary"></button></div></form>';
      dlg.querySelector('h2').textContent = title;
      dlg.querySelector('label').textContent = label;
      const input = dlg.querySelector('input');
      input.value = value;
      input.maxLength = maxLength;
      dlg.querySelector('[type=submit]').textContent = confirmLabel;
      dlg.querySelector('[data-x=cancel]').onclick = () => done(null);
      dlg.querySelector('form').onsubmit = (e) => { e.preventDefault(); done(input.value.trim() || null); };
      input.focus(); input.select();
    });
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (_) { /* ignore */ }
      ta.remove();
      return ok;
    }
  }

  function formatTime(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return '';
    const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    if (d.toDateString() === new Date().toDateString()) return time;
    return d.toLocaleDateString([], { day: 'numeric', month: 'short' }) + ', ' + time;
  }

  async function currentUser() {
    try { return (await API.get('/auth/me')).user; } catch (_) { return null; }
  }

  async function requireAuth() {
    const user = await currentUser();
    if (!user) {
      const here = location.pathname.split('/').pop() + location.search;
      location.replace('login.html?next=' + encodeURIComponent(here));
      return null;
    }
    return user;
  }

  /* Only allow redirects to our own pages, e.g. chat.html?mode=think */
  function safeNext(fallback) {
    const next = new URLSearchParams(location.search).get('next') || '';
    return /^[a-z0-9_-]+\.html(\?[\w=&%.-]*)?$/i.test(next) ? next : fallback;
  }

  async function logout() {
    try { await API.post('/auth/logout'); } catch (_) { /* leave anyway */ }
    location.href = 'index.html';
  }

  window.App = { toggleTheme, toast, confirm: confirmDialog, prompt: promptDialog, copy, formatTime, currentUser, requireAuth, safeNext, logout };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      syncThemeButton(btn);
      btn.addEventListener('click', toggleTheme);
    });
    document.querySelectorAll('[data-logout]').forEach((btn) => btn.addEventListener('click', logout));
  });
})();
