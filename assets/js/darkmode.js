document.addEventListener("DOMContentLoaded", () => {
  // 1) Check localStorage for a saved theme
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
  }

  const modeToggle = document.getElementById("mode-toggle");

  if (modeToggle) {
    // The .toggle-icon span's appearance is now controlled by CSS.
    // We only need to set the button's ARIA label.

    // 2) Update the ARIA label based on the initial theme
    if (document.body.classList.contains("dark-mode")) {
      modeToggle.setAttribute("aria-label", "Switch to light mode");
    } else {
      modeToggle.setAttribute("aria-label", "Switch to dark mode");
    }

    // 3) On click, toggle dark mode, update ARIA label, and store the preference
    modeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const isDarkMode = document.body.classList.contains("dark-mode");

      if (isDarkMode) {
        modeToggle.setAttribute("aria-label", "Switch to light mode");
        localStorage.setItem("theme", "dark");
      } else {
        modeToggle.setAttribute("aria-label", "Switch to dark mode");
        localStorage.setItem("theme", "light");
      }
    });
  }
});
