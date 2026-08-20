# Simple 2D Game Prototype

A lightweight Python game prototype featuring a keyboard-controlled, animated character.

## Tech Stack
- **Language:** Python 3.10+
- **Core Library:** Pygame (for game loops, window management, and 2D rendering)

## Core Commands
- **Install Dependencies:** `pip install pygame`
- **Run Game:** `python main.py`

## Coding Guidelines
- **Architecture:** Keep input processing, state updates, and rendering strictly separated. Use a simple Object-Oriented (OOP) structure with a dedicated `Player` class.
- **Game Loop:** Enforce a steady frame rate (target 60 FPS) using `pygame.time.Clock()`.
- **Inputs:** Implement simultaneous support for both **WASD** and **Arrow Keys** for smooth 2D vector movement.
- **Visuals:** Start with a clean color-coded rectangular placeholder for the player, transitioning to sprite sheet calculations once assets are introduced.
- **Code Style:** Strictly adhere to PEP 8 standards. Write clear, human-readable variable names and keep rendering loops lightweight.