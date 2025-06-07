document.addEventListener('DOMContentLoaded', () => {
    const totalTimeElem = document.getElementById('totalTime');
    const totalAnswersElem = document.getElementById('totalAnswers');
    const correctAnswersElem = document.getElementById('correctAnswers');
    const badgeElem = document.getElementById('badge');

    const totalTime = parseInt(localStorage.getItem('studyTime') || '0');
    const totalAnswers = parseInt(localStorage.getItem('totalAnswers') || '0');
    const correctAnswers = parseInt(localStorage.getItem('correctAnswers') || '0');
    const accuracy = totalAnswers > 0 ? (correctAnswers / totalAnswers * 100).toFixed(1) : 0;

    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}分 ${secs}秒`;
    }

    function getBadge(accuracy, totalTime) {
        if (accuracy >= 90 && totalTime >= 600) return "🎓 神レベル学習者";
        if (accuracy >= 80) return "🔥 エリート学習者";
        if (totalTime >= 600) return "⏱️ 継続の達人";
        if (accuracy >= 50) return "💪 頑張り中！";
        return "🌱 はじめの一歩";
    }

    // 表示
    totalTimeElem.textContent = formatTime(totalTime);
    totalAnswersElem.textContent = `${totalAnswers}問`;
    correctAnswersElem.textContent = `${correctAnswers}問`;
    badgeElem.textContent = getBadge(accuracy, totalTime);

    // Chart.js グラフ表示
    const ctx = document.getElementById('accuracyChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['正解', '不正解'],
            datasets: [{
                data: [correctAnswers, totalAnswers - correctAnswers],
                backgroundColor: ['#0284c7', '#cbd5e1'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: {
                legend: { display: false }
            }
        }
    });
});
