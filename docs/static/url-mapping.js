
// URL mapping for GitHub Pages
const URL_MAPPING = {"Васильев Андрей Владимирович": "Васильев_Андрей_Владимирович", "Пригодич Никита Дмитриевич": "Пригодич_Никита_Дмитриевич", "Вычеров Дмитрий Александрович": "Вычеров_Дмитрий_Александрович", "Богомазов Николай Иванович": "Богомазов_Николай_Иванович", "Жиркова Галина Петровна": "Жиркова_Галина_Петровна", "Белоусов Александр Сергеевич": "Белоусов_Александр_Сергеевич", "Мунжукова Светлана Игоревна": "Мунжукова_Светлана_Игоревна"};

// Функция для получения правильного URL лектора
function getLecturerUrl(lecturerName) {
    const safeName = URL_MAPPING[lecturerName];
    return safeName ? `lecturers/${safeName}/` : '#';
}

// Обновляем все ссылки на лекторов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const lecturerLinks = document.querySelectorAll('a[href*="/lecturers/"]');
    lecturerLinks.forEach(link => {
        const href = link.getAttribute('href');
        const lecturerName = decodeURIComponent(href.split('/lecturers/')[1]);
        const newUrl = getLecturerUrl(lecturerName);
        if (newUrl !== '#') {
            link.setAttribute('href', newUrl);
        }
    });
});
