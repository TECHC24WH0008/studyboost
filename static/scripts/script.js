document.addEventListener('DOMContentLoaded', function() {
    const navButtons = document.querySelectorAll('[data-link]');
    navButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // ボタンのデフォルト動作を防ぐ
            const target = btn.getAttribute('data-link');
            if (target) {
                window.location.href = target;
            }
        });
    });
});
