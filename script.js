const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const scoreElement = document.getElementById('score');
const clickableImage = document.getElementById('clickableImage');

let score = 0;
let userId = tg.initDataUnsafe?.user?.id; // получаем ID пользователя Telegram

if (!userId) {
    console.warn("No user id, using fallback");
    userId = 0;
}

// Загружаем сохранённый счёт с сервера
async function loadScore() {
    try {
        const response = await fetch(`/get_score?user_id=${userId}`);
        if (response.ok) {
            const data = await response.json();
            score = data.score || 0;
            scoreElement.innerText = score;
        }
    } catch(e) {
        console.error("Failed to load score:", e);
    }
}

// Отправляем обновлённый счёт на сервер
async function saveScore(newScore) {
    try {
        await fetch('/update_score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, score: newScore })
        });
    } catch(e) {
        console.error("Failed to save score:", e);
    }
}

function vibrate() {
    try {
        if (tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
            tg.HapticFeedback.impactOccurred('light');
        }
    } catch(e) {}
}

async function onClick() {
    score++;
    scoreElement.innerText = score;
    vibrate();
    // Анимация
    clickableImage.style.transform = 'scale(0.95)';
    setTimeout(() => { clickableImage.style.transform = 'scale(1)'; }, 100);
    // Сохраняем на сервере (не ждём ответа, чтобы не тормозить интерфейс)
    saveScore(score);
}

clickableImage.addEventListener('click', onClick);
// Загружаем счёт при старте
loadScore();