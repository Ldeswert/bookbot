/* Spanish Learning App — Frontend Logic */

const App = {
  currentView: "dashboard",
  flashcards: [],
  fcIndex: 0,
  fcFlipped: false,
  quizQuestions: [],
  quizIndex: 0,
  quizScore: 0,
  matchData: null,
  matchSelected: null,
  matchMatched: 0,
  matchWrong: 0,

  init() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => this.navigate(btn.dataset.view));
    });
    document.getElementById("chat-send").addEventListener("click", () => this.sendChat());
    document.getElementById("chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") this.sendChat();
    });
    document.getElementById("chat-clear").addEventListener("click", () => this.clearChat());
    this.navigate("dashboard");
  },

  navigate(view) {
    this.currentView = view;
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.getElementById("view-" + view).classList.add("active");
    if (view === "dashboard") this.loadDashboard();
    if (view === "flashcards") this.loadFlashcards();
    if (view === "quiz") this.loadQuiz();
    if (view === "matching") this.loadMatching();
    if (view === "chat") this.loadChat();
  },

  // ---- Dashboard ----
  async loadDashboard() {
    const res = await fetch("/api/stats");
    const s = await res.json();
    document.getElementById("stats-grid").innerHTML = `
      <div class="stat-box"><div class="num">${s.total_words}</div><div class="label">Total Words</div></div>
      <div class="stat-box"><div class="num">${s.due_count}</div><div class="label">Due for Review</div></div>
      <div class="stat-box"><div class="num">${s.learned}</div><div class="label">Learned (3+ reps)</div></div>
      <div class="stat-box"><div class="num">${s.chat_count}</div><div class="label">Chat Messages</div></div>
    `;
    const hist = document.getElementById("quiz-history");
    if (s.quiz_history.length === 0) {
      hist.innerHTML = '<p style="color:var(--text-muted)">No quizzes yet. Take your first quiz!</p>';
    } else {
      hist.innerHTML = s.quiz_history
        .map((q) => `<div class="quiz-row"><span>${new Date(q.completed_at).toLocaleDateString()}</span><span class="quiz-score">${q.score}/${q.total}</span></div>`)
        .join("");
    }
  },

  // ---- Flashcards ----
  async loadFlashcards() {
    const container = document.getElementById("flashcard-container");
    container.innerHTML = '<div class="empty-state">Loading flashcards…</div>';
    const res = await fetch("/api/flashcards/due");
    this.flashcards = await res.json();
    this.fcIndex = 0;
    this.fcFlipped = false;
    if (this.flashcards.length === 0) {
      container.innerHTML = '<div class="empty-state"><h3>All caught up!</h3><p>No cards due for review. Come back later.</p></div>';
      return;
    }
    this.renderFlashcard();
  },

  renderFlashcard() {
    const c = this.flashcards[this.fcIndex];
    const container = document.getElementById("flashcard-container");
    const progress = ((this.fcIndex) / this.flashcards.length) * 100;
    container.innerHTML = `
      <div class="progress-bar"><div class="fill" style="width:${progress}%"></div></div>
      <div class="flashcard" id="fc-card">
        <div class="category">${c.category}</div>
        <div class="word">${c.spanish}</div>
        <div class="hint">Click to flip</div>
      </div>
      <div class="review-buttons" id="review-btns" style="display:none">
        <button class="btn-again" data-q="1">Again</button>
        <button class="btn-hard" data-q="3">Hard</button>
        <button class="btn-good" data-q="4">Good</button>
        <button class="btn-easy" data-q="5">Easy</button>
      </div>
    `;
    document.getElementById("fc-card").addEventListener("click", () => this.flipCard());
    document.querySelectorAll("#review-btns button").forEach((btn) => {
      btn.addEventListener("click", () => this.reviewCard(parseInt(btn.dataset.q)));
    });
  },

  flipCard() {
    if (this.fcFlipped) return;
    this.fcFlipped = true;
    const c = this.flashcards[this.fcIndex];
    const card = document.getElementById("fc-card");
    card.innerHTML = `
      <div class="category">${c.category}</div>
      <div class="word">${c.spanish}</div>
      <div class="translation">${c.english}</div>
    `;
    document.getElementById("review-btns").style.display = "flex";
  },

  async reviewCard(quality) {
    const c = this.flashcards[this.fcIndex];
    await fetch("/api/flashcards/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ word_id: c.id, quality }),
    });
    this.fcIndex++;
    this.fcFlipped = false;
    if (this.fcIndex >= this.flashcards.length) {
      document.getElementById("flashcard-container").innerHTML =
        '<div class="empty-state"><h3>Session complete!</h3><p>You reviewed all due cards.</p></div>';
      return;
    }
    this.renderFlashcard();
  },

  // ---- Quiz ----
  async loadQuiz() {
    const container = document.getElementById("quiz-container");
    container.innerHTML = '<div class="empty-state">Loading quiz…</div>';
    const res = await fetch("/api/quiz");
    this.quizQuestions = await res.json();
    this.quizIndex = 0;
    this.quizScore = 0;
    if (this.quizQuestions.length === 0) {
      container.innerHTML = '<div class="empty-state"><h3>Not enough words</h3></div>';
      return;
    }
    this.renderQuizQuestion();
  },

  renderQuizQuestion() {
    const q = this.quizQuestions[this.quizIndex];
    const container = document.getElementById("quiz-container");
    const progress = ((this.quizIndex) / this.quizQuestions.length) * 100;
    container.innerHTML = `
      <div class="progress-bar"><div class="fill" style="width:${progress}%"></div></div>
      <div class="card">
        <p style="color:var(--text-muted);text-align:center;margin-bottom:0.5rem;font-size:0.85rem">
          Question ${this.quizIndex + 1} of ${this.quizQuestions.length} · Score: ${this.quizScore}
        </p>
        <div class="quiz-question">${q.prompt}</div>
        <div class="quiz-options" id="quiz-options">
          ${q.options.map((o) => `<button class="quiz-option" data-opt="${o}">${o}</button>`).join("")}
        </div>
        <div class="quiz-feedback" id="quiz-feedback"></div>
      </div>
    `;
    document.querySelectorAll(".quiz-option").forEach((btn) => {
      btn.addEventListener("click", () => this.answerQuiz(btn.dataset.opt));
    });
  },

  answerQuiz(selected) {
    const q = this.quizQuestions[this.quizIndex];
    const correct = selected === q.answer;
    const options = document.querySelectorAll(".quiz-option");
    options.forEach((btn) => {
      btn.classList.add("disabled");
      if (btn.dataset.opt === q.answer) btn.classList.add("correct");
      else if (btn.dataset.opt === selected) btn.classList.add("wrong");
    });
    const fb = document.getElementById("quiz-feedback");
    if (correct) {
      this.quizScore++;
      fb.innerHTML = '<span style="color:var(--green)">✓ Correct!</span>';
    } else {
      fb.innerHTML = `<span style="color:var(--red)">✗ Answer: ${q.answer}</span>`;
    }
    setTimeout(() => {
      this.quizIndex++;
      if (this.quizIndex >= this.quizQuestions.length) {
        this.finishQuiz();
      } else {
        this.renderQuizQuestion();
      }
    }, 1200);
  },

  async finishQuiz() {
    await fetch("/api/quiz/result", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ score: this.quizScore, total: this.quizQuestions.length }),
    });
    const pct = Math.round((this.quizScore / this.quizQuestions.length) * 100);
    document.getElementById("quiz-container").innerHTML = `
      <div class="card" style="text-align:center">
        <h2>Quiz Complete!</h2>
        <div style="font-size:3rem;font-weight:800;color:var(--primary);margin:1rem 0">${this.quizScore}/${this.quizQuestions.length}</div>
        <p style="color:var(--text-muted);margin-bottom:1.5rem">${pct}% correct</p>
        <button class="btn-start" onclick="App.loadQuiz()">New Quiz</button>
      </div>
    `;
  },

  // ---- Matching ----
  async loadMatching() {
    const container = document.getElementById("matching-container");
    container.innerHTML = '<div class="empty-state">Loading…</div>';
    const res = await fetch("/api/matching");
    this.matchData = await res.json();
    this.matchSelected = null;
    this.matchMatched = 0;
    this.matchWrong = 0;
    this.renderMatching();
  },

  renderMatching() {
    const container = document.getElementById("matching-container");
    const total = this.matchData.spanish.length;
    if (this.matchMatched >= total) {
      container.innerHTML = `
        <div class="card" style="text-align:center">
          <h2>Matching Complete!</h2>
          <div style="font-size:2rem;font-weight:800;color:var(--primary);margin:1rem 0">
            ${total - this.matchWrong}/${total} correct
          </div>
          <p style="color:var(--text-muted);margin-bottom:1.5rem">${this.matchWrong} wrong attempts</p>
          <button class="btn-start" onclick="App.loadMatching()">New Round</button>
        </div>
      `;
      return;
    }
    container.innerHTML = `
      <div class="card">
        <p style="color:var(--text-muted);margin-bottom:1rem;font-size:0.85rem">
          Match: ${this.matchMatched}/${total} · Wrong: ${this.matchWrong}
        </p>
        <div class="matching-grid">
          <div class="match-col" id="match-spanish">
            ${this.matchData.spanish.map((w) =>
              `<div class="match-item ${w.matched ? "matched" : ""}" data-id="${w.id}" data-side="spanish">${w.text}</div>`
            ).join("")}
          </div>
          <div class="match-col" id="match-english">
            ${this.matchData.english.map((w) =>
              `<div class="match-item ${w.matched ? "matched" : ""}" data-id="${w.id}" data-side="english">${w.text}</div>`
            ).join("")}
          </div>
        </div>
      </div>
    `;
    document.querySelectorAll(".match-item:not(.matched)").forEach((el) => {
      el.addEventListener("click", () => this.selectMatch(el));
    });
  },

  selectMatch(el) {
    const id = parseInt(el.dataset.id);
    const side = el.dataset.side;

    if (this.matchSelected === null) {
      this.matchSelected = { id, side, el };
      el.classList.add("selected");
    } else {
      if (this.matchSelected.side === side) {
        this.matchSelected.el.classList.remove("selected");
        this.matchSelected = { id, side, el };
        el.classList.add("selected");
        return;
      }
      const prev = this.matchSelected;
      if (prev.id === id) {
        prev.el.classList.remove("selected");
        prev.el.classList.add("matched");
        el.classList.add("matched");
        this.matchData.spanish.find((w) => w.id === id).matched = true;
        this.matchData.english.find((w) => w.id === id).matched = true;
        this.matchMatched++;
      } else {
        el.classList.add("wrong");
        this.matchWrong++;
        setTimeout(() => el.classList.remove("wrong"), 400);
      }
      prev.el.classList.remove("selected");
      this.matchSelected = null;
      setTimeout(() => this.renderMatching(), 300);
    }
  },

  // ---- Chat ----
  async loadChat() {
    const res = await fetch("/api/chat/history");
    const history = await res.json();
    const container = document.getElementById("chat-messages");
    container.innerHTML = history.map((m) =>
      `<div class="chat-msg ${m.role}"><div class="bubble">${this.escape(m.content)}</div></div>`
    ).join("");
    container.scrollTop = container.scrollHeight;
  },

  async sendChat() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    const container = document.getElementById("chat-messages");
    container.innerHTML += `<div class="chat-msg user"><div class="bubble">${this.escape(msg)}</div></div>`;
    container.scrollTop = container.scrollHeight;

    const sendBtn = document.getElementById("chat-send");
    sendBtn.disabled = true;
    sendBtn.textContent = "…";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      if (res.ok) {
        container.innerHTML += `<div class="chat-msg assistant"><div class="bubble">${this.escape(data.reply)}</div></div>`;
      } else {
        container.innerHTML += `<div class="chat-msg assistant"><div class="bubble" style="color:var(--red)">⚠ ${this.escape(data.error)}</div></div>`;
      }
    } catch (e) {
      container.innerHTML += `<div class="chat-msg assistant"><div class="bubble" style="color:var(--red)">⚠ Connection error</div></div>`;
    }
    container.scrollTop = container.scrollHeight;
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
  },

  async clearChat() {
    await fetch("/api/chat/clear", { method: "POST" });
    this.loadChat();
  },

  escape(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  },
};

App.init();
