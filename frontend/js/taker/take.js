checkAuth('taker');
renderHeader();

const params   = new URLSearchParams(location.search);
const surveyId = params.get('id');
if (!surveyId) window.location.href = '/taker/surveys.html';

const errEl        = document.getElementById('error');
const answerErrEl  = document.getElementById('answer-error');
const questionCard = document.getElementById('question-card');
const completionEl = document.getElementById('completion');
const progressWrap = document.getElementById('progress-wrap');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const progressCount = document.getElementById('progress-count');
const questionText = document.getElementById('question-text');
const answerArea   = document.getElementById('answer-area');
const submitBtn    = document.getElementById('submit-btn');

let currentQuestion = null;

// ── Загрузить следующий вопрос ───────────────────────────────
async function loadNextQuestion() {
  hideError(answerErrEl);
  submitBtn.disabled = true;

  try {
    const q = await api.get(`/api/surveys/${surveyId}/next-question/`);

    if (q === null) {
      // 204 — опрос завершён
      showCompletion();
      return;
    }

    currentQuestion = q;
    renderQuestion(q);

  } catch (err) {
    errEl.textContent = extractError(err);
    errEl.classList.remove('hidden');
  }
}

// ── Отрисовка вопроса ────────────────────────────────────────
function renderQuestion(q) {
  const { answered, total } = q.session_progress;
  const pct = total ? Math.round((answered / total) * 100) : 0;

  progressFill.style.width = pct + '%';
  progressText.textContent = `Вопрос ${answered + 1} из ${total}`;
  progressCount.textContent = `${answered} отвечено`;

  questionText.textContent = q.text;

  if (q.question_type === 'single') {
    answerArea.innerHTML = q.options.map(o => `
      <label style="display:flex; align-items:center; gap:10px; padding:10px 12px;
                    border:1px solid var(--border); border-radius:6px; cursor:pointer; margin-bottom:8px">
        <input type="radio" name="single" value="${o.id}" style="accent-color:var(--primary)">
        <span>${escHtml(o.text)}</span>
      </label>
    `).join('');
  } else if (q.question_type === 'multiple') {
    answerArea.innerHTML = q.options.map(o => `
      <label style="display:flex; align-items:center; gap:10px; padding:10px 12px;
                    border:1px solid var(--border); border-radius:6px; cursor:pointer; margin-bottom:8px">
        <input type="checkbox" value="${o.id}" style="accent-color:var(--primary)">
        <span>${escHtml(o.text)}</span>
      </label>
    `).join('');
  } else {
    answerArea.innerHTML = `
      <textarea class="form-textarea" id="text-answer" rows="4"
                placeholder="Введите ваш ответ…"></textarea>
    `;
  }

  submitBtn.disabled = false;
}

// ── Отправка ответа ──────────────────────────────────────────
async function submitAnswer() {
  if (!currentQuestion) return;
  hideError(answerErrEl);
  setLoading(submitBtn, true, 'Ответить');

  const q = currentQuestion;
  let body = { question_id: q.question_id };

  if (q.question_type === 'single') {
    const sel = document.querySelector('input[name="single"]:checked');
    if (!sel) {
      answerErrEl.textContent = 'Выберите один вариант ответа';
      answerErrEl.classList.remove('hidden');
      setLoading(submitBtn, false, 'Ответить');
      return;
    }
    body.selected_option_ids = [parseInt(sel.value)];

  } else if (q.question_type === 'multiple') {
    const checked = [...answerArea.querySelectorAll('input[type="checkbox"]:checked')];
    if (!checked.length) {
      answerErrEl.textContent = 'Выберите хотя бы один вариант';
      answerErrEl.classList.remove('hidden');
      setLoading(submitBtn, false, 'Ответить');
      return;
    }
    body.selected_option_ids = checked.map(c => parseInt(c.value));

  } else {
    const val = document.getElementById('text-answer')?.value.trim();
    if (!val) {
      answerErrEl.textContent = 'Введите текст ответа';
      answerErrEl.classList.remove('hidden');
      setLoading(submitBtn, false, 'Ответить');
      return;
    }
    body.text_answer = val;
  }

  try {
    const result = await api.post(`/api/surveys/${surveyId}/answer/`, body);
    if (result && result.completed) {
      showCompletion();
    } else {
      await loadNextQuestion();
    }
  } catch (err) {
    answerErrEl.textContent = extractError(err);
    answerErrEl.classList.remove('hidden');
  } finally {
    setLoading(submitBtn, false, 'Ответить');
  }
}

// ── Экран завершения ─────────────────────────────────────────
function showCompletion() {
  questionCard.classList.add('hidden');
  progressWrap.classList.add('hidden');
  completionEl.classList.remove('hidden');
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Делаем submitAnswer доступной глобально (вызывается из onclick)
window.submitAnswer = submitAnswer;

loadNextQuestion();
