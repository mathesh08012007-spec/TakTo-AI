/* Landing page: show the right buttons for logged-in vs logged-out visitors. */
(function () {
  const box = document.getElementById('nav-actions');
  if (!box) return;
  App.currentUser().then((user) => {
    const theme = box.querySelector('[data-theme-toggle]');
    if (user) {
      box.insertAdjacentHTML('afterbegin', '<a class="btn btn-primary" href="chat.html">Open chat</a><a class="btn btn-ghost" href="profile.html">Profile</a>');
    } else {
      box.insertAdjacentHTML('afterbegin', '<a class="btn btn-ghost" href="login.html">Log in</a><a class="btn btn-primary" href="register.html">Sign up</a>');
    }
    if (theme) box.appendChild(theme);
  });
})();
