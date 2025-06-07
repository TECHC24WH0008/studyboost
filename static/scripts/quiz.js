const questions = [
  { title: "クイズの内容", choices: ["選択肢1", "選択肢2", "選択肢3", "選択肢4"], answer: 0, explanation: "選択肢1が正解です。なぜなら..." },
  { title: "クイズの内容", choices: ["A", "B", "C", "D"], answer: 2, explanation: "Cが正しい理由は..." },
  { title: "クイズの内容", choices: ["赤", "青", "黄", "緑"], answer: 1, explanation: "青が正しいのは..." },
  { title: "クイズの内容", choices: ["犬", "猫", "鳥", "魚"], answer: 3, explanation: "魚が正しい理由..." },
  { title: "クイズの内容", choices: ["春", "夏", "秋", "冬"], answer: 0, explanation: "春が正しいのは..." }
];

let currentQuestion = 0;
let correctCount = 0;
let userAnswers = [];

const totalQuestions = questions.length;

const questionTitle = document.getElementById('question-title');
const choicesDiv = document.getElementById('choices');
const progressBar = document.getElementById('progress-bar');

document.getElementById('back-button').addEventListener('click', () => {
  if (currentQuestion > 0) {
    currentQuestion--;
    loadQuestion();
  }
});

function updateProgressBar() {
  const progressPercent = (currentQuestion / totalQuestions) * 100;
  progressBar.style.width = `${progressPercent}%`;
}

function loadQuestion() {
  updateProgressBar();

  const q = questions[currentQuestion];
  questionTitle.textContent = q.title;
  choicesDiv.innerHTML = '';

  q.choices.forEach((choiceText, index) => {
    const btn = document.createElement('button');
    btn.textContent = choiceText;
    btn.disabled = false;
    btn.classList.remove('correct', 'incorrect');

    btn.addEventListener('click', () => {
      // 回答を記録
      userAnswers.push(index);

      // 全てのボタンを無効化
      const allButtons = document.querySelectorAll('#choices button');
      allButtons.forEach(b => b.disabled = true);

      if (index === q.answer) {
        correctCount++;
        btn.classList.add('correct');
        btn.textContent += ' 〇';
      } else {
        btn.classList.add('incorrect');
        btn.textContent += ' ✕';

        // 正解の選択肢に〇を表示
        allButtons[q.answer].classList.add('correct');
        allButtons[q.answer].textContent += ' 〇';
      }

      // 次の問題へ
      setTimeout(() => {
        nextQuestion();
      }, 1000);
    });

    choicesDiv.appendChild(btn);
  });
}

function nextQuestion() {
  currentQuestion++;
  if (currentQuestion < totalQuestions) {
    loadQuestion();
  } else {
    // 結果と復習用データを保存
    localStorage.setItem('correctCount', correctCount);
    localStorage.setItem('totalCount', totalQuestions);
    localStorage.setItem('userAnswers', JSON.stringify(userAnswers));
    localStorage.setItem('questions', JSON.stringify(questions));

    window.location.href = 'result.html';
  }
}

window.addEventListener('DOMContentLoaded', loadQuestion);
