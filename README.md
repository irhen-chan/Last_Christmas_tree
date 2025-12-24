# 🎄 Terminal Last Christmas

A fully animated **terminal-based Christmas scene** with:

- A swaying, twinkling ASCII Christmas tree  
- A cozy house with chimney smoke  
- Layered snowfall that lands on the ground  
- Time-synced karaoke lyrics using `.lrc` files  
- Optional audio playback (via your system’s default player)

All rendered **entirely in the terminal** using Python and ANSI escape codes.

---

## Demo

<img width="812" height="411" alt="image" src="https://github.com/user-attachments/assets/c9261630-dbcc-4c2c-9c8f-1add44782429" />


Run it in a dark terminal with a monospaced font for best results.

> The visuals are synced to the song *Last Christmas* (audio file not included for licensing reasons).

---

## Features

- 🎄 **Animated ASCII Tree**
  - Twinkling lights
  - Animated garlands
  - Pulsing star
  - Gentle sway motion

- 🏠 **House Scene**
  - Same ground level as the tree
  - Chimney smoke animation
  - Snow accumulation illusion

- ❄️ **Snow System**
  - Confined to the scene area (no snow over lyrics)
  - Layered background + foreground flakes
  - Smooth drift and fall speeds

- 🎤 **Karaoke Lyrics**
  - `.lrc` file parsing
  - Current + next line display
  - Optional lyric offset for audio intros

- 🔊 **Audio Playback (Optional)**
  - Uses your OS default player on Windows
  - Falls back gracefully if audio isn’t available

---

## Requirements

- Python **3.9+**
- A terminal that supports ANSI escape codes  
  (Windows Terminal, VS Code terminal, iTerm2, etc.)

Optional:
```bash
pip install colorama
