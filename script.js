// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// DOM элементы
const scoreElement = document.getElementById('score');
const clickableImage = document.getElementById('clickableImage');

let score = 0;

function updateScoreDisplay() {
    scoreElement.innerText = score;
    // Отправляем счёт боту (можно использовать для сохранения в БД)
    tg.sendData(JSON.stringify({ score: score }));
}

function triggerVibration() {
    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('light');
    }
}

function handleClick() {
    score++;
    updateScoreDisplay();
    triggerVibration();
    
    // Анимация нажатия
    clickableImage.style.transform = 'scale(0.9)';
    setTimeout(() => {
        clickableImage.style.transform = 'scale(1)';
    }, 100);
}

clickableImage.addEventListener('click', handleClick);