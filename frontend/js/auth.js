// Сохранение данных после входа
function saveAuth({ access, refresh, username, role }) {
  localStorage.setItem('access_token',  access);
  localStorage.setItem('refresh_token', refresh);
  localStorage.setItem('username', username);
  localStorage.setItem('role', role);
}

function getRole()     { return localStorage.getItem('role'); }
function getUsername() { return localStorage.getItem('username'); }

function logout() {
  ['access_token', 'refresh_token', 'username', 'role'].forEach(
    k => localStorage.removeItem(k)
  );
  window.location.href = '/login.html';
}

// Вызывается в начале каждой защищённой страницы.
// requiredRole: 'creator' | 'taker' | null (любая роль)
function checkAuth(requiredRole = null) {
  if (!localStorage.getItem('access_token')) {
    window.location.href = '/login.html';
    return false;
  }
  if (requiredRole && getRole() !== requiredRole) {
    window.location.href =
      getRole() === 'creator' ? '/creator/surveys.html' : '/taker/surveys.html';
    return false;
  }
  return true;
}

// Рендерит шапку в элемент <header id="app-header">
function renderHeader(activePage) {
  const role = getRole();
  const username = getUsername();

  const creatorNav = `
    <a href="/creator/surveys.html" class="${activePage === 'surveys' ? 'active' : ''}">Мои опросы</a>
  `;
  const takerNav = `
    <a href="/taker/surveys.html" class="${activePage === 'surveys' ? 'active' : ''}">Опросы</a>
  `;

  document.getElementById('app-header').innerHTML = `
    <header class="header">
      <a href="${role === 'creator' ? '/creator/surveys.html' : '/taker/surveys.html'}" class="header-logo">
        UGC Surveys
      </a>
      <nav class="header-nav">
        ${role === 'creator' ? creatorNav : takerNav}
      </nav>
      <div class="header-user">
        <span>${escHtml(username || '')}</span>
        <button class="btn btn-ghost btn-sm" onclick="logout()">Выйти</button>
      </div>
    </header>
  `;
}

// Показывает сообщение об ошибке в элементе .alert внутри контейнера
function showError(container, message) {
  const el = container.querySelector('.alert') || container;
  el.textContent = message;
  el.classList.remove('hidden');
}

function hideError(el) {
  el.classList.add('hidden');
  el.textContent = '';
}

function escHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Блокирует кнопку на время загрузки
function setLoading(btn, loading, originalText) {
  btn.disabled = loading;
  btn.textContent = loading ? 'Загрузка…' : originalText;
}
