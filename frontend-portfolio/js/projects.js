// projects.js

// DOM
const projectStatus = document.querySelector(".project-status");
const projectList = document.querySelector(".project-list");

const githubUsername = "js910";

// State
// React의 state처럼 프로젝트 데이터와 현재 화면 상태를 한 곳에서 관리
const state = {
    projects: [],
    currentLanguage: "all",
    status: "idle",
    error: "",
};


// Filter
const createFilterButtons = (projects) => {
    const existingFilter = document.querySelector(".project-filter");

    if (existingFilter) {
        existingFilter.remove();
    }

    // 프로젝트에서 사용된 언어 추출 및 중복 제거
    const languages = [
        ...new Set(
            projects
                .map((project) => project.language)
                .filter((language) => language),
        ),
    ];

    const projectFilter = document.createElement("div");

    projectFilter.className = "project-filter";

    const allButton = document.createElement("button");

    allButton.type = "button";
    allButton.className = "filter-button active";
    allButton.textContent = "전체";

    projectFilter.appendChild(allButton);

    // 언어별 필터 버튼 생성
    languages.forEach((language) => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "filter-button";
        button.textContent = language;
        button.dataset.language = language;

        projectFilter.appendChild(button);
    });

    projectStatus.after(projectFilter);

    // 필터 버튼 클릭 이벤트
    const filterButtons = projectFilter.querySelectorAll(".filter-button");

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            filterButtons.forEach((item) => {
                item.classList.remove("active");
            });

            button.classList.add("active");

            // 선택한 언어를 State에 저장하고 화면 갱신
            state.currentLanguage = button.dataset.language || "all";
            renderFilteredProjects();
        });
    });
};


// Render
const renderFilteredProjects = () => {
    // 현재 선택된 언어에 따라 프로젝트 필터링
    const filteredProjects =
        state.currentLanguage === "all"
            ? state.projects
            : state.projects.filter(
                  (project) => project.language === state.currentLanguage,
              );

    if (filteredProjects.length === 0) {
        projectList.innerHTML = "<p>해당 언어의 프로젝트가 없습니다.</p>";
        return;
    }

    // 성공 상태로 변경한 뒤 화면 렌더링
    state.status = "success";
    renderProjects(filteredProjects);
};

const renderLoading = () => {
    state.status = "loading";
    state.error = "";
    projectStatus.textContent = "프로젝트를 불러오는 중...";
    projectList.innerHTML = "";
};

const renderEmpty = () => {
    state.status = "empty";
    projectStatus.textContent = "표시할 프로젝트가 없습니다.";
    projectList.innerHTML = "";
};

const renderError = (message) => {
    state.status = "error";
    state.error = message;

    projectStatus.innerHTML = `
        <p>${message}</p>
        <button
            type="button"
            class="btn retry-button"
        >
            다시 시도
        </button>
    `;

    projectList.innerHTML = "";

    // 다시 시도 시 API 재요청
    const retryButton = projectStatus.querySelector(".retry-button");
    retryButton.addEventListener("click", fetchProjects);
};

const renderProjects = (projects) => {
    projectStatus.textContent = "";

    projectList.innerHTML = projects
        .map((project) => {
            const { name, description, html_url, stargazers_count, language } =
                project;

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

    // 렌더링 완료 이벤트 지정
    const event = new CustomEvent("projects-rendered");
    window.dispatchEvent(event);
};


// Github API
async function fetchProjects() {
    renderLoading();

    try {
        const response = await fetch(
            `https://api.github.com/users/${githubUsername}/repos`,
        );

        if (response.status === 403) {
            throw new Error(
                "GitHub API 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.",
            );
        }

        if (!response.ok) {
            throw new Error(`GitHub API Error: ${response.status}`);
        }

        const projects = await response.json();

        // Fork 프로젝트 제외
        const filteredProjects = projects.filter((project) => !project.fork);

        if (filteredProjects.length === 0) {
            state.projects = [];
            renderEmpty();
            return;
        }

        // API 데이터를 State에 저장 후 렌더링
        state.projects = filteredProjects;
        state.currentLanguage = "all";

        createFilterButtons(state.projects);
        renderFilteredProjects();
    } catch (error) {
        console.error(error);
        renderError(error.message);
    }
}


// Initial API Call
fetchProjects();
