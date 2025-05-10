# Flip7 MDP Simulator

This folder contains two Python modules to model and simulate the card game **Flip7** under a simple MDP-style engine.

## Files

- **game_functions.py**  
  Core game logic and state classes:  
  - `CardType`, `NumberCard`, `ActionCard`, `ModifierCard`  
  - `Deck` with draw/discard and auto-reshuffle  
  - `PlayerState` (per-round flags, busted, pending flips/freezes)  
  - `GameState` (turn-taking, `step(action)`, scoring, race-to-target)

- **random_sim.py**  
  A random-policy simulator that:  
  1. Biases **Hit** vs. **Stay** to provoke busts  
  2. Plays rounds until a player reaches the target score (default 100)  
  3. Logs and prints each round’s actions, hits, cards drawn, and points  
  4. Declares a winner  

## Requirements

- Python 3.7 or higher  
- No external dependencies  

## Quick Start

1. Clone or copy these two files into the same directory.  
2. From that directory, run:
   ```bash
   python random_sim.py

