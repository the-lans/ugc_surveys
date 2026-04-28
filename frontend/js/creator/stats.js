checkAuth('creator');
renderHeader();

const params   = new URLSearchParams(location.search);
const surveyId = params.get('id');
if (!surveyId) window.location.href = '/creator/surveys.html';

const errEl   = document.getElementById('error');
const content = document.getElementById('content');

async function loadStats() {
  content.innerHTML = '<p class="text-muted">Загрузка…</p>';
  try {
    const s = await api.get(`/api/surveys/${surveyId}/stats/`);
    render(s);
  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
    content.innerHTML = '';
  }
}

function render(s) {
  const avgTime = s.avg_completion_time_seconds != null
    ? formatSeconds(s.avg_completion_time_seconds)
    : 'н/д';

  content.innerHTML = `
    <h1 class="page-title">${escHtml(s.title)}</h1>

    <!-- Общая статистика -->
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px,1fr)); gap:12px; margin-bottom:28px">
      ${statBox('Всего сессий',    s.total_sessions)}
      ${statBox('Завершено',       s.completed_sessions)}
      ${statBox('Завершаемость',   s.completion_rate + '%')}
      ${statBox('Среднее время',   avgTime)}
    </div>

    <!-- Вопросы -->
    ${s.questions.map(renderQuestion).join('')}
  `;
}

function statBox(label, value) {
  return `
    <div class="card" style="text-align:center; padding:16px">
      <div style="font-size:26px; font-weight:700; color:var(--primary)">${escHtml(String(value))}</div>
      <div class="text-muted" style="font-size:12px; margin-top:4px">${escHtml(label)}</div>
    </div>
  `;
}

function renderQuestion(q) {
  const typeLabel = { single: 'Один вариант', multiple: 'Несколько вариантов', text: 'Текст' };
  const body = q.question_type === 'text'
    ? renderTextQuestion(q)
    : renderChoiceQuestion(q);

  return `
    <div class="card" style="margin-bottom:12px">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px">
        <span class="badge badge-${q.question_type}">${typeLabel[q.question_type]}</span>
      </div>
      <div class="card-title" style="margin-bottom:14px">${escHtml(q.text)}</div>
      ${body}
    </div>
  `;
}

function renderChoiceQuestion(q) {
  if (!q.options || !q.options.length) {
    return '<p class="text-muted">Нет ответов</p>';
  }
  return q.options.map(o => `
    <div class="stat-option">
      <div class="stat-option-header">
        <span>${escHtml(o.text)}</span>
        <span class="stat-option-pct">${o.count} (${o.percentage}%)</span>
      </div>
      <div class="stat-bar-track">
        <div class="stat-bar-fill" style="width:${o.percentage}%"></div>
      </div>
    </div>
  `).join('');
}

function renderTextQuestion(q) {
  const count = q.answer_count || 0;
  const samples = q.sample_answers || [];
  return `
    <p class="text-muted" style="margin-bottom:10px">Ответов: <strong>${count}</strong></p>
    ${samples.length ? `
      <ul style="padding-left:16px; font-size:14px; color:var(--text)">
        ${samples.map(a => `<li style="margin-bottom:4px">${escHtml(a)}</li>`).join('')}
      </ul>
    ` : '<p class="text-muted">Ещё нет ответов</p>'}
  `;
}

function formatSeconds(s) {
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return m ? `${m} мин ${sec} сек` : `${sec} сек`;
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

loadStats();
