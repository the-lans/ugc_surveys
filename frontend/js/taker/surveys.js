checkAuth('taker');
renderHeader('surveys');

const listEl = document.getElementById('surveys-list');
const errEl  = document.getElementById('error');

async function loadSurveys() {
  listEl.innerHTML = '<p class="text-muted">Загрузка…</p>';
  try {
    const data = await api.get('/api/surveys/available/');
    renderList(data.results || []);
  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
    listEl.innerHTML = '';
  }
}

function renderList(surveys) {
  if (!surveys.length) {
    listEl.innerHTML = '<p class="empty-state">Нет доступных опросов</p>';
    return;
  }
  listEl.innerHTML = surveys.map(s => `
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">${escHtml(s.title)}</div>
          <div class="card-meta">${s.question_count} вопросов &bull; ${escHtml(s.author)}</div>
        </div>
        <div class="card-actions">
          <a class="btn btn-primary btn-sm" href="take.html?id=${s.id}">Пройти</a>
        </div>
      </div>
    </div>
  `).join('');
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

loadSurveys();
