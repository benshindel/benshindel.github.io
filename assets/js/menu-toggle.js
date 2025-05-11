// menu-toggle.js (revised for single-nav approach and click-outside-to-close)
document.addEventListener("DOMContentLoaded", () => {
  const menuHamburgerButton = document.getElementById("menu-toggle"); // Your hamburger button
  const mainNav = document.getElementById("main-nav"); // Your navigation menu

  if (menuHamburgerButton && mainNav) {
    menuHamburgerButton.addEventListener("click", function() {
      const wasActive = mainNav.classList.contains("active"); // Check state BEFORE toggle

      // Toggle the .active class on the navigation menu
      mainNav.classList.toggle("active");

      // Update aria-expanded for accessibility
      menuHamburgerButton.setAttribute("aria-expanded", !wasActive); // Sets to the new state

      if (!wasActive) { // Menu has just been opened
        // Add event listeners for clicks/touches outside.
        // Use a brief timeout to ensure these listeners are added after the current click event cycle,
        // preventing the menu from closing immediately due to the same click that opened it.
        setTimeout(() => {
          document.addEventListener('click', handleClickOutsideNavMenu);
          document.addEventListener('touchstart', handleClickOutsideNavMenu);
        }, 0);
      } else { // Menu has just been closed (by clicking the button)
        // Remove event listeners
        document.removeEventListener('click', handleClickOutsideNavMenu);
        document.removeEventListener('touchstart', handleClickOutsideNavMenu);
      }
    });
  }

  function handleClickOutsideNavMenu(event) {
    // If the mainNav element isn't in the DOM or isn't active,
    // clear listeners and do nothing (safety check).
    if (!mainNav || !mainNav.classList.contains('active')) {
      document.removeEventListener('click', handleClickOutsideNavMenu);
      document.removeEventListener('touchstart', handleClickOutsideNavMenu);
      return;
    }

    // Check if the click was on the hamburger button itself or inside the main navigation menu.
    // If it was, don't close the menu.
    if ((menuHamburgerButton && menuHamburgerButton.contains(event.target)) || mainNav.contains(event.target)) {
      return;
    }

    // If the click was outside both the button and the menu, close the menu.
    mainNav.classList.remove('active');
    menuHamburgerButton.setAttribute("aria-expanded", "false"); // Update ARIA

    // Clean up: remove the event listeners from the document.
    document.removeEventListener('click', handleClickOutsideNavMenu);
    document.removeEventListener('touchstart', handleClickOutsideNavMenu);
  }
});
