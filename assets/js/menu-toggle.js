// menu-toggle.js (revised for single-nav approach)
document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const mainNav = document.getElementById("main-nav");

  if (menuToggle && mainNav) {
    menuToggle.addEventListener("click", () => {
      const isActive = mainNav.classList.contains("active");

      // Toggle the .active class
      mainNav.classList.toggle("active");

      // Update aria-expanded for accessibility
      menuToggle.setAttribute("aria-expanded", !isActive);
    });
  }
});
