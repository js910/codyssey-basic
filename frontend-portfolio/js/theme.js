// theme.js

// DOM
const themeToggle = document.querySelector(".theme-toggle");

// Browser API
const savedTheme = localStorage.getItem("theme");
const systemDarkMode = window.matchMedia("(prefers-color-scheme: dark)");

// Functions
const applyTheme = (theme) => {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    themeToggle.textContent = "☀️";
  } else {
    document.documentElement.setAttribute("data-theme", "light");
    themeToggle.textContent = "🌙";
  }
};

// Initialize
const initialTheme =
    savedTheme ||
    (systemDarkMode.matches ? "dark" : "light");

applyTheme(initialTheme);

// Events
themeToggle.addEventListener("click", () => {
  const currentTheme = document.documentElement.getAttribute("data-theme");

  const nextTheme = currentTheme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);

  localStorage.setItem("theme", nextTheme);
});
