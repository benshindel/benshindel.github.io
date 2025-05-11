document.addEventListener('DOMContentLoaded', function() {
  // Define separate arrays of SVG file paths for left and right images
  const leftSvgFiles = [
    '/assets/images/svg/crow2.svg',
    '/assets/images/svg/crow1.svg'
    // Add more paths for the left side
  ];

  const rightSvgFiles = [
    '/assets/images/svg/snail2',
    '/assets/images/svg/snail1'
    // Add more paths for the right side
  ];

  /**
   * Sets a random SVG mask on a given container element from a provided array of SVG paths.
   * @param {string} containerId - The ID of the HTML element to apply the mask to.
   * @param {string[]} svgFileArray - The array of SVG file paths to choose from.
   */
  function setRandomSvgMask(containerId, svgFileArray) {
    const container = document.getElementById(containerId);
    if (container && svgFileArray && svgFileArray.length > 0) {
      const randomSvgPath = svgFileArray[Math.floor(Math.random() * svgFileArray.length)];
      // Apply the selected SVG as a mask-image
      // Using `-webkit-mask-image` for broader browser compatibility (Safari)
      container.style.webkitMaskImage = `url('${randomSvgPath}')`;
      container.style.maskImage = `url('${randomSvgPath}')`;
    } else if (container) {
      console.warn(`SVG file array for container '${containerId}' is empty or not provided.`);
    } else {
      console.warn(`Container with ID '${containerId}' not found.`);
    }
  }

  // Set a random SVG for the left container from the leftSvgFiles array
  setRandomSvgMask('left-footer-svg-container', leftSvgFiles);

  // Set a random SVG for the right container from the rightSvgFiles array
  setRandomSvgMask('right-footer-svg-container', rightSvgFiles);
});
