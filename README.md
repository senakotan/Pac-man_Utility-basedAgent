# 🟡 Pac-Man Utility Agent: Classic Game with Intelligent AI

This project is a modern reinterpretation of the classic **Pac-Man** game, powered by a **Utility-Based Artificial Intelligence (AI) Agent** that makes real-time strategic decisions.

The agent continuously evaluates survival, pellet collection efficiency, ghost threats, and power-pellet opportunities to determine the **most optimal action** at every moment.

---

## 🎮 Overview, Features, and Setup

Pac-Man can be controlled **manually** by the user or **automatically** by the intelligent AI agent. The agent observes the environment, computes utility scores for possible actions, and selects the one with the highest expected benefit.

### **Key Decision Factors:**

* **Avoiding** high-danger ghosts
* Navigating the **shortest safe paths**
* **Prioritizing** pellet-dense areas
* **Balancing risk and reward** throughout the game

### **🌟 Core Features**

* **Utility-based AI** decision-making framework
* Smooth directional sprite **rotation** and animations
* Adaptive ghost interaction and **danger evaluation**
* **Safe shortest-path** navigation (BFS/UCS-inspired)
* Supports both manual and **AI-controlled** gameplay

### **▶️ How to Run**

Follow these steps to set up and run the project locally:

1.  **Install Dependencies:** The project requires the **Pygame** library.
    ```bash
    pip install pygame
    ```
2.  **Run the Game:** Start the game by running the main file.
    ```bash
    python main.py
    ```

---

## 🧠 AI Agent Logic and Behavior

The Utility Agent evaluates multiple competing behaviors every frame and selects the optimal one based on calculated utility values. 

### **Evaluated Behaviors Include:**

* **Fleeing** from threatening ghosts
* **Chasing** ghosts during power mode
* **Moving** toward pellets and power pellets
* Computing **safe shortest paths**
* **Dynamically adjusting** behavior based on danger level

---

## 📁 Project Structure

The project is organized into a modular structure to keep functionalities clean and manageable:
pac-man-utility-agent/

├── main.py # Game loop, rendering, event handling
├── pacman.py # Pac-Man movement, animations, state logic
├── ghost.py # Ghost movement, modes, frightened behavior
├── assets/ # Sprites, sound effects, textures

---
