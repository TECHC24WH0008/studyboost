document.addEventListener("DOMContentLoaded", () => {
  const displayName = document.getElementById('display-name');
  const nameInput = document.getElementById('name-input');
  const editButton = document.getElementById('edit-button');
  const saveButton = document.getElementById('save-button');

  // localStorage から保存済みの名前を取得
  const savedName = localStorage.getItem('userName');
  if (savedName) {
    displayName.textContent = savedName;
  }

  // 編集ボタン押下時
  editButton.addEventListener('click', () => {
    nameInput.value = displayName.textContent;
    displayName.style.display = 'none';
    nameInput.style.display = 'block';
    editButton.style.display = 'none';
    saveButton.style.display = 'inline-block';
    nameInput.focus();
  });

  // 保存ボタン押下時
  saveButton.addEventListener('click', () => {
    const newName = nameInput.value.trim();
    if (newName) {
      displayName.textContent = newName;
      localStorage.setItem('userName', newName);
    }
    displayName.style.display = 'block';
    nameInput.style.display = 'none';
    editButton.style.display = 'inline-block';
    saveButton.style.display = 'none';
  });

  // Enterキーで保存できるようにする
  nameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      saveButton.click();
    }
  });
});
