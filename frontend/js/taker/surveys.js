checkAuth('taker');
renderHeader('surveys');

const listEl = document.getElementById('surveys-list');
const errEl  = document.getElementById('error');

let nextUrl = null;

async function loadSurveys(url = '/api/surveys/available/') {
  const isInitial = url === '/api/surveys/available/';
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
  const placeholder = listEl.querySelector('p.text-muted,p.empty-state');
  if (placeholder) placeholder.remove();

  if (!surveys.length && !listEl.querySelector('.card')) {
    listEl.innerHTML = '<p class="empty-state">Нет доступных опросов</p>';
    return;
  }

  surveys.forEach(s => {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="card-header">
        <div>
          <div class="card-title">${escHtml(s.title)}</div>
          <div class="card-meta">${s.question_count} вопросов &bull; ${escHtml(s.author)}</div>
        </div>
        <div class="card-actions">
          <a class="btn btn-primary btn-sm" href="take.html?id=${s.id}">Пройти</a>
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

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

loadSurveys();
