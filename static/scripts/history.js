// 最初に仮データを追加（すでにデータがある場合はスキップ）
if (!localStorage.getItem('viewHistory')) {
    const dummyHistory = [
        {
            title: '英語リスニング - 初級',
            date: '2025/06/01',
            done: false
        },
        {
            title: '歴史概論 - 日本史',
            date: '2025/06/03',
            done: true
        },
        {
            title: '数学の基礎 - 因数分解',
            date: '2025/06/05',
            done: false
        }
    ];
    localStorage.setItem('viewHistory', JSON.stringify(dummyHistory));
}

document.addEventListener('DOMContentLoaded', () => {
    const historyList = document.getElementById('historyList');
    const searchInput = document.getElementById('searchInput');

    let historyData = JSON.parse(localStorage.getItem('viewHistory') || '[]');

    function renderList(filter = '') {
        historyList.innerHTML = ''; // リストを一旦クリア

        const filtered = historyData.filter(item =>
            item.title.toLowerCase().includes(filter.toLowerCase())
        );

        if (filtered.length === 0) {
            const li = document.createElement('li');
            li.textContent = '一致する履歴がありません。';
            li.style.color = '#666';
            historyList.appendChild(li);
            return;
        }

        filtered.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'video-history-item' + (item.done ? ' done' : '');

            li.innerHTML = `
                <div>
                    <div class="video-title">${item.title}</div>
                    <div class="video-date">${item.date}</div>
                </div>
                <input type="checkbox" ${item.done ? 'checked' : ''}>
            `;

            // チェックボックスの動作
            const checkbox = li.querySelector('input');
            checkbox.addEventListener('change', (e) => {
                const realIndex = historyData.findIndex(h => h.title === item.title && h.date === item.date);
                historyData[realIndex].done = e.target.checked;
                localStorage.setItem('viewHistory', JSON.stringify(historyData));
                li.classList.toggle('done', e.target.checked);
            });

            historyList.appendChild(li);
        });
    }

    // 初期表示
    renderList();

    // 検索欄のイベント
    searchInput.addEventListener('input', (e) => {
        const keyword = e.target.value.trim();
        renderList(keyword);
    });
});
