document.addEventListener('DOMContentLoaded', function() {
  // Footer animals (PNG masks in /assets/images/sprites/, made from the original SVG engravings)
  const leftSvgFiles = [
    'snail2',
    'snail1',
    'okapi1',
    'lizard2',
    'caterpillar1',
    'caterpillar2',
    'toad1',
    'shrew1'
  ];

  const rightSvgFiles = [
    'crow1',
    'crow2',
    'pigeon1',
    'lizard1',
    'lizard3',
    'crab1',
    'crab2',
    'mole1'    
  ];
  
  /**
   * Picks a random footer animal and hands the container two masks:
   * --ink-mask (the engraved lines, used in light mode) and
   * --paper-mask (the animal's silhouette minus the lines, used in dark mode,
   * so the engraving reads as a positive print instead of a photo negative).
   */
  function setRandomSvgMask(containerId, names) {
    const container = document.getElementById(containerId);
    if (!container || !names || names.length === 0) return;
    const name = names[Math.floor(Math.random() * names.length)];
    container.style.setProperty('--ink-mask', `url('/assets/images/sprites/${name}-ink.png')`);
    container.style.setProperty('--paper-mask', `url('/assets/images/sprites/${name}-paper.png')`);
  }

  // Set a random SVG for the left container from the leftSvgFiles array
  setRandomSvgMask('left-footer-svg-container', leftSvgFiles);

  // Set a random SVG for the right container from the rightSvgFiles array
  setRandomSvgMask('right-footer-svg-container', rightSvgFiles);
});
