// overlay-toggle.js

document.addEventListener("DOMContentLoaded", () => {
  const imageLinks = document.querySelectorAll('.image-grid a');

  imageLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      // Detect if the device is touch-capable
      const isTouchDevice = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;

      if (isTouchDevice) {
        // If the link is not already active, prevent navigation and toggle active state
        if (!link.classList.contains('active')) {
          e.preventDefault(); // Prevent navigation

          // Remove 'active' from all other links
          imageLinks.forEach(l => {
            if (l !== link) l.classList.remove('active');
          });

          // Toggle 'active' on the clicked link
          link.classList.toggle('active');

          // Update ARIA attribute for accessibility
          const isActive = link.classList.contains('active');
          link.setAttribute('aria-expanded', isActive);
        }
        // If already active, allow navigation
      }
    });
  });

  // Optional: Remove 'active' when clicking outside the image-links
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.image-grid a')) {
      imageLinks.forEach(l => l.classList.remove('active'));
    }
  });
});
