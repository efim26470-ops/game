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

    let score = 0;
    let userId = tg.initDataUnsafe?.user?.id;
    let username = tg.initDataUnsafe?.user?.username || `user_${userId}`;

    if (!userId) {
        console.warn('No user ID, game will work but score will not be saved');
        userId = null;
    }

    // Загрузка сохранённого счёта с сервера
    async function loadScore() {
        if (!userId) return;
        try {
            const response = await fetch(`/api/score?user_id=${userId}`);
            const data = await response.json();
            if (data.score !== undefined) {
                score = data.score;
                scoreElement.innerText = score;
            }
        } catch(e) {
            console.error('Failed to load score:', e);
        }
    }

    // Отправка счёта на сервер
    async function saveScore() {
        if (!userId) return;
        try {
            await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username: username, score: score })
            });
        } catch(e) {
            console.error('Failed to save score:', e);
        }
    }

    function updateScoreDisplay() {
        scoreElement.innerText = score;
    }

    function vibrate() {
        try {
            if (tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
                tg.HapticFeedback.impactOccurred('light');
            }
        } catch(e) {}
    }

    function handleClick() {
        score++;
        updateScoreDisplay();
        vibrate();
        clickableImage.style.transform = 'scale(0.95)';
        setTimeout(() => {
            clickableImage.style.transform = 'scale(1)';
        }, 100);
        // Сохраняем счёт на сервере (но не чаще раза в секунду, можно добавить throttle)
        saveScore();
    }

    clickableImage.addEventListener('click', handleClick);
    clickableImage.onclick = handleClick;

    // Загружаем сохранённый счёт
    loadScore();
})();