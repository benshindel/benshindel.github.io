// Toggle Mobile Menu
document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menu-toggle");
  const mobileMenu = document.getElementById("mobile-menu");

  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener("click", () => {
      const isHidden = mobileMenu.classList.contains("hidden");

      // Toggle visibility
      mobileMenu.classList.toggle("hidden");
      mobileMenu.classList.toggle("active");

      // Update aria-expanded for accessibility
      menuToggle.setAttribute("aria-expanded", !isHidden);
    });
  }
});
