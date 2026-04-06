// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const scoreElement = document.getElementById('score');
const clickableImage = document.getElementById('clickableImage');

let score = 0;

function updateScore() {
    scoreElement.innerText = score;
}

function vibrate() {
    try {
        if (tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch(e) { console.log(e); }
}

function onClick() {
    score++;
    updateScore();
    vibrate();
    // Анимация
    clickableImage.style.transform = 'scale(0.95)';
    setTimeout(() => {
        clickableImage.style.transform = 'scale(1)';
    }, 100);
}

clickableImage.addEventListener('click', onClick);