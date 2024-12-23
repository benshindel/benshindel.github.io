document.addEventListener("DOMContentLoaded", () => {
  // 1) Check localStorage for a saved theme
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
  }

  const modeToggle = document.getElementById("mode-toggle");
  
  if (modeToggle) {
    const icon = modeToggle.querySelector(".toggle-icon");

    // 2) Update the icon if we're already in dark mode
    if (document.body.classList.contains("dark-mode")) {
      icon.textContent = "🌙";
      modeToggle.setAttribute("aria-label", "Switch to light mode");
      icon.style.filter = "grayscale(100%)";
    } else {
      icon.textContent = "☀️";
      modeToggle.setAttribute("aria-label", "Switch to dark mode");
      icon.style.filter = "grayscale(100%)";
    }

    // 3) On click, toggle dark mode and store the preference
    modeToggle.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const isDarkMode = document.body.classList.contains("dark-mode");

      if (isDarkMode) {
        icon.textContent = "🌙";
        modeToggle.setAttribute("aria-label", "Switch to light mode");
        icon.style.filter = "grayscale(100%)";
        localStorage.setItem("theme", "dark");
      } else {
        icon.textContent = "☀️";
        modeToggle.setAttribute("aria-label", "Switch to dark mode");
        icon.style.filter = "grayscale(100%)";
        localStorage.setItem("theme", "light");
      }
    });
  }
});
