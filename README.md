# Impostor Game

**Author:** bizzy-0110

## Overview
Impostor Game is a multiplayer social deduction game designed for both **LAN** and **Online (like in a VPS)** play. Players are assigned roles (Citizen or Imposter); Citizens share a **Secret Word** that the Imposter doesn't know. The goal is to deduce who the imposter is through a series of clue-giving rounds and voting.

## How it Works
The game follows a Client-Server architecture:
- **Server**: Manages multiple lobbies, game state, and communication.
- **Client**: A Python-based GUI application (using CustomTkinter) for players to interact with the game.

### Game Flow
1.  **Lobby**: Players connect to the server and create or join a game lobby via a unique code.
2.  **Roles**:
    -   **Citizen**: Receives a specific secret word.
    -   **Imposter**: Receives the role "IMPOSTER" but NOT the secret word.
3.  **Clue Phase**: Players take turns giving a one-word clue related to the secret word. The Imposter must blend in without knowing the word.
4.  **Voting**: After a set number of rounds, players vote on who they think the Imposter is.
5.  **Win Condition**:
    -   Citizens win if they vote out the Imposter.
    -   Imposter wins if they survive the vote.

## Installation & Running

### Requirements
- Python 3.x
- `customtkinter`

### How to Run
1.  **Start the Server**:
    Navigate to the `Server` directory and run:
    ```bash
    python main.py
    ```
2.  **Start Clients**:
    Navigate to the `Client` directory and run:
    ```bash
    python main.py
    ```
    (You can run multiple clients to test locally).

## Features
-   **Multi-Lobby System**: Multiple games can run simultaneously with unique codes.
-   **Robust Lobby Management**:
    -   **Host Migration**: If the host leaves, leadership is automatically transferred.
    -   **Auto-Cleanup**: Empty lobbies are automatically removed.
    -   **Duplicate Names**: Servers automatically handle duplicate nicknames (e.g., "Player 1").
-   **Game Flow**:
    -   **Clue Phase**: Turn-based clue giving.
    -   **Voting System**: Democratic voting phase. Ties result in Imposter victory.
    -   **Game Over Screen**: Clear results with options to "Play Again" or "Leave".
-   **User Interface**:
    -   Modern dark-mode UI with `customtkinter`.
    -   **Toast Notifications**: Non-intrusive error messages.
    -   **Dynamic Chat**: Clue history wipes automatically for new games.
-   **Customizable**: Adjust rounds and settings via `settings.json`.
