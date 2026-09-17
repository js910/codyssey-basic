// form.js

// DOM
const contactForm = document.querySelector("#contact-form");

const nameInput = document.querySelector("#name");
const emailInput = document.querySelector("#email");
const messageInput = document.querySelector("#message");

const nameError = document.querySelector("#name-error");
const emailError = document.querySelector("#email-error");
const messageError = document.querySelector("#message-error");

const formSuccess = document.querySelector("#form-success");

// Formspree endpoint
const FORMSPREE_URL = "https://formspree.io/f/xjybebko";

// Validation
const validateEmail = (email) => {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailPattern.test(email);
};

const clearErrors = () => {
    nameError.textContent = "";
    emailError.textContent = "";
    messageError.textContent = "";
};

const validateForm = () => {
    let isValid = true;

    clearErrors();
    formSuccess.textContent = "";

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const message = messageInput.value.trim();

    if (name === "") {
        nameError.textContent = "이름을 입력해주세요.";
        isValid = false;
    }

    if (email === "") {
        emailError.textContent = "이메일을 입력해주세요.";
        isValid = false;
    } else if (!validateEmail(email)) {
        emailError.textContent = "올바른 이메일 형식을 입력해주세요.";
        isValid = false;
    }

    if (message === "") {
        messageError.textContent = "메시지를 입력해주세요.";
        isValid = false;
    }

    return isValid;
};

// Form Submit
contactForm.addEventListener("submit", async (event) => {
    // 페이지 이동 방지
    event.preventDefault();

    if (!validateForm()) return;

    const response = await fetch("https://formspree.io/f/xjybebko", {
        method: "POST",                     // HTTP 요청 방식, 서버에 데이터를 전달할 때 사용
        body: new FormData(contactForm),    // 전송 데이터
        headers: { Accept: "application/json" } // 요청 응답 형식
    });

    if (response.ok) {
        formSuccess.textContent = "문의가 성공적으로 접수되었습니다.";
        contactForm.reset();
    } else {
        formSuccess.textContent = "전송에 실패했습니다. 다시 시도해주세요.";
    }
});

// Input Event
[nameInput, emailInput, messageInput].forEach((input) => {
    input.addEventListener("input", () => {
        formSuccess.textContent = "";
    });
});
