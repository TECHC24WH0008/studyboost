window.addEventListener('DOMContentLoaded', () => {
  const correct = parseInt(localStorage.getItem('correctCount') || '0');
  const total = parseInt(localStorage.getItem('totalCount') || '1');
  const rate = Math.round((correct / total) * 100);
  document.getElementById('result-text').textContent = `正解数: ${correct} / ${total}　正答率: ${rate}%`;

  const userAnswers = JSON.parse(localStorage.getItem('userAnswers') || '[]');
  const questions = JSON.parse(localStorage.getItem('questions') || '[]');
  const container = document.getElementById('review-container');

  questions.forEach((q, i) => {
    const userAnswer = userAnswers[i];
    const reviewDiv = document.createElement('div');
    reviewDiv.className = 'review-question';
    reviewDiv.innerHTML = `
      <h3>Q${i + 1}: ${q.title}</h3>
      <p>あなたの回答: ${q.choices[userAnswer] || '未回答'}</p>
      <p>正解: ${q.choices[q.answer]}</p>
      <button class="toggle-explanation">解説</button>
      <div class="explanation">
        <p>${q.explanation || '解説はまだありません。'}</p>
        <span class="close">×</span>
      </div>
    `;

    reviewDiv.querySelector('.toggle-explanation').addEventListener('click', () => {
      reviewDiv.querySelector('.explanation').style.display = 'block';
    });

    reviewDiv.querySelector('.close').addEventListener('click', () => {
      reviewDiv.querySelector('.explanation').style.display = 'none';
    });

    container.appendChild(reviewDiv);
  });
});
