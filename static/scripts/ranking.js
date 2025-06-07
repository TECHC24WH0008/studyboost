document.addEventListener("DOMContentLoaded", () => {
  // ホーム画面へのリンク
  document.querySelectorAll('[data-link]').forEach(btn => {
    btn.addEventListener('click', () => {
      window.location.href = btn.dataset.link;
    });
  });

  // ランキングデータ（仮の静的データ）
  const rankingData = {
    daily: [
      { name: 'ユーザーA', points: 120 },
      { name: 'ユーザーB', points: 110 },
      { name: 'ユーザーC', points: 100 }
    ],
    weekly: [
      { name: 'ユーザーB', points: 800 },
      { name: 'ユーザーA', points: 760 },
      { name: 'ユーザーD', points: 700 }
    ],
    monthly: [
      { name: 'ユーザーC', points: 3200 },
      { name: 'ユーザーA', points: 3100 },
      { name: 'ユーザーE', points: 3000 }
    ]
  };

  const rankingList = document.getElementById('ranking-list');
  const tabButtons = document.querySelectorAll('.tab-button');

  // ユーザー情報表示用の要素
  const userNameEl = document.getElementById('user-name');
  const userPointsEl = document.getElementById('user-points');

  // localStorage から名前とポイントを取得
  const userName = localStorage.getItem('userName') || 'あなたの名前';
  const userPoints = localStorage.getItem('userPoints') || '0';

  userNameEl.textContent = userName;
  userPointsEl.textContent = `ポイント: ${userPoints}pt`;

  // ランキング描画関数
  function renderRanking(period) {
    rankingList.innerHTML = '';
    rankingData[period].forEach((user, index) => {
      const li = document.createElement('li');
      li.setAttribute('data-rank', `${index + 1}位`);
      li.innerHTML = `${user.name} - ${user.points}pt`;

      // 1位だけ王冠アイコンを表示
      if (index === 0) {
        li.innerHTML = '👑 ' + li.innerHTML;
      }

      rankingList.appendChild(li);
    });
  }

  // 初期表示（日別ランキング）
  renderRanking('daily');

  // タブ切り替え
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const period = btn.dataset.period;

      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      renderRanking(period);
    });
  });
});
