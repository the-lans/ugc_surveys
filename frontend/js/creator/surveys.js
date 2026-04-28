checkAuth('creator');
renderHeader('surveys');

const listEl      = document.getElementById('surveys-list');
const errEl       = document.getElementById('error');
const createForm  = document.getElementById('create-form');
const createErrEl = document.getElementById('create-error');
const createBtn   = document.getElementById('create-btn');

let nextUrl = null;

async function loadSurveys(url = '/api/surveys/') {
  const isInitial = url === '/api/surveys/';
  if (isInitial) {
    listEl.innerHTML = '<p class="text-muted">Загрузка…</p>';
    nextUrl = null;
  }
  try {
    const data = await api.get(url);
    hideError(errEl);
    nextUrl = data.next || null;
    appendList(data.results || []);
  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
    if (isInitial) listEl.innerHTML = '';
  } finally {
    syncLoadMoreBtn();
  }
}

function appendList(surveys) {
  const isEmpty = !listEl.querySelector('.card') && !surveys.length;
  if (isEmpty) {
    listEl.innerHTML = '<p class="empty-state">Опросов пока нет. Создайте первый!</p>';
    return;
  }

  const placeholder = listEl.querySelector('p.text-muted,p.empty-state');
  if (placeholder) placeholder.remove();

  surveys.forEach(s => {
    const div = document.createElement('div');
    div.className = 'card';
    div.id = `survey-${s.id}`;
    div.innerHTML = `
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
    `;
    listEl.appendChild(div);
  });

}

function syncLoadMoreBtn() {
  let btn = document.getElementById('load-more-btn');
  if (nextUrl) {
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'load-more-btn';
      btn.className = 'btn btn-outline';
      btn.style.cssText = 'display:block; margin:16px auto 0';
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        await loadSurveys(nextUrl);
      });
      listEl.after(btn);
    }
    btn.disabled = false;
    btn.textContent = 'Загрузить ещё';
  } else {
    btn?.remove();
  }
}

async function deleteSurvey(id) {
  if (!confirm('Удалить опрос? Данные сессий сохранятся.')) return;
  try {
    await api.delete(`/api/surveys/${id}/`);
    document.getElementById(`survey-${id}`)?.remove();
    if (!listEl.querySelector('.card')) {
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
