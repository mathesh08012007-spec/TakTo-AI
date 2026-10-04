/* Chat screen: conversations, streaming replies, message actions, modes. */
(function () {
  'use strict';

  const MODES = [
    { id: 'friend', label: 'Friend', icon: '😊', hint: 'Relaxed, natural conversation.' },
    { id: 'mentor', label: 'Mentor', icon: '🎯', hint: 'Goal-oriented guidance and structured advice.' },
    { id: 'study', label: 'Study', icon: '📚', hint: 'Explanations, quizzes and revision.' },
    { id: 'coding', label: 'Coding', icon: '💻', hint: 'Debugging, explanations and code.' },
    { id: 'idea', label: 'Idea', icon: '💡', hint: 'Brainstorming projects and startup ideas.' },
    { id: 'fun', label: 'Fun', icon: '😂', hint: 'Jokes, games and challenges.' },
    { id: 'think', label: 'Think', icon: '🧠', hint: 'Work through decisions and situations.' },
  ];

  const STARTERS = {
    friend: ["I had a weird day", "Tell me something interesting", "I'm bored, talk to me"],
    mentor: ["Help me set a goal for this month", "I keep procrastinating", "Review my plan for the week"],
    study: ["Explain recursion simply", "Quiz me on Python basics", "Make a revision plan for tomorrow's exam"],
    coding: ["Help me debug an error", "Explain how Flask sessions work", "Review my code for bugs"],
    idea: ["Give me 5 project ideas for my portfolio", "Help me brainstorm a startup", "I want to build something with AI"],
    fun: ["Give me a riddle", "Would you rather…?", "Quiz me with something random"],
    think: ["I'm confused whether to choose AI or web development", "Help me decide between two job offers", "Is this plan realistic?"],
  };

  const FUN_ITEMS = [
    ['🎲 Random question', 'Ask me one random, interesting question to get me thinking.'],
    ['⚖️ Would you rather', "Give me a fun 'would you rather' question, then react to my answer."],
    ['📝 Mini quiz', 'Give me a 3-question mini quiz on a random topic, one question at a time.'],
    ['🧩 Riddle', "Give me a riddle. Don't reveal the answer until I guess or ask."],
    ['🧠 Brain teaser', 'Give me a brain teaser and let me try to solve it before you help.'],
    ['😂 Joke', 'Tell me a joke that would actually make me laugh.'],
    ['💻 Coding challenge', 'Give me a small coding challenge for a beginner and wait for my attempt.'],
    ['🔥 Motivation challenge', 'Give me a 10-minute motivation challenge I can start right now.'],
  ];

  const $ = (id) => document.getElementById(id);
  const els = {
    messages: $('messages'), input: $('input'), form: $('composer'), send: $('send'),
    suggestions: $('suggestions'), list: $('conv-list'), search: $('search'), title: $('conv-title'),
    modes: $('modes'), newChat: $('new-chat'), menu: $('menu-btn'), scrim: $('scrim'),
    rename: $('rename-btn'), clear: $('clear-btn'), fun: $('fun-btn'), funDialog: $('fun-dialog'), funGrid: $('fun-grid'),
  };

  const SEND_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3.4 20.4l17.5-7.5a1 1 0 000-1.8L3.4 3.6a1 1 0 00-1.4 1.2L4 10.5l9 1.5-9 1.5-2 5.7a1 1 0 001.4 1.2z"/></svg>';
  const STOP_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
  const EDIT_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg>';
  const TRASH_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>';

  const state = {
    user: null, conversations: [], currentId: null, mode: 'friend',
    streaming: false, controller: null, run: 0, tempUser: null, stick: true,
  };

  /* ---------- small helpers ---------- */
  function el(tag, cls, text) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }
  const modeInfo = (id) => MODES.find((m) => m.id === id) || MODES[0];
  const firstName = () => (state.user && state.user.name ? state.user.name.split(' ')[0] : 'there');

  function autosize() {
    els.input.style.height = 'auto';
    els.input.style.height = Math.min(els.input.scrollHeight, 200) + 'px';
  }

  function nearBottom() {
    const m = els.messages;
    return m.scrollHeight - m.scrollTop - m.clientHeight < 140;
  }
  function scrollToBottom(force) {
    if (force || state.stick) els.messages.scrollTop = els.messages.scrollHeight;
  }
  els.messages.addEventListener('scroll', () => { state.stick = nearBottom(); });

  function setStreaming(on) {
    state.streaming = on;
    els.messages.setAttribute('aria-busy', on ? 'true' : 'false');
    els.send.innerHTML = on ? STOP_ICON : SEND_ICON;
    els.send.setAttribute('aria-label', on ? 'Stop generating' : 'Send message');
    els.send.classList.toggle('stop', on);
  }

  function abortStream() {
    if (state.controller) { state.run++; state.controller.abort(); state.controller = null; }
    setStreaming(false);
  }

  /* ---------- modes ---------- */
  function renderModes() {
    els.modes.innerHTML = '';
    MODES.forEach((m) => {
      const b = el('button', 'mode-chip');
      b.type = 'button';
      b.dataset.mode = m.id;
      b.title = m.hint;
      b.setAttribute('aria-pressed', String(m.id === state.mode));
      b.append(el('span', '', m.icon), el('span', '', m.label));
      els.modes.appendChild(b);
    });
  }

  async function setMode(id) {
    if (id === state.mode) return;
    state.mode = id;
    renderModes();
    if (!els.messages.querySelector('.msg')) renderWelcome();
    if (state.currentId) {
      try { await API.put('/conversations/' + state.currentId, { mode: id }); }
      catch (err) { App.toast(err.message, 'error'); }
    }
  }

  /* ---------- messages ---------- */
  function renderWelcome() {
    els.messages.innerHTML = '';
    const info = modeInfo(state.mode);
    const box = el('section', 'welcome');
    const mascot = el('div', 'welcome-mascot');
    mascot.innerHTML = '<img src="img/takto.svg" alt="">';
    box.append(mascot, el('h2', '', 'Hey, ' + firstName() + '!'),
      el('p', '', "I'm Takto, your personal companion. Share what's on your mind. I'm here to listen and support you."),
      el('p', 'mode-note', info.icon + ' ' + info.label + ' mode: ' + info.hint));
    const starters = el('div', 'starters');
    (STARTERS[state.mode] || []).forEach((s) => {
      const b = el('button', 'chip', s);
      b.type = 'button';
      b.addEventListener('click', () => send(s));
      starters.appendChild(b);
    });
    box.appendChild(starters);
    els.messages.appendChild(box);
  }

  function setBubble(node, text) {
    const bubble = node.querySelector('.bubble');
    node._raw = text;
    if (node.classList.contains('assistant')) bubble.innerHTML = Markdown.render(text);
    else bubble.textContent = text;
  }

  function actionButton(act, label) {
    const b = el('button', 'act-' + act, label);
    b.type = 'button';
    b.dataset.act = act;
    return b;
  }

  function createMessage(msg) {
    const node = el('article', 'msg ' + msg.role + (msg.pending ? ' pending' : ''));
    if (msg.message_id) node.dataset.id = msg.message_id;
    const avatar = el('div', 'avatar', msg.role === 'user' ? firstName().charAt(0).toUpperCase() : '');
    if (msg.role !== 'user') avatar.innerHTML = '<img src="img/takto.svg" alt="">';
    avatar.setAttribute('aria-hidden', 'true');
    const main = el('div', 'msg-main');
    main.appendChild(el('span', 'sr-only', msg.role === 'user' ? 'You said:' : 'Takto said:'));
    main.appendChild(el('div', 'bubble' + (msg.role === 'assistant' ? ' md' : '')));

    const meta = el('div', 'msg-meta');
    const time = el('time', '', msg.created_at ? App.formatTime(msg.created_at) : '');
    if (msg.created_at) time.dateTime = msg.created_at;
    const actions = el('div', 'msg-actions');
    actions.appendChild(actionButton('copy', 'Copy'));
    if (msg.role === 'user') actions.appendChild(actionButton('edit', 'Edit'));
    else actions.appendChild(actionButton('regen', 'Regenerate'));
    actions.appendChild(actionButton('delete', 'Delete'));
    meta.append(time, actions);
    main.appendChild(meta);
    node.append(avatar, main);

    if (msg.pending) {
      const t = el('span', 'typing');
      t.setAttribute('role', 'status');
      t.setAttribute('aria-label', 'Takto is typing');
      t.append(el('span'), el('span'), el('span'));
      node.querySelector('.bubble').appendChild(t);
      node._raw = '';
    } else {
      setBubble(node, msg.content);
    }
    return node;
  }

  function updateLastAi() {
    els.messages.querySelectorAll('.is-last-ai').forEach((n) => n.classList.remove('is-last-ai'));
    const all = els.messages.querySelectorAll('.msg.assistant:not(.pending)');
    if (all.length) all[all.length - 1].classList.add('is-last-ai');
  }

  function addMessage(msg) {
    const welcome = els.messages.querySelector('.welcome');
    if (welcome) welcome.remove();
    const node = createMessage(msg);
    els.messages.appendChild(node);
    updateLastAi();
    scrollToBottom();
    return node;
  }

  function renderMessages(list) {
    els.messages.innerHTML = '';
    if (!list.length) renderWelcome();
    else list.forEach((m) => els.messages.appendChild(createMessage(m)));
    updateLastAi();
    clearSuggestions();
    state.stick = true;
    scrollToBottom(true);
  }

  function clearSuggestions() { els.suggestions.innerHTML = ''; }
  function clearErrors() { els.messages.querySelectorAll('.msg-error').forEach((n) => n.remove()); }

  function showSuggestions(items) {
    clearSuggestions();
    items.forEach((s) => {
      const b = el('button', 'chip', s);
      b.type = 'button';
      b.addEventListener('click', () => send(s));
      els.suggestions.appendChild(b);
    });
  }

  function showError(message, canRetry) {
    const box = el('div', 'msg-error');
    box.setAttribute('role', 'alert');
    box.append(el('strong', '', 'Error:'), el('span', '', message));
    if (canRetry) {
      const b = el('button', 'btn', 'Retry');
      b.type = 'button';
      b.addEventListener('click', regenerate);
      box.appendChild(b);
    }
    els.messages.appendChild(box);
    scrollToBottom(true);
  }

  /* ---------- streaming ---------- */
  async function runStream(path, body) {
    const run = ++state.run;
    const ctrl = new AbortController();
    state.controller = ctrl;
    setStreaming(true);
    clearSuggestions();
    clearErrors();

    const aiEl = addMessage({ role: 'assistant', pending: true });
    const tempUser = state.tempUser;
    state.tempUser = null;
    let buffer = '', raf = 0, sawDelta = false, sseError = null, httpError = null, aborted = false, doneSeen = false;
    const alive = () => run === state.run;
    const paint = () => { raf = 0; if (alive()) { setBubble(aiEl, buffer); scrollToBottom(); } };
    let convId = body.conversation_id || null;

    try {
      await API.stream(path, body, (ev) => {
        if (!alive() && ev.type !== 'title') return;
        switch (ev.type) {
          case 'meta':
            convId = ev.conversation_id;
            if (!state.currentId) {
              state.currentId = convId;
              history.replaceState(null, '', 'chat.html?c=' + convId);
              loadConversations();
            }
            if (tempUser && ev.user_message) tempUser.dataset.id = ev.user_message.message_id;
            break;
          case 'delta':
            if (!sawDelta) { sawDelta = true; aiEl.classList.remove('pending'); aiEl.querySelector('.bubble').innerHTML = ''; }
            buffer += ev.text;
            if (!raf) raf = requestAnimationFrame(paint);
            break;
          case 'done': {
            doneSeen = true;
            if (raf) cancelAnimationFrame(raf);
            aiEl.classList.remove('pending');
            aiEl.dataset.id = ev.message.message_id;
            setBubble(aiEl, ev.message.content);
            const t = aiEl.querySelector('time');
            t.textContent = App.formatTime(ev.message.created_at);
            t.dateTime = ev.message.created_at;
            updateLastAi();
            setStreaming(false);
            if (ev.suggestions && ev.suggestions.length) showSuggestions(ev.suggestions);
            loadConversations();
            scrollToBottom();
            break;
          }
          case 'title':
            if (state.currentId === ev.conversation_id) els.title.textContent = ev.title;
            loadConversations();
            break;
          case 'error':
            sseError = ev.error;
            break;
          default:
        }
      }, ctrl.signal);
    } catch (err) {
      if (err.name === 'AbortError') aborted = true;
      else if (err.status !== undefined) httpError = err;
      else sseError = 'Something went wrong while talking to my AI brain 😅. Try again.';
    }

    if (raf) cancelAnimationFrame(raf);
    if (!alive()) return;               // the user switched conversations; nothing more to do here
    state.controller = null;
    setStreaming(false);

    if (aborted) {
      // The server keeps whatever was written before the stop; sync ids shortly after.
      if (sawDelta) setBubble(aiEl, buffer); else aiEl.remove();
      aiEl.classList.remove('pending');
      setTimeout(() => { if (!state.streaming && state.currentId === convId) reloadMessages(); }, 700);
    } else if (httpError || sseError) {
      aiEl.remove();
      if (httpError && body.message !== undefined) {
        if (tempUser) tempUser.remove();           // the message was never saved: put the text back
        els.input.value = body.message;
        autosize();
        if (!els.messages.querySelector('.msg')) renderWelcome();
        showError(httpError.message, false);
      } else {
        showError((httpError || { message: sseError }).message, true);
      }
    } else if (!doneSeen) {
      aiEl.remove();
      showError('The reply was cut off. Please retry.', true);
    }
    updateLastAi();
  }

  async function reloadMessages() {
    if (!state.currentId) return;
    try {
      const data = await API.get('/conversations/' + state.currentId);
      renderMessages(data.messages);
    } catch (_) { /* leave the view as it is */ }
  }

  async function send(text) {
    text = (text || '').trim();
    if (!text || state.streaming) return;
    clearErrors();
    state.stick = true;
    state.tempUser = addMessage({ role: 'user', content: text, created_at: new Date().toISOString() });
    els.input.value = '';
    autosize();
    await runStream('/chat', { message: text, conversation_id: state.currentId, mode: state.mode });
  }

  async function regenerate() {
    if (state.streaming || !state.currentId) return;
    const last = els.messages.querySelector('.msg.assistant.is-last-ai');
    if (last) last.remove();
    await runStream('/chat/regenerate', { conversation_id: state.currentId, mode: state.mode });
  }

  /* ---------- message actions ---------- */
  function startEdit(node) {
    if (state.streaming) return;
    const main = node.querySelector('.msg-main');
    const bubble = node.querySelector('.bubble');
    const meta = node.querySelector('.msg-meta');
    const box = el('div', 'edit-box');
    const ta = el('textarea');
    ta.value = node._raw;
    ta.maxLength = 8000;
    ta.setAttribute('aria-label', 'Edit your message');
    const actions = el('div', 'actions');
    const cancel = el('button', 'btn', 'Cancel');
    cancel.type = 'button';
    const save = el('button', 'btn btn-primary', 'Save and regenerate');
    save.type = 'button';
    actions.append(cancel, save);
    box.append(ta, actions);
    main.replaceChild(box, bubble);
    meta.hidden = true;
    ta.focus();

    const restore = () => { main.replaceChild(bubble, box); meta.hidden = false; };
    cancel.addEventListener('click', restore);
    save.addEventListener('click', async () => {
      const content = ta.value.trim();
      if (!content) return App.toast("A message can't be empty.", 'error');
      save.disabled = true;
      try {
        await API.put('/conversations/' + state.currentId + '/messages/' + node.dataset.id, { content });
      } catch (err) {
        save.disabled = false;
        return App.toast(err.message, 'error');
      }
      while (node.nextElementSibling) node.nextElementSibling.remove();
      restore();
      setBubble(node, content);
      await runStream('/chat/regenerate', { conversation_id: state.currentId, mode: state.mode });
    });
  }

  async function deleteMessage(node) {
    if (state.streaming) return;
    const yes = await App.confirm({ title: 'Delete this message?', message: "It will be removed from the conversation.", confirmLabel: 'Delete', danger: true });
    if (!yes) return;
    try {
      await API.del('/conversations/' + state.currentId + '/messages/' + node.dataset.id);
    } catch (err) { return App.toast(err.message, 'error'); }
    node.remove();
    clearSuggestions();
    updateLastAi();
    if (!els.messages.querySelector('.msg')) renderWelcome();
  }

  els.messages.addEventListener('click', async (e) => {
    const codeBtn = e.target.closest('.copy-code');
    if (codeBtn) {
      const ok = await App.copy(codeBtn.closest('.code-block').querySelector('code').textContent);
      codeBtn.textContent = ok ? 'Copied' : 'Copy failed';
      setTimeout(() => { codeBtn.textContent = 'Copy'; }, 1500);
      return;
    }
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const node = btn.closest('.msg');
    if (!node) return;
    switch (btn.dataset.act) {
      case 'copy': App.toast((await App.copy(node._raw)) ? 'Copied to clipboard.' : "Couldn't copy.", ''); break;
      case 'edit': startEdit(node); break;
      case 'regen': regenerate(); break;
      case 'delete': deleteMessage(node); break;
      default:
    }
  });

  /* ---------- conversations ---------- */
  function groupLabel(iso) {
    const d = new Date(iso);
    const days = Math.floor((new Date().setHours(0, 0, 0, 0) - new Date(d).setHours(0, 0, 0, 0)) / 86400000);
    if (days <= 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return 'Previous 7 days';
    return 'Older';
  }

  function renderConversationList() {
    els.list.innerHTML = '';
    if (!state.conversations.length) {
      els.list.appendChild(el('p', 'empty', els.search.value ? 'No chats match your search.' : 'No chats yet. Say hi!'));
      return;
    }
    const groups = new Map();
    state.conversations.forEach((c) => {
      const label = groupLabel(c.updated_at);
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(c);
    });
    groups.forEach((items, label) => {
      const section = el('section', 'conv-group');
      section.appendChild(el('h2', '', label));
      items.forEach((c) => {
        const row = el('div', 'conv-item' + (c.conversation_id === state.currentId ? ' active' : ''));
        const open = el('button', 'conv-open');
        open.type = 'button';
        open.dataset.id = c.conversation_id;
        if (c.conversation_id === state.currentId) open.setAttribute('aria-current', 'page');
        open.append(el('span', '', modeInfo(c.mode).icon), el('span', 't', c.title));
        open.addEventListener('click', () => { closeDrawer(); openConversation(c.conversation_id); });

        const actions = el('div', 'conv-actions');
        const ren = el('button', 'icon-btn');
        ren.type = 'button';
        ren.innerHTML = EDIT_ICON;
        ren.setAttribute('aria-label', 'Rename ' + c.title);
        ren.addEventListener('click', () => renameConversation(c));
        const del = el('button', 'icon-btn');
        del.type = 'button';
        del.innerHTML = TRASH_ICON;
        del.setAttribute('aria-label', 'Delete ' + c.title);
        del.addEventListener('click', () => deleteConversation(c));
        actions.append(ren, del);
        row.append(open, actions);
        section.appendChild(row);
      });
      els.list.appendChild(section);
    });
  }

  async function loadConversations() {
    try {
      const data = await API.get('/conversations' + (els.search.value.trim() ? '?q=' + encodeURIComponent(els.search.value.trim()) : ''));
      state.conversations = data.conversations;
      renderConversationList();
    } catch (err) { App.toast(err.message, 'error'); }
  }

  async function openConversation(id) {
    abortStream();
    try {
      const data = await API.get('/conversations/' + id);
      state.currentId = id;
      state.mode = data.conversation.mode;
      renderModes();
      els.title.textContent = data.conversation.title;
      renderMessages(data.messages);
      history.replaceState(null, '', 'chat.html?c=' + id);
      updateHeaderButtons();
      renderConversationList();
      els.input.focus();
    } catch (err) {
      App.toast(err.message, 'error');
      if (err.status === 404) newChat();
    }
  }

  function newChat(mode) {
    abortStream();
    state.currentId = null;
    if (mode) state.mode = mode;
    renderModes();
    els.title.textContent = 'New chat';
    history.replaceState(null, '', 'chat.html');
    renderWelcome();
    clearSuggestions();
    updateHeaderButtons();
    renderConversationList();
    els.input.focus();
  }

  function updateHeaderButtons() {
    els.rename.hidden = !state.currentId;
    els.clear.hidden = !state.currentId;
  }

  async function renameConversation(c) {
    const title = await App.prompt({ title: 'Rename chat', label: 'Chat title', value: c.title });
    if (!title) return;
    try {
      await API.put('/conversations/' + c.conversation_id, { title });
      if (c.conversation_id === state.currentId) els.title.textContent = title;
      loadConversations();
    } catch (err) { App.toast(err.message, 'error'); }
  }

  async function deleteConversation(c) {
    const yes = await App.confirm({ title: 'Delete this chat?', message: '"' + c.title + '" and all its messages will be removed.', confirmLabel: 'Delete', danger: true });
    if (!yes) return;
    try {
      await API.del('/conversations/' + c.conversation_id);
      if (c.conversation_id === state.currentId) newChat();
      loadConversations();
    } catch (err) { App.toast(err.message, 'error'); }
  }

  /* ---------- drawer (mobile) ---------- */
  function openDrawer() {
    document.body.classList.add('sidebar-open');
    els.scrim.hidden = false;
    els.menu.setAttribute('aria-expanded', 'true');
  }
  function closeDrawer() {
    document.body.classList.remove('sidebar-open');
    els.scrim.hidden = true;
    els.menu.setAttribute('aria-expanded', 'false');
  }

  /* ---------- wiring ---------- */
  els.form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (state.streaming) {
      // Stop: keep the partial reply, which the server saves.
      if (state.controller) state.controller.abort();
      return;
    }
    send(els.input.value);
  });

  els.input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      if (!state.streaming) send(els.input.value);
    }
  });
  els.input.addEventListener('input', autosize);

  els.modes.addEventListener('click', (e) => {
    const chip = e.target.closest('.mode-chip');
    if (chip) setMode(chip.dataset.mode);
  });

  els.newChat.addEventListener('click', () => { closeDrawer(); newChat(); });
  els.menu.addEventListener('click', () => (document.body.classList.contains('sidebar-open') ? closeDrawer() : openDrawer()));
  els.scrim.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });

  let searchTimer;
  els.search.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadConversations, 250); });

  els.rename.addEventListener('click', () => {
    const c = state.conversations.find((x) => x.conversation_id === state.currentId);
    if (c) renameConversation(c);
  });

  els.clear.addEventListener('click', async () => {
    if (!state.currentId || state.streaming) return;
    const yes = await App.confirm({ title: 'Clear this conversation?', message: 'All messages in this chat will be deleted. The chat itself stays.', confirmLabel: 'Clear messages', danger: true });
    if (!yes) return;
    try {
      await API.post('/conversations/' + state.currentId + '/clear');
      renderMessages([]);
    } catch (err) { App.toast(err.message, 'error'); }
  });

  FUN_ITEMS.forEach(([label, prompt]) => {
    const b = el('button', '', label);
    b.type = 'button';
    b.addEventListener('click', () => {
      els.funDialog.close();
      closeDrawer();
      newChat('fun');
      send(prompt);
    });
    els.funGrid.appendChild(b);
  });
  els.fun.addEventListener('click', () => els.funDialog.showModal());
  $('fun-close').addEventListener('click', () => els.funDialog.close());

  /* ---------- start ---------- */
  (async function init() {
    state.user = await App.requireAuth();
    if (!state.user) return;
    const params = new URLSearchParams(location.search);
    let favorite = 'friend';
    try { favorite = (await API.get('/profile')).profile.favorite_mode || 'friend'; } catch (_) { /* default */ }

    setStreaming(false);
    renderModes();
    API.get('/health').then((h) => {
      const ok = h.ai_configured;
      $('status-text').textContent = ok ? 'Online' : 'AI key not set';
      $('status-dot').classList.toggle('off', !ok);
    }).catch(() => {
      $('status-text').textContent = 'Offline';
      $('status-dot').classList.add('off');
    });
    await loadConversations();

    const cid = parseInt(params.get('c'), 10);
    const requested = params.get('mode');
    if (cid) await openConversation(cid);
    else newChat(MODES.some((m) => m.id === requested) ? requested : favorite);
  })();
})();
