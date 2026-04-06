// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;

// Расширяем на весь экран
tg.expand();

// Показываем, что приложение готово
tg.ready();

// Получаем элементы
const scoreElement = document.getElementById('score');
const clickableImage = document.getElementById('clickableImage');

// Проверяем, что элементы найдены
if (!scoreElement) console.error('score element not found');
if (!clickableImage) console.error('clickableImage element not found');

let score = 0;

// Функция обновления счёта
function updateScore() {
    scoreElement.innerText = score;
    // Отправляем счёт боту (опционально, можно закомментировать если вылетает)
    try {
        tg.sendData(JSON.stringify({ score: score }));
    } catch(e) {
        console.log('sendData error:', e);
    }
}

// Функция вибрации (только если поддерживается)
function vibrate() {
    try {
        if (tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch(e) {
        console.log('vibration error:', e);
    }
}

// Обработчик клика
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

// Назначаем обработчик
clickableImage.addEventListener('click', onClick);

// Альтернативный способ на случай, если addEventListener не сработает
clickableImage.onclick = onClick;