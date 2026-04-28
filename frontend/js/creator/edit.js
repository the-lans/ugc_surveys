checkAuth('creator');
renderHeader();

const params    = new URLSearchParams(location.search);
const surveyId  = params.get('id');

if (!surveyId) window.location.href = '/creator/surveys.html';

const errEl        = document.getElementById('error');
const lockedBanner = document.getElementById('locked-banner');
const titleInput   = document.getElementById('survey-title');
const titleStatus  = document.getElementById('title-status');
const questionsList = document.getElementById('questions-list');
const addCard      = document.getElementById('add-question-card');
const addForm      = document.getElementById('add-question-form');
const addErrEl     = document.getElementById('add-error');
const addBtn       = document.getElementById('add-q-btn');
const optionsList  = document.getElementById('options-list');
const addOptBtn    = document.getElementById('add-option-btn');
const optSection   = document.getElementById('options-section');

let isLocked  = false;
let optionCount = 0;

// ── Загрузка опроса ─────────────────────────────────────────
async function loadSurvey() {
  try {
    const survey = await api.get(`/api/surveys/${surveyId}/`);
    titleInput.value = survey.title;
    if (survey.is_locked) setLocked();
    renderQuestions(survey.questions || []);
  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
  }
}

// ── Сохранение заголовка по blur ────────────────────────────
let saveTitleTimer = null;
titleInput.addEventListener('input', () => {
  clearTimeout(saveTitleTimer);
  titleStatus.textContent = '';
  saveTitleTimer = setTimeout(saveTitle, 800);
});

async function saveTitle() {
  const title = titleInput.value.trim();
  if (!title) return;
  try {
    await api.patch(`/api/surveys/${surveyId}/`, { title });
    titleStatus.textContent = 'Сохранено';
    setTimeout(() => { titleStatus.textContent = ''; }, 2000);
  } catch (err) {
    const msg = extractError(err);
    if (msg.includes('заблокирован') || msg.includes('ответы')) {
      setLocked();
    } else {
      titleStatus.textContent = 'Ошибка сохранения';
    }
  }
}

// ── Рендер вопросов ─────────────────────────────────────────
function renderQuestions(questions) {
  if (!questions.length) {
    questionsList.innerHTML = '<p class="text-muted mb-20">Вопросов пока нет.</p>';
    return;
  }
  questionsList.innerHTML = questions.map(q => `
    <div class="card" id="q-${q.id}" data-order="${q.order}" style="margin-bottom:10px">
      <div class="card-header">
        <div>
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px">
            <span class="badge badge-${q.question_type}">
              ${{ single: 'Один вариант', multiple: 'Несколько вариантов', text: 'Текст' }[q.question_type]}
            </span>
            <span style="font-size:12px; color:var(--muted)">№ ${q.order}</span>
          </div>
          <div class="card-title">${escHtml(q.text)}</div>
          ${q.options.length ? `
            <ul style="margin-top:8px; padding-left:16px; font-size:13px; color:var(--muted)">
              ${q.options.map(o => `<li>${escHtml(o.text)}</li>`).join('')}
            </ul>
          ` : ''}
        </div>
        ${!isLocked ? `
          <div class="card-actions">
            <button class="btn btn-danger btn-sm" onclick="deleteQuestion(${q.id})">Удалить</button>
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

async function deleteQuestion(qId) {
  if (!confirm('Удалить вопрос?')) return;
  try {
    await api.delete(`/api/surveys/${surveyId}/questions/${qId}/`);
    document.getElementById(`q-${qId}`)?.remove();
    if (!questionsList.querySelector('.card')) {
      questionsList.innerHTML = '<p class="text-muted mb-20">Вопросов пока нет.</p>';
    }
  } catch (err) {
    alert(extractError(err));
  }
}

// ── Блокировка редактирования ────────────────────────────────
function setLocked() {
  isLocked = true;
  lockedBanner.classList.remove('hidden');
  titleInput.disabled = true;
  addCard.classList.add('hidden');
}

// ── Управление вариантами ответа в форме ────────────────────
function addOptionRow() {
  optionCount++;
  const row = document.createElement('div');
  row.className = 'option-row';
  row.innerHTML = `
    <input class="form-input" type="text" name="option" placeholder="Вариант ${optionCount}" required>
    <button type="button" class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()">✕</button>
  `;
  optionsList.appendChild(row);
}

addOptBtn.addEventListener('click', addOptionRow);

// Показываем/скрываем варианты в зависимости от типа
document.querySelectorAll('input[name="qtype"]').forEach(radio => {
  radio.addEventListener('change', () => {
    const isText = radio.value === 'text';
    optSection.style.display = isText ? 'none' : '';
    optionsList.querySelectorAll('input[name="option"]').forEach(
      i => { i.required = !isText; }
    );
  });
});

// ── Добавление вопроса ──────────────────────────────────────
addForm.addEventListener('submit', async e => {
  e.preventDefault();
  hideError(addErrEl);
  setLoading(addBtn, true, 'Добавить вопрос');

  const qtype = document.querySelector('input[name="qtype"]:checked').value;
  const options = [...optionsList.querySelectorAll('input[name="option"]')]
    .map((inp, idx) => ({ text: inp.value.trim(), order: idx + 1 }))
    .filter(o => o.text);

  // Определяем следующий номер порядка по максимальному order среди существующих
  const orders = [...questionsList.querySelectorAll('.card[data-order]')]
    .map(el => parseInt(el.dataset.order, 10));
  const order = orders.length ? Math.max(...orders) + 1 : 1;

  try {
    const newQ = await api.post(`/api/surveys/${surveyId}/questions/`, {
      text: document.getElementById('q-text').value.trim(),
      question_type: qtype,
      order,
      options: qtype !== 'text' ? options : [],
    });

    // Добавляем новый вопрос в список без перезагрузки
    if (questionsList.querySelector('p.text-muted')) {
      questionsList.innerHTML = '';
    }
    const tmp = document.createElement('div');
    tmp.innerHTML = `
      <div class="card" id="q-${newQ.id}" data-order="${newQ.order}" style="margin-bottom:10px">
        <div class="card-header">
          <div>
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px">
              <span class="badge badge-${newQ.question_type}">
                ${{ single: 'Один вариант', multiple: 'Несколько вариантов', text: 'Текст' }[newQ.question_type]}
              </span>
              <span style="font-size:12px; color:var(--muted)">№ ${newQ.order}</span>
            </div>
            <div class="card-title">${escHtml(newQ.text)}</div>
            ${(newQ.options || []).length ? `
              <ul style="margin-top:8px; padding-left:16px; font-size:13px; color:var(--muted)">
                ${newQ.options.map(o => `<li>${escHtml(o.text)}</li>`).join('')}
              </ul>
            ` : ''}
          </div>
          <div class="card-actions">
            <button class="btn btn-danger btn-sm" onclick="deleteQuestion(${newQ.id})">Удалить</button>
          </div>
        </div>
      </div>
    `;
    questionsList.appendChild(tmp.firstElementChild);

    // Сброс формы
    addForm.reset();
    optionsList.innerHTML = '';
    optionCount = 0;
    optSection.style.display = '';

  } catch (err) {
    const msg = extractError(err);
    if (msg.includes('заблокирован') || msg.includes('ответы')) {
      setLocked();
    } else {
      addErrEl.textContent = msg;
      addErrEl.classList.remove('hidden');
    }
  } finally {
    setLoading(addBtn, false, 'Добавить вопрос');
  }
});

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Инициализация: добавить 2 варианта по умолчанию
addOptionRow();
addOptionRow();
loadSurvey();
