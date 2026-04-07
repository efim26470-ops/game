(function() {
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();

    const scoreElement = document.getElementById('score');
    const clickableImage = document.getElementById('clickableImage');

    if (!scoreElement || !clickableImage) {
        console.error('Elements not found');
        return;
    }

    // Получаем user_id из Telegram
    let userId = null;
    let username = "Anonymous";
    try {
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userId = tg.initDataUnsafe.user.id;
            username = tg.initDataUnsafe.user.username || `user_${userId}`;
            console.log('User ID:', userId);
        } else {
            console.warn('No user data, trying to get via initData');
        }
    } catch(e) {
        console.error('Error getting user:', e);
    }

    let score = 0;

    async function loadScore() {
        if (!userId) return;
        try {
            const res = await fetch(`/api/score?user_id=${userId}`);
            if (res.ok) {
                const data = await res.json();
                score = data.score || 0;
                scoreElement.innerText = score;
                console.log('Loaded score:', score);
            }
        } catch(e) { console.error('Load error:', e); }
    }

    async function saveScore() {
        if (!userId) return;
        try {
            await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username, score })
            });
            console.log('Saved score:', score);
        } catch(e) { console.error('Save error:', e); }
    }

    function handleClick() {
        score++;
        scoreElement.innerText = score;
        // Анимация
        clickableImage.style.transform = 'scale(0.95)';
        setTimeout(() => clickableImage.style.transform = 'scale(1)', 100);
        // Вибрация
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
        // Сохраняем
        saveScore();
    }

    clickableImage.addEventListener('click', handleClick);
    loadScore();
})();