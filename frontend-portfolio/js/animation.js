// animation.js

// DOM
const heroDescription = document.querySelector(".hero-description");
const animatedElements = document.querySelectorAll("section");

// Typing Effect
const typingText =
    "백엔드 개발자를 꿈꾸며 웹 서비스와 데이터 기술을 공부하고 있습니다.";
let typingIndex = 0;
heroDescription.textContent = "";

const typeText = () => {
    if (typingIndex < typingText.length) {
        heroDescription.textContent += typingText.charAt(typingIndex);
        typingIndex++;
        setTimeout(typeText, 50);   // 50ms 후 자기 자신을 다시 호출
    }
};

typeText();

// IntersectionObserver (교차상태 감시자)
// 요소가 화면에 들어왔는지 감지하고 callback을 실행
const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
            }
        });
    },
    {
        threshold: 0.2  // options
    }
);

// Observer 등록
animatedElements.forEach((element) => {
    element.classList.add("animate-on-scroll");
    observer.observe(element);
});
