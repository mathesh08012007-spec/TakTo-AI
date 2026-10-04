/* Login and register forms. */
(function () {
  const form = document.getElementById('auth-form');
  if (!form) return;
  const isRegister = form.dataset.kind === 'register';
  const errorBox = document.getElementById('form-error');
  const submit = form.querySelector('[type=submit]');
  const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  App.currentUser().then((user) => { if (user) location.replace(App.safeNext('chat.html')); });

  function showError(msg) { errorBox.textContent = msg; }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    showError('');
    const value = (id) => (form.elements[id] ? form.elements[id].value : '');
    const body = { email: value('email').trim(), password: value('password') };

    if (!body.email || !body.password) return showError('Please fill in all the fields.');
    if (!EMAIL_RE.test(body.email)) return showError("That email address doesn't look right.");
    if (isRegister) {
      body.name = value('name').trim();
      body.confirm_password = value('confirm_password');
      if (!body.name) return showError('Please enter your name.');
      if (body.password.length < 8) return showError('Password must be at least 8 characters.');
      if (body.password !== body.confirm_password) return showError("Passwords don't match.");
    }

    submit.disabled = true;
    const original = submit.textContent;
    submit.textContent = isRegister ? 'Creating account…' : 'Logging in…';
    try {
      await API.post(isRegister ? '/auth/register' : '/auth/login', body);
      location.href = App.safeNext('chat.html');
    } catch (err) {
      showError(err.message);
      submit.disabled = false;
      submit.textContent = original;
    }
  });
})();
