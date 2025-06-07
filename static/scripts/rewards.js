document.addEventListener('DOMContentLoaded', () => {
  const rewardList = document.getElementById('rewardList');
  const currentPointsElem = document.getElementById('currentPoints');

  // ダミーデータ
  const rewards = [
    {
      id: 1,
      title: 'Study Boost オリジナルノート',
      desc: '頑張ったあなたにぴったりのノートです！',
      points: 1200,
      img: '../assets/images/note.png'
    },
    {
      id: 2,
      title: 'Amazonギフト券 500円分',
      desc: 'お好きなものを買えるギフト券！',
      points: 3000,
      img: '../assets/images/gift.png'
    },
    {
      id: 3,
      title: '特製ステッカーセット',
      desc: 'やる気アップのカラフルステッカー！',
      points: 1500,
      img: '../assets/images/sticker.png'
    },
    {
      id: 4,
      title: 'iFace',
      desc: 'あなたのスマホに個性と保護をプラス！',
      points: 30000,
      img: '../assets/images/iface.png'
    },
    {
      id: 5,
      title: 'お菓子詰め合わせ',
      desc: 'やる気回復！ちょっとした幸せをどうぞ！',
      points: 1000,
      img: '../assets/images/foods.png'
    }
  ];

  // 現在のポイント（localStorageから取得 or 1000pt固定）
  let currentPoints = parseInt(localStorage.getItem('userPoints')) || 1200;
  currentPointsElem.textContent = currentPoints;

  // モーダル要素
  const modal = document.getElementById('modal');
  const modalTitle = document.getElementById('modalTitle');
  const modalDesc = document.getElementById('modalDesc');
  const modalPoints = document.getElementById('modalPoints');
  const confirmBtn = document.getElementById('confirmBtn');
  const cancelBtn = document.getElementById('cancelBtn');

  // 商品選択用変数
  let selectedReward = null;

  function renderRewards() {
    rewardList.innerHTML = '';
    rewards.forEach(r => {
      const li = document.createElement('li');
      li.className = 'reward-item';

      li.innerHTML = `
        <img src="${r.img}" alt="${r.title}" />
        <div class="reward-title">${r.title}</div>
        <div class="reward-desc">${r.desc}</div>
        <div class="reward-points">必要ポイント: ${r.points}pt</div>
        <button class="reward-btn" ${currentPoints < r.points ? 'disabled class="disabled"' : ''}>交換する</button>
      `;

      // 交換ボタン押下イベント
      const btn = li.querySelector('button');
      btn.addEventListener('click', () => {
        selectedReward = r;
        modalTitle.textContent = r.title;
        modalDesc.textContent = r.desc;
        modalPoints.textContent = r.points;
        modal.classList.remove('hidden');
      });

      rewardList.appendChild(li);
    });
  }

  confirmBtn.addEventListener('click', () => {
    if (!selectedReward) return;
    if (currentPoints >= selectedReward.points) {
      currentPoints -= selectedReward.points;
      localStorage.setItem('userPoints', currentPoints);
      currentPointsElem.textContent = currentPoints;
      alert(`${selectedReward.title} と交換しました！`);
      modal.classList.add('hidden');
      renderRewards();
    } else {
      alert('ポイントが足りません。');
    }
  });

  cancelBtn.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  // 初期レンダリング
  renderRewards();

  // 戻るボタンイベント
  document.querySelector('.back-btn').addEventListener('click', () => {
    location.href = 'home.html';
  });
});
