# MrArrow

MrArrow is an archery game made with Python and Pygame by a group of grade 9 classmates.

## How to play
Move your archer along the ground, aim the bow, and shoot arrows at the target. Arrows fly in an arc because gravity pulls them down. The closer you hit to the middle, the more points you get:

| Ring | Points |
|------|--------|
| Yellow (bullseye) | 10 |
| Red | 8 |
| Blue | 6 |
| Black | 4 |
| White | 2 |

Each level gives you a limited number of arrows and a score goal. Reach the goal to go to the next level, where the target gets smaller and starts moving faster. If you run out of arrows before reaching the goal, the game is over. Your best score is saved in `highscore.txt`.

## Controls
| Key | Action |
|-----|--------|
| LEFT / RIGHT (or A / D) | Move |
| UP / DOWN (or W / S) | Aim the bow |
| Hold SPACE | Draw the bow (hold longer for more power) |
| Release SPACE | Shoot |
| P | Pause |
| M | Mute / unmute |
| ESC | Quit |

## Features
- Arrow physics with gravity, aiming and adjustable shot power
- Five levels, then it keeps getting harder
- Moving targets with scoring rings
- Title, pause, level complete and game over screens
- Score, arrows left and a power bar shown on screen
- High score saved between games
- Sound effects and background music made in code, so no sound files are needed

## Installation
```sh
pip install -r requirements.txt
```
This installs [pygame-ce](https://pyga.me/), a drop-in replacement for pygame (your code still says `import pygame`). Plain `pygame` 2.6 has no working font module on Python 3.14.

## Usage
```sh
python main.py
```

## Ideas for later
- Wind that pushes arrows sideways
- Picture and sound files instead of shapes and beeps
- More than one target at a time

## Contributing
Feel free to fork this repository and submit pull requests. Contributions are welcome!

## Authors
- [Prarambha369](https://github.com/Prarambha369)
- Classmates of Grade 9
