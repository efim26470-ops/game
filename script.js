(function() {
    // Инициализация Telegram Web App
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();

    // DOM элементы
    const scoreElement = document.getElementById('score');
    const clickableImage = document.getElementById('clickableImage');
    const topListElement = document.getElementById('top-list'); // предположим, что есть элемент для списка топов

    if (!scoreElement || !clickableImage) {
        console.error('Elements not found: score or clickableImage');
        return;
    }

    // Получаем данные пользователя из Telegram
    let userId = null;
    let username = "Anonymous";
    try {
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userId = tg.initDataUnsafe.user.id;
            username = tg.initDataUnsafe.user.username || `user_${userId}`;
            console.log('User ID:', userId);
        } else {
            console.warn('No user data, game may work in demo mode');
        }
    } catch(e) {
        console.error('Error getting user:', e);
    }

    let score = 0;

    // Загрузка текущего счёта с сервера
    async function loadScore() {
        if (!userId) {
            console.warn('No userId, cannot load score');
            return;
        }
        try {
            const res = await fetch(`/api/score?user_id=${userId}`);
            if (res.ok) {
                const data = await res.json();
                score = data.score || 0;
                scoreElement.innerText = score;
                console.log('Loaded score:', score);
            } else {
                console.error('Failed to load score:', res.status);
            }
        } catch(e) {
            console.error('Load score error:', e);
        }
    }

    // Сохранение счёта на сервере (при клике)
    async function saveScore() {
        if (!userId) {
            console.warn('No userId, cannot save score');
            return;
        }
        try {
            const res = await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId, username, score: score })
            });
            if (res.ok) {
                console.log('Score saved:', score);
            } else {
                console.error('Failed to save score:', res.status);
            }
        } catch(e) {
            console.error('Save score error:', e);
        }
    }

    // Загрузка и отображение топа
    async function loadTop() {
        try {
            const res = await fetch('/api/top');
            if (res.ok) {
                const top = await res.json();
                console.log('Top data:', top);
                displayTop(top);
            } else {
                console.error('Failed to load top:', res.status);
            }
        } catch(e) {
            console.error('Load top error:', e);
        }
    }

    // Отображение топа в интерфейсе
    function displayTop(players) {
        if (!topListElement) {
            console.warn('No top-list element found');
            return;
        }
        if (!players || players.length === 0) {
            topListElement.innerHTML = '<li>Нет игроков</li>';
            return;
        }
        const html = players.map((p, idx) => {
            const name = p.first_name || p.username || 'Anonymous';
            return `<li>${idx+1}. ${name} — ${p.score} очков</li>`;
        }).join('');
        topListElement.innerHTML = html;
    }

    // Обработчик клика по картинке
    function handleClick() {
        score++;
        scoreElement.innerText = score;
        // Анимация
        clickableImage.style.transform = 'scale(0.95)';
        setTimeout(() => clickableImage.style.transform = 'scale(1)', 100);
        // Вибрация (если поддерживается)
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
        // Сохраняем счёт на сервере
        saveScore();
    }

    // Привязываем событие клика
    clickableImage.addEventListener('click', handleClick);

    // Загружаем данные при старте
    loadScore();
    loadTop();
})();