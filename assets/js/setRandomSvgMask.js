document.addEventListener('DOMContentLoaded', function() {
  // Define separate arrays of SVG file paths for left and right images
  const leftSvgFiles = [
    '/assets/images/svg/snail2.svg',
    '/assets/images/svg/snail1.svg',
    '/assets/images/svg/okapi1.svg',
    '/assets/images/svg/lizard2.svg',
    '/assets/images/svg/caterpillar1.svg',
    '/assets/images/svg/caterpillar2.svg',
    '/assets/images/svg/toad1.svg'
  ];

  const rightSvgFiles = [
    '/assets/images/svg/crow1.svg',
    '/assets/images/svg/crow2.svg',
    '/assets/images/svg/pigeon1.svg',
    '/assets/images/svg/lizard1.svg',
    '/assets/images/svg/lizard3.svg',
    '/assets/images/svg/crab1.svg',
    '/assets/images/svg/crab2.svg'    
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
