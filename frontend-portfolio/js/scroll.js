// scroll.js

// DOM
const header = document.querySelector(".header");
const scrollTopButton = document.querySelector(".scroll-top");

// Events
window.addEventListener("scroll", () => {
    const scrollPosition = window.scrollY;

    // toggle(상태전환): 있으면 제거, 없으면 추기
    header.classList.toggle("scrolled", scrollPosition >= 60);

    scrollTopButton.classList.toggle("visible", scrollPosition >= 300);
});

scrollTopButton.addEventListener("click", () => {
    window.scrollTo({
        top: 0,
        behavior: "smooth",
    });
});
