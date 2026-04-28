checkAuth('creator');
renderHeader('surveys');

const listEl      = document.getElementById('surveys-list');
const errEl       = document.getElementById('error');
const createForm  = document.getElementById('create-form');
const createErrEl = document.getElementById('create-error');
const createBtn   = document.getElementById('create-btn');

async function loadSurveys() {
  listEl.innerHTML = '<p class="text-muted">Загрузка…</p>';
  try {
    const data = await api.get('/api/surveys/');
    renderList(data.results || []);
  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
    listEl.innerHTML = '';
  }
}

function renderList(surveys) {
  if (!surveys.length) {
    listEl.innerHTML = '<p class="empty-state">Опросов пока нет. Создайте первый!</p>';
    return;
  }

  listEl.innerHTML = surveys.map(s => `
    <div class="card" id="survey-${s.id}">
      <div class="card-header">
        <div>
          <div class="card-title">${escHtml(s.title)}</div>
          <div class="card-meta">
            ${s.question_count} вопр. &bull;
            ${s.is_active ? '<span style="color:var(--success)">Активен</span>' : '<span style="color:var(--muted)">Неактивен</span>'}
            &bull; ${formatDate(s.created_at)}
          </div>
        </div>
        <div class="card-actions">
          <a class="btn btn-outline btn-sm" href="edit.html?id=${s.id}">Редактировать</a>
          <a class="btn btn-ghost btn-sm" href="stats.html?id=${s.id}">Статистика</a>
          <button class="btn btn-danger btn-sm" onclick="deleteSurvey(${s.id})">Удалить</button>
        </div>
      </div>
    </div>
  `).join('');
}

async function deleteSurvey(id) {
  if (!confirm('Удалить опрос? Данные сессий сохранятся.')) return;
  try {
    await api.delete(`/api/surveys/${id}/`);
    document.getElementById(`survey-${id}`)?.remove();
    if (!listEl.children.length) {
      listEl.innerHTML = '<p class="empty-state">Опросов пока нет. Создайте первый!</p>';
    }
  } catch (err) {
    alert(extractError(err));
  }
}

createForm.addEventListener('submit', async e => {
  e.preventDefault();
  hideError(createErrEl);
  setLoading(createBtn, true, '+ Создать опрос');

  try {
    const survey = await api.post('/api/surveys/', {
      title: document.getElementById('new-title').value.trim(),
    });
    window.location.href = `edit.html?id=${survey.id}`;
  } catch (err) {
    createErrEl.textContent = extractError(err);
    createErrEl.classList.remove('hidden');
    setLoading(createBtn, false, '+ Создать опрос');
  }
});

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day:'numeric', month:'short', year:'numeric' });
}

loadSurveys();
