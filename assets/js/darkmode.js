// darkmode.js
document.addEventListener("DOMContentLoaded", () => {
  const modeToggle = document.getElementById("mode-toggle");

  if (modeToggle) {
    modeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const icon = modeToggle.querySelector(".toggle-icon");
      if (document.body.classList.contains("dark-mode")) {
        icon.textContent = "🌙"; // Moon icon for dark mode
        modeToggle.setAttribute("aria-label", "Switch to light mode");
      } else {
        icon.textContent = "☀️"; // Sun icon for light mode
        modeToggle.setAttribute("aria-label", "Switch to dark mode");
      }
    });
  }
});
