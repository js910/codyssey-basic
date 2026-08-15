// navigation.js

// DOM
const menuToggle = document.querySelector(".menu-toggle");
const navMenu = document.querySelector(".nav-menu");

// Functions
const closeMenu = () => {
    navMenu.classList.remove("active");
    menuToggle.setAttribute("aria-expanded", "false");
};

// Events

// 메뉴 토글 버튼: 메뉴 열기/닫기
menuToggle.addEventListener("click", (event) => {
    event.stopPropagation();    // 버블링 차단

    const isOpen = navMenu.classList.toggle("active");
    menuToggle.setAttribute("aria-expanded", isOpen);
});

// 메뉴 링크: 메뉴 닫기 (이벤트 위임)
navMenu.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
    closeMenu();
    }
});

// 메뉴 바깥: 메뉴 닫기
document.addEventListener("click", (event) => {
  if (!navMenu.contains(event.target)) {
    closeMenu();
  }
});

// 스크롤: 메뉴 닫기
window.addEventListener("scroll", closeMenu);
