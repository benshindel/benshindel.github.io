---
layout: default
title: Boggle Game
permalink: /boggle/
---

<!-- Include Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Caudex&display=swap" rel="stylesheet">

<!-- Boggle Game Container -->
<div class="boggle-container">
  <div id="container">
    <div id="boggle-board"></div> <!-- Placeholder for the 4x4 Boggle board -->

    <div class="top-row">
      <button onclick="generateBoggleBoard()">New<br>Board</button> <!-- Generates a new board -->
      <button onclick="toggleOrientation()" id="orientation-button">Table<br>Mode</button> <!-- Toggles tile orientation -->
      <button id="validate-button" onclick="validateWord()">Validate</button> <!-- Validates the selected word -->
    </div>

    <div class="bottom-row">
      <button onclick="startPauseTimer()">Start/<br>Pause</button> <!-- Start or pause the timer -->
      <button onclick="resetAndIncrementTimer()">Reset /<br>Increment</button> <!-- Resets and increments the timer -->
      <div id="timer">2:00</div> <!-- Displays the remaining time -->
    </div>
    
    <!-- Message Display Area -->
    <div id="message"></div>
  </div>
</div>

<!-- Inline CSS for Boggle Widget -->
<style>
  /* Center the entire game interface within the browser window */
  body {
    display: flex;
    justify-content: center; /* Horizontally center the container */
    align-items: center; /* Vertically center the container */
    min-height: 100vh; /* Ensure the body takes up the full height of the viewport */
    background-color: #f5f5f5; /* Light gray background for a neutral look */
    margin: 0; /* Remove any default margin */
    padding: 0; /* Remove any default padding */
  }

  /* The main container holding the entire Boggle game */
  #container {
    padding: 30px; /* Padding inside the container for breathing room */
    width: 300px; /* Fixed width to ensure a consistent layout */
    background-color: #e0c097; /* Light wood-like background color */
    border-radius: 0px; /* No rounded corners */
  }

  /* Grid layout for the Boggle board (4x4) */
  #boggle-board {
    display: grid; /* CSS Grid layout */
    grid-template-columns: repeat(4, 1fr); /* 4 equal columns */
    gap: 8px; /* Space between each tile */
    padding: 10px; /* Padding inside the board */
    border: 5px solid #5c4033; /* Dark brown border around the board */
    border-radius: 12px; /* Slightly rounded corners for aesthetic effect */
    background-color: #f5deb3; /* Light beige background within the board */
    margin-bottom: 20px; /* Space below the board */
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.4); /* Subtle shadow for depth effect */
  }

  /* Individual tile styling on the Boggle board */
  .boggle-tile {
    width: 55px; /* Fixed width */
    height: 55px; /* Fixed height */
    display: flex; /* Flexbox to center content inside the tile */
    align-items: center; /* Vertically center the text */
    justify-content: center; /* Horizontally center the text */
    border: 2px solid #5c4033; /* Dark brown border */
    border-radius: 8px; /* Slightly rounded corners */
    background-color: #d2a679; /* Warm brown background */
    cursor: pointer; /* Show pointer cursor to indicate interactivity */
    font-family: 'Caudex', serif; /* Vintage-style font */
    font-size: 32px; /* Large font size for easy reading */
    color: #3b2f2f; /* Dark brown text color for contrast */
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.4); /* Inner shadow for 3D effect */
    transition: transform 0.3s; /* Smooth transition on rotation */
  }

  /* Styling for tiles that have been clicked (selected) */
  .boggle-tile.clicked {
    background-color: #b58969; /* Change color to indicate selection */
  }

  /* Layout for the top row of control buttons */
  .top-row {
    display: flex; /* Flexbox layout */
    justify-content: space-between; /* Spread buttons evenly across the row */
    gap: 20px; /* Space between buttons */
    margin-bottom: 10px; /* Space below the top row */
  }

  /* Layout for the bottom row of timer controls and display */
  .bottom-row {
    display: flex; /* Flexbox layout */
    justify-content: space-between; /* Spread buttons and timer evenly */
    align-items: center; /* Align buttons with the timer vertically */
    gap: 20px; /* Space between buttons */
  }

  /* Button styling for all control buttons */
  button {
    width: 90px; /* Fixed width */
    height: 55px; /* Fixed height */
    font-family: 'Caudex', serif; /* Matching font with the tiles */
    font-size: 16px; /* Small font size for labels */
    background-color: #4b2e1a; /* Dark brown button background */
    color: #fff; /* White text for contrast */
    border-radius: 8px; /* Rounded corners */
    cursor: pointer; /* Pointer cursor for interactivity */
  }

  /* Styling for the timer display */
  #timer {
    text-align: right; /* Align text to the right */
    font-size: 32px; /* Large font for visibility */
    font-family: 'Caudex', serif; /* Matching font with other elements */
    margin-left: 15px; /* Space between timer and buttons */
    margin-right: 15px; /* Space between timer and right edge */
    flex-grow: 1; /* Pushes the timer to the right */
  }

  /* Responsive adjustments */
  @media (max-width: 600px) {
    #container {
      width: 90%;
      padding: 20px;
    }

    .boggle-tile {
      width: 40px;
      height: 40px;
      font-size: 24px;
    }

    button {
      width: 70px;
      height: 45px;
      font-size: 14px;
    }

    #timer {
      font-size: 24px;
    }
  }
</style>

<!-- JavaScript for the Boggle Game -->
<script>
  const dice = [
    "AAEEGN", "ABBJOO", "ACHOPS", "AFFKPS", "AOOTTW",
    "CIMOTU", "DEILRX", "DELRVY", "DISTTY", "EEGHNW",
    "EEINSU", "EHRTVW", "EIOSST", "ELRTTY", "HIMNUQ", "HLNNRZ"
  ];

  let selectedWord = ""; // Tracks the selected word
  let randomOrientation = true;
  let countdown;
  let timerRunning = false;
  let remainingTime = 120;
  let timerValue = 2;
  const wordSet = new Set(); // Stores valid words

  async function fetchWordList() {
    try {
      const response = await fetch('https://raw.githubusercontent.com/wordnik/wordlist/refs/heads/main/wordlist-20210729.txt');
      const text = await response.text();
      text.split('\n').forEach(word => {
        const cleanWord = word.replace(/"/g, '').trim().toLowerCase();
        wordSet.add(cleanWord); // Add word to the set
      });
      console.log("Word list loaded successfully");
    } catch (error) {
      console.error("Failed to load word list:", error);
    }
  }

  function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function generateBoggleBoard() {
    const shuffledDice = shuffle([...dice]);
    const board = shuffledDice.map(die => {
      let randomLetter = die[Math.floor(Math.random() * die.length)];
      if (randomLetter === 'Q') randomLetter = 'Qu';

      const underline = (randomLetter === 'M' || randomLetter === 'W' || randomLetter === 'N' || randomLetter === 'Z') ? 'underline' : 'none';
      return `<div class="boggle-tile" style="text-decoration: ${underline};" onclick="selectTile(this, '${randomLetter}')">
                ${randomLetter}
              </div>`;
    }).join('');
    document.getElementById('boggle-board').innerHTML = board;
    applyOrientation();
    document.getElementById('message').innerHTML = ""; // Clear any previous messages
  }

  function applyOrientation() {
    document.querySelectorAll('.boggle-tile').forEach(tile => {
      const rotation = randomOrientation ? [0, 90, 180, 270][Math.floor(Math.random() * 4)] : 0;
      tile.style.transform = `rotate(${rotation}deg)`;
    });
  }

  function toggleOrientation() {
    randomOrientation = !randomOrientation;
    document.getElementById('orientation-button').innerHTML = randomOrientation ? 'Table<br>Mode' : 'Upright<br>Mode';
    applyOrientation();
  }

  function startPauseTimer() {
    if (timerRunning) {
      clearInterval(countdown);
    } else {
      countdown = setInterval(() => {
        if (remainingTime > 0) {
          remainingTime--;
          updateTimerDisplay();
        } else {
          clearInterval(countdown);
          flashRedScreen(5);
          timerRunning = false;
        }
      }, 1000);
    }
    timerRunning = !timerRunning;
  }

  function flashRedScreen(times) {
    if (times > 0) {
      const container = document.getElementById('container');
      container.style.backgroundColor = 'red';
      setTimeout(() => {
        container.style.backgroundColor = '#e0c097';
        setTimeout(() => flashRedScreen(times - 1), 200);
      }, 200);
    }
  }

  function resetAndIncrementTimer() {
    timerValue = (remainingTime % 60 === 0) ? timerValue + 1 : Math.ceil(remainingTime / 60);
    if (timerValue > 5) timerValue = 1;

    remainingTime = timerValue * 60;
    updateTimerDisplay();
    timerRunning = false;
    clearInterval(countdown);
  }

  function updateTimerDisplay() {
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    document.getElementById('timer').innerText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  function selectTile(tile, letter) {
    if (!tile.classList.contains('clicked')) {
      tile.classList.add('clicked');
      selectedWord += letter;
    }
  }

  function validateWord() {
    const cleanWord = selectedWord.toLowerCase();
    if (wordSet.has(cleanWord)) {
      alert(`"${selectedWord}" is a valid word!`);
    } else {
      alert(`"${selectedWord}" is not a valid word.`);
    }
    resetSelection();
  }

  function resetSelection() {
    selectedWord = "";
    document.querySelectorAll('.boggle-tile').forEach(tile => tile.classList.remove('clicked'));
  }

  fetchWordList();
  generateBoggleBoard();
</script>

1) "New Board" regenerates the board randomly, using the post-2013 Boggle dice configurations

2) The next button toggles between "Table Mode" for playing face down around a table, and "Upright Mode" for playing off a vertical display

3) If you tap the tiles in order to form a word, you can check with the "Validate" button if it is in a Scrabble dictionary file

4) "Start/Pause" and "Reset/Increment" do exactly those things to the timer (2 min default)

5) Inspired by my boggle friends: Danny, Talia, Hannah, and Emma