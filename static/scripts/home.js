document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('menuBtn');
    const modal = document.getElementById('modal');
    const addBtn = document.querySelector('.add-playlist');
    const cancelBtn = document.getElementById('cancelBtn');
    const okBtn = document.getElementById('okBtn');
    const videoList = document.querySelector('.video-list');

    // メニューへ遷移
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            window.location.href = 'menu.html';
        });
    }

    // クイズボタン遷移（静的項目）
    document.querySelectorAll('.quiz-btn').forEach(button => {
        button.addEventListener('click', () => {
            const link = button.getAttribute('data-link');
            if (link) {
                window.location.href = link;
            }
        });
    });

    // モーダル表示/非表示
    addBtn.addEventListener('click', () => modal.classList.remove('hidden'));
    cancelBtn.addEventListener('click', () => modal.classList.add('hidden'));

    // モーダルでOKを押したら追加
    okBtn.addEventListener('click', () => {
        const title = document.getElementById('videoTitle').value.trim();
        const url = document.getElementById('videoUrl').value.trim();

        if (title && url) {
            const newItem = { title, url };
            addVideoItem(newItem);
            saveToLocalStorage(newItem);
            modal.classList.add('hidden');
            document.getElementById('videoTitle').value = '';
            document.getElementById('videoUrl').value = '';
        } else {
            alert('タイトルとURLを入力してください');
        }
    });

    // 既存データ読み込み
    loadFromLocalStorage();

    // 再生リストを画面に追加する関数
    function addVideoItem({ title, url }, index = null) {
        const li = document.createElement('li');
        li.className = 'video-item';
        li.innerHTML = `
            <span class="video-title">${title}</span>
            <button class="quiz-btn" data-link="quiz.html">クイズ</button>
            <button class="delete-btn">削除</button>
        `;

        // クイズボタン
        li.querySelector('.quiz-btn').addEventListener('click', () => {
            window.location.href = 'quiz.html';
        });

        // 削除ボタン
        li.querySelector('.delete-btn').addEventListener('click', () => {
            if (confirm(`「${title}」を削除しますか？`)) {
                li.remove();
                deleteFromLocalStorage(index ?? getIndexByTitle(title));
            }
        });

        videoList.appendChild(li);
    }

    function getIndexByTitle(title) {
        const items = JSON.parse(localStorage.getItem('playlistItems')) || [];
        return items.findIndex(item => item.title === title);
    }

    function saveToLocalStorage(item) {
        const items = JSON.parse(localStorage.getItem('playlistItems')) || [];
        items.push(item);
        localStorage.setItem('playlistItems', JSON.stringify(items));
    }

    function loadFromLocalStorage() {
        const items = JSON.parse(localStorage.getItem('playlistItems')) || [];
        items.forEach((item, index) => {
            addVideoItem(item, index);
        });
    }

    function deleteFromLocalStorage(index) {
        const items = JSON.parse(localStorage.getItem('playlistItems')) || [];
        if (index >= 0 && index < items.length) {
            items.splice(index, 1);
            localStorage.setItem('playlistItems', JSON.stringify(items));
        }
    }
});
