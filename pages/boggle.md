---
layout: default
title: Boggle
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
  /* Boggle game specific styles */
  .boggle-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
    /* Removed background-color to keep the website's normal background */
    padding: 20px;
    box-sizing: border-box;
  }

  #container {
    padding: 30px;
    width: 300px;
    background-color: #e0c097;
    border-radius: 0px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  #boggle-board {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    padding: 10px;
    border: 5px solid #5c4033;
    border-radius: 12px;
    background-color: #f5deb3;
    margin-bottom: 20px;
    box-shadow: 0 0 15px rgba(0, 0, 0, 0.4);
  }

  .boggle-tile {
    width: 55px;
    height: 55px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #5c4033;
    border-radius: 8px;
    background-color: #d2a679;
    cursor: pointer;
    font-family: 'Caudex', serif;
    font-size: 32px;
    color: #3b2f2f;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.4);
    transition: transform 0.3s;
  }

  .boggle-tile.clicked {
    background-color: #b58969;
  }

  .top-row, .bottom-row {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 10px;
  }

  button {
    width: 90px;
    height: 55px;
    font-family: 'Caudex', serif;
    font-size: 16px;
    background-color: #4b2e1a;
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  button:hover {
    background-color: #5c4033;
  }

  #timer {
    text-align: right;
    font-size: 32px;
    font-family: 'Caudex', serif;
    margin-left: 15px;
    margin-right: 15px;
    flex-grow: 1;
    /* Changed timer text color to black */
    color: #000;
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
      const response = await fetch('https://benshindel.github.io/assets/textfiles/wordlist1.txt')
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

  // Initialize the game
  fetchWordList();
  generateBoggleBoard();
</script>

1) "New Board" regenerates the board randomly, using the post-2013 Boggle dice configurations

​2) The next button toggles between "Table Mode" for playing face down around a table, and "Upright Mode" for playing off a vertical display

3) If you tap the tiles in order to form a word, you can check with the "Validate" button if it is in a Scrabble dictionary file

4) "Start/Pause" and "Reset/Increment" do exactly those things to the timer (2 min default)

5) Inspired by my boggle friends: Danny, Talia, Hannah, and Emma
