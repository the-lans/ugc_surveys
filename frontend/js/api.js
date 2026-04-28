// В dev фронтенд работает на порту 3000, бэкенд — на 8000.
// В проде оба отдаёт nginx с одного домена, поэтому BASE_URL пустой.
const BASE_URL =
  window.location.port === '3000' ? 'http://localhost:8000' : '';

async function _fetch(method, path, body, isRetry) {
  const token = localStorage.getItem('access_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body !== null && body !== undefined) opts.body = JSON.stringify(body);

  const res = await fetch(BASE_URL + path, opts);

  // Токен истёк — пробуем обновить один раз
  if (res.status === 401 && !isRetry) {
    const ok = await _refresh();
    if (ok) return _fetch(method, path, body, true);
    _clearAuth();
    window.location.href = '/login.html';
    throw { detail: 'Сессия истекла.' };
  }

  if (res.status === 204) return null;

  if (!res.ok) {
    let err;
    try { err = await res.json(); } catch { err = { detail: 'Ошибка сервера' }; }
    throw err;
  }

  return res.json();
}

async function _refresh() {
  const refresh = localStorage.getItem('refresh_token');
  if (!refresh) return false;
  try {
    const res = await fetch(BASE_URL + '/api/auth/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem('access_token', data.access);
    return true;
  } catch {
    return false;
  }
}

function _clearAuth() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('username');
  localStorage.removeItem('role');
}

// Публичный API-клиент
const api = {
  get:    (path)        => _fetch('GET',    path, null),
  post:   (path, body)  => _fetch('POST',   path, body),
  patch:  (path, body)  => _fetch('PATCH',  path, body),
  delete: (path)        => _fetch('DELETE', path, null),
};

// Преобразует объект ошибок DRF в читаемую строку
function extractError(err) {
  if (!err) return 'Неизвестная ошибка';
  if (typeof err === 'string') return err;
  if (Array.isArray(err)) return err.join(', ');
  if (err.detail) return err.detail;
  if (err.non_field_errors) return err.non_field_errors.join(', ');
  const msgs = [];
  for (const [field, errs] of Object.entries(err)) {
    const text = Array.isArray(errs) ? errs.join(', ') : errs;
    msgs.push(`${field}: ${text}`);
  }
  return msgs.join('; ') || 'Ошибка запроса';
}
