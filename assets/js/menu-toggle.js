document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const mobileMenu = document.getElementById("mobile-menu");

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
      mobileMenu.classList.toggle("active");
    });
  }
  const modeToggleDesktop = document.getElementById("mode-toggle");
  const modeToggleMobile = document.getElementById("mode-toggle-mobile");

  const toggleDarkMode = () => {
    document.body.classList.toggle("dark-mode");
  };

  if (modeToggleDesktop) {
    modeToggleDesktop.addEventListener("click", toggleDarkMode);
  }

  if (modeToggleMobile) {
    modeToggleMobile.addEventListener("click", toggleDarkMode);
  }
});
