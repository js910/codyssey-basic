/* ================================
DOM Elements
================================ */

const userName = "송지윤";

const menuToggle = document.querySelector(".menu-toggle");
const navMenu = document.querySelector(".nav-menu");
const themeToggle = document.querySelector(".theme-toggle");

const heroName = document.querySelector("#hero-name");
const footerName = document.querySelector("#footer-name");

const header = document.querySelector(".header");
const scrollTopButton = document.querySelector(".scroll-top");

const contactForm = document.querySelector("#contact-form");

const nameInput = document.querySelector("#name");
const emailInput = document.querySelector("#email");
const messageInput = document.querySelector("#message");

const nameError = document.querySelector("#name-error");
const emailError = document.querySelector("#email-error");
const messageError = document.querySelector("#message-error");

const formSuccess = document.querySelector("#form-success");

const projectStatus = document.querySelector(".project-status");
const projectList = document.querySelector(".project-list");

const githubUsername = "js910";

heroName.textContent = userName;
footerName.textContent = userName;

/* ================================
Mobile Menu
================================ */

menuToggle.addEventListener("click", () => {
navMenu.classList.toggle("active");

const isOpen = navMenu.classList.contains("active");

menuToggle.setAttribute("aria-expanded", isOpen);
});

/* 메뉴 클릭 시 모바일 메뉴 닫기 */

const navLinks = document.querySelectorAll(".nav-menu a");

navLinks.forEach((link) => {
link.addEventListener("click", () => {
navMenu.classList.remove("active");
menuToggle.setAttribute("aria-expanded", "false");
});
});

/* ================================
Dark Mode
================================ */

const savedTheme = localStorage.getItem("theme");

if (savedTheme === "dark") {
document.documentElement.setAttribute("data-theme", "dark");
themeToggle.textContent = "☀️";
}

themeToggle.addEventListener("click", () => {
const currentTheme =
document.documentElement.getAttribute("data-theme");

const isDark = currentTheme === "dark";

if (isDark) {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("theme", "light");
    themeToggle.textContent = "🌙";
} else {
    document.documentElement.setAttribute("data-theme", "dark");
    localStorage.setItem("theme", "dark");
    themeToggle.textContent = "☀️";
}
});

/* ================================
Scroll
================================ */

window.addEventListener("scroll", () => {
const scrollPosition = window.scrollY;

/* 60px 이상 스크롤하면 Header 스타일 변경 */
if (scrollPosition >= 60) {
    header.classList.add("scrolled");
} else {
    header.classList.remove("scrolled");
}

/* 300px 이상 스크롤하면 Top 버튼 표시 */
if (scrollPosition >= 300) {
    scrollTopButton.classList.add("visible");
} else {
    scrollTopButton.classList.remove("visible");
}
});

/* ================================
Scroll To Top
================================ */

scrollTopButton.addEventListener("click", () => {
window.scrollTo({
top: 0,
behavior: "smooth"
});
});

/* ================================
Contact Form Validation
================================ */

const validateEmail = (email) => {
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

return emailPattern.test(email);
};

const clearErrors = () => {
nameError.textContent = "";
emailError.textContent = "";
messageError.textContent = "";
formSuccess.textContent = "";
};

const validateForm = () => {
let isValid = true;

clearErrors();

const name = nameInput.value.trim();
const email = emailInput.value.trim();
const message = messageInput.value.trim();

/* 이름 검사 */

if (name === "") {
    nameError.textContent = "이름을 입력해주세요.";
    isValid = false;
}


/* 이메일 검사 */

if (email === "") {
    emailError.textContent = "이메일을 입력해주세요.";
    isValid = false;
} else if (!validateEmail(email)) {
    emailError.textContent =
        "올바른 이메일 형식을 입력해주세요.";
    isValid = false;
}


/* 메시지 검사 */

if (message === "") {
    messageError.textContent = "메시지를 입력해주세요.";
    isValid = false;
}

return isValid;
};

contactForm.addEventListener("submit", (event) => {
event.preventDefault();

const isValid = validateForm();

if (!isValid) {
    return;
}

formSuccess.textContent =
    "문의가 성공적으로 접수되었습니다.";

contactForm.reset();
});

/* ================================
Input Event
================================ */

const formInputs = [
nameInput,
emailInput,
messageInput
];

formInputs.forEach((input) => {
input.addEventListener("input", () => {
formSuccess.textContent = "";
});
});

/* ================================
Scroll Animation
================================ */

const animatedElements =
document.querySelectorAll("section");

const observer = new IntersectionObserver(
(entries) => {
entries.forEach((entry) => {

        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
        }

    });
},
{
    threshold: 0.2
}
);

animatedElements.forEach((element) => {
element.classList.add("animate-on-scroll");
observer.observe(element);
});

/* ================================
GitHub API
================================ */

const renderLoading = () => {
projectStatus.textContent = "프로젝트를 불러오는 중...";
projectList.innerHTML = "";
};

const renderEmpty = () => {
projectStatus.textContent = "표시할 프로젝트가 없습니다.";

projectList.innerHTML = "";
};

const renderError = () => {
projectStatus.innerHTML = `
    <p>프로젝트를 불러올 수 없습니다.</p>
    <button type="button" class="btn retry-button">
        다시 시도
    </button>
`;

projectList.innerHTML = "";

const retryButton =
    projectStatus.querySelector(".retry-button");

retryButton.addEventListener("click", fetchProjects);
};

const renderProjects = (projects) => {
projectStatus.textContent = "";

projectList.innerHTML = projects
    .map((project) => {

        const {
            name,
            description,
            html_url,
            stargazers_count,
            language
        } = project;

        return `
            <article class="project-card">

                <h3>${name}</h3>

                <p>
                    ${description || "프로젝트 설명이 없습니다."}
                </p>

                <div class="project-info">
                    <span>
                        ⭐ ${stargazers_count}
                    </span>

                    <span>
                        ${language || "언어 정보 없음"}
                    </span>
                </div>

                <a
                    href="${html_url}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="project-link"
                >
                    GitHub에서 보기 →
                </a>

            </article>
        `;
    })
    .join("");
};

async function fetchProjects() {

renderLoading();

try {

    const response = await fetch(
        `https://api.github.com/users/${githubUsername}/repos`
    );


    if (!response.ok) {
        throw new Error(
            `GitHub API Error: ${response.status}`
        );
    }


    const projects = await response.json();


    /* fork가 아닌 본인 프로젝트만 표시 */
    const filteredProjects = projects.filter(
        (project) => !project.fork
    );


    if (filteredProjects.length === 0) {
        renderEmpty();
        return;
    }


    renderProjects(filteredProjects);

} catch (error) {

    console.error(error);

    renderError();
}
}

/* ================================
Initial API Call
================================ */

fetchProjects();
