(function() {
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();

    const scoreElement = document.getElementById('score');
    const clickableImage = document.getElementById('clickableImage');

    if (!scoreElement || !clickableImage) {
        console.error('❌ Элементы #score или #clickableImage не найдены');
        return;
    }

    // Получаем данные пользователя
    let userId = null;
    let username = "Anonymous";

    try {
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userId = tg.initDataUnsafe.user.id;
            username = tg.initDataUnsafe.user.username || `user_${userId}`;
            console.log(`✅ User ID: ${userId}, Username: ${username}`);
        } else {
            console.warn('⚠️ Нет данных пользователя. Возможно, бот не запросил user. Используем fallback.');
            // Fallback: попросим пользователя нажать кнопку, чтобы получить ID
            userId = null;
        }
    } catch(e) {
        console.error('Ошибка получения user:', e);
    }

    let score = 0;

    // Загрузка сохранённого счёта
    async function loadScore() {
        if (!userId) {
            console.warn('Нет user_id, загрузка счёта невозможна');
            return;
        }
        try {
            const response = await fetch(`/api/score?user_id=${userId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.score !== undefined) {
                    score = data.score;
                    scoreElement.innerText = score;
                    console.log(`📥 Загружен счёт: ${score}`);
                }
            } else {
                console.error('Ошибка загрузки счёта:', response.status);
            }
        } catch(e) {
            console.error('Ошибка сети при загрузке счёта:', e);
        }
    }

    // Сохранение счёта на сервере
    async function saveScore() {
        if (!userId) {
            console.warn('Нет user_id, счёт не сохранён');
            return;
        }
        try {
            const response = await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username: username, score: score })
            });
            if (response.ok) {
                console.log(`💾 Счёт ${score} сохранён`);
            } else {
                console.error('Ошибка сохранения счёта:', response.status);
            }
        } catch(e) {
            console.error('Ошибка сети при сохранении:', e);
        }
    }

    // Обновление отображения счёта
    function updateDisplay() {
        scoreElement.innerText = score;
    }

    // Вибрация
    function vibrate() {
        try {
            if (tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
                tg.HapticFeedback.impactOccurred('light');
            }
        } catch(e) {}
    }

    // Обработчик клика
    function handleClick() {
        score++;
        updateDisplay();
        vibrate();
        // Анимация
        clickableImage.style.transform = 'scale(0.95)';
        setTimeout(() => {
            clickableImage.style.transform = 'scale(1)';
        }, 100);
        // Сохраняем (можно добавить throttle, но пока просто)
        saveScore();
    }

    // Назначаем обработчик
    clickableImage.addEventListener('click', handleClick);
    clickableImage.onclick = handleClick;

    // Загружаем счёт при старте
    loadScore();
})();