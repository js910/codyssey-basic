
# [Troubleshooting] 앵커(Hash) 위치에서 새로고침 시 스크롤 문제

## 1. 문제 상황
웹페이지의 특정 섹션 해시(`/#section`)가 포함된 상태에서 새로고침 시, 스크롤 위치가 원하는 영역에 고정되지 않고 어긋나는 현상 발생.
* 스크롤이 고정되지 않고 조금씩 위로 올라감.
* 새로고침이 완료되기 전 다시 새로고침 시 스크롤 고정이 풀림.

## 2. 원인 분석
비동기 데이터 로딩과 렌더링 타이밍으로 인한 **레이아웃 변동(Layout Shift)** 이 원인이었음.
1. **레이아웃 크기 변동:** 초기 로드 시점과 JavaScript로 동적 데이터(타이핑 효과, 프로젝트 리스트 등)가 렌더링된 이후의 높이 값이 달라 브라우저가 계산한 스크롤 위치가 어긋남.
2. **타이밍 문제:** DOM이 완전히 그려지기 전 브라우저의 기본 해시 이동 처리가 우선시되면서 스크롤 시점이 엇갈림.

## 3. 해결 방법
### ① 타이핑 영역 레이아웃 안정화 (CSS)
타이핑 효과로 인해 텍스트가 채워지기 전후로 높이가 변하는 것을 방지하기 위해 `min-height`를 적용하여 레이아웃 고정.
```css
.hero-description {
    min-height: 3.2em;
    /* 기타 스타일... */
}
```

### ② 커스텀 해시 스크롤 제어 (JavaScript)
브라우저의 기본 동작에 의존하지 않고, 데이터 렌더링 완료 시점을 감지하여 이동하도록 구현.
```JavaScript
// 해시 위치로 스크롤 함수
const scrollToHash = () => {
    if (!location.hash) return;
    const target = document.querySelector(location.hash);
    if (target) {
        target.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });
    }
};

// 중복 실행 방지 플래그
let hasScrolled = false;

const handleScrollToHash = () => {
    if (!hasScrolled) {
        scrollToHash();
        hasScrolled = true;
    }
};

// 프로젝트 데이터 렌더링 완료 시 커스텀 이벤트 호출
window.addEventListener("projects-rendered", handleScrollToHash);

// 안전장치 (데이터 렌더링 지연 대비, 1.5초 후 강제 실행)
window.addEventListener("load", () => {
    setTimeout(handleScrollToHash, 1500); 
});
```

## 4. 배운 점
* 비동기 렌더링의 주의점: 비동기 데이터를 불러오는 환경에서는 브라우저의 기본 기능(Hash Scroll)이 의도대로 동작하지 않을 수 있다는 것을 인지함.
* 사용자 경험(UX) 최적화: 단순히 기능을 구현하는 것을 넘어, 레이아웃이 완성되는 시점을 명시적으로 제어하는 것이 사용자 경험 측면에서 중요함을 배움.
