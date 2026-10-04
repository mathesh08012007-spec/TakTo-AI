/* Profile form + memory manager. */
(function () {
  const form = document.getElementById('profile-form');
  if (!form) return;
  const errorBox = document.getElementById('form-error');
  const memoryList = document.getElementById('memory-list');
  const memoryEmpty = document.getElementById('memory-empty');
  const clearBtn = document.getElementById('clear-memories');

  const LABELS = { preference: 'Preference', goal: 'Goal', interest: 'Interest', learning: 'Learning', project: 'Project', personal_context: 'Personal context' };

  function fill(p) {
    ['name', 'email', 'tone', 'favorite_mode', 'learning_goals', 'interests'].forEach((k) => { form.elements[k].value = p[k] || ''; });
  }

  function renderMemories(memories) {
    memoryList.innerHTML = '';
    memoryEmpty.hidden = memories.length > 0;
    clearBtn.hidden = memories.length === 0;
    memories.forEach((m) => {
      const li = document.createElement('li');
      li.className = 'memory-item';
      const body = document.createElement('p');
      body.textContent = m.memory_text;
      const meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = 'Importance ' + m.importance + '/10 · saved ' + App.formatTime(m.created_at);
      body.appendChild(meta);
      const badge = document.createElement('span');
      badge.className = 'badge';
      badge.textContent = LABELS[m.category] || m.category;
      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'btn btn-ghost btn-danger';
      del.textContent = 'Delete';
      del.setAttribute('aria-label', 'Delete memory: ' + m.memory_text);
      del.addEventListener('click', async () => {
        try {
          await API.del('/memories/' + m.memory_id);
          li.remove();
          if (!memoryList.children.length) renderMemories([]);
          App.toast('Memory deleted.');
        } catch (err) { App.toast(err.message, 'error'); }
      });
      li.append(badge, body, del);
      memoryList.appendChild(li);
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBox.textContent = '';
    const body = {};
    ['name', 'email', 'tone', 'favorite_mode', 'learning_goals', 'interests'].forEach((k) => { body[k] = form.elements[k].value; });
    const btn = form.querySelector('[type=submit]');
    btn.disabled = true;
    try {
      fill((await API.put('/profile', body)).profile);
      App.toast('Profile saved.');
    } catch (err) {
      errorBox.textContent = err.message;
    } finally { btn.disabled = false; }
  });

  clearBtn.addEventListener('click', async () => {
    const yes = await App.confirm({ title: 'Clear all memories?', message: 'Your companion will forget everything it saved about you. This can\'t be undone.', confirmLabel: 'Clear all', danger: true });
    if (!yes) return;
    try {
      await API.del('/memories');
      renderMemories([]);
      App.toast('All memories cleared.');
    } catch (err) { App.toast(err.message, 'error'); }
  });

  (async function init() {
    const user = await App.requireAuth();
    if (!user) return;
    try {
      const [profile, memories] = await Promise.all([API.get('/profile'), API.get('/memories')]);
      fill(profile.profile);
      renderMemories(memories.memories);
    } catch (err) { errorBox.textContent = err.message; }
  })();
})();
