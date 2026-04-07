(function() {
    // Инициализация Telegram WebApp
    const tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();

    // Получаем элементы
    const scoreElement = document.getElementById('score');
    const clickableImage = document.getElementById('clickableImage');

    // Проверяем, что элементы существуют
    if (!scoreElement) {
        console.error('Ошибка: элемент #score не найден');
        return;
    }
    if (!clickableImage) {
        console.error('Ошибка: элемент #clickableImage не найден');
        return;
    }

    let score = 0;

    // Функция обновления счёта на экране
    function updateScore() {
        scoreElement.innerText = score;
    }

    // Функция вибрации (если поддерживается)
    function vibrate() {
        try {
            if (tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
                tg.HapticFeedback.impactOccurred('light');
            }
        } catch(e) {
            // Игнорируем ошибки вибрации
        }
    }

    // Обработчик клика
    function handleClick() {
        score++;
        updateScore();
        vibrate();
        // Анимация нажатия
        clickableImage.style.transform = 'scale(0.95)';
        setTimeout(() => {
            clickableImage.style.transform = 'scale(1)';
        }, 100);
    }

    // Назначаем обработчик
    clickableImage.addEventListener('click', handleClick);
    // Резервный вариант для старых браузеров
    clickableImage.onclick = handleClick;
})();