// scroll.js

// DOM
const header = document.querySelector(".header");
const scrollTopButton = document.querySelector(".scroll-top");

// 브라우저의 자동 스크롤 복원 기능 끄기
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}

// 스크롤 이벤트
window.addEventListener("scroll", () => {
    const scrollPosition = window.scrollY;

    // toggle(상태전환): 있으면 제거, 없으면 추가
    header.classList.toggle("scrolled", scrollPosition >= 60);

    scrollTopButton.classList.toggle("visible", scrollPosition >= 300);
});

// Top 스크롤
scrollTopButton.addEventListener("click", () => {
    window.scrollTo({
        top: 0,
    });
});

// Hash 스크롤
const scrollToHash = () => {
    if (!location.hash) return;
    const target = document.querySelector(location.hash);
    if (target) {
        target.scrollIntoView({
            block: "start",
        });
    }
};

// 해시 스크롤이 한번만 실행되도록 함
let hasScrolled = false;

const handleScrollToHash = () => {
    if (!hasScrolled) {
        scrollToHash();
        hasScrolled = true;
    }
};

// 1. 프로젝트 렌더링이 완료되면 실행
window.addEventListener("projects-rendered", handleScrollToHash);

// 2. 프로젝트 데이터가 없는 경우 : 1.5초 후 강제 실행
window.addEventListener("load", () => {
    setTimeout(handleScrollToHash, 1500); 
});
