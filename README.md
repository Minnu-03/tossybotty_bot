# tossybotty_bot (A Savage Telegram Bot)

A modular Telegram bot built with python-telegram-bot and Groq language models.  
It includes coin flips, dice rolls, predictions, challenges, and AI-driven responses, designed with scalability and customization in mind.

---

## Features

- Coin tosses with dynamic responses  
- Magic 8-Ball (AI-generated replies)  
- Dice rolls with contextual feedback  
- Predictions between two options  
- Random picker from a list  
- Roasting: self, friend, and roast battles  
- Daily challenges and mini-games  
- User statistics and leaderboards  
- Admin utilities for data export and resets  

---

## Installation

1. Clone the repository and enter the project folder.  
2. Set up and activate a virtual environment.  
3. Install dependencies from `requirements.txt`.  
4. Add your bot token and Groq API key to a `.env` file.  
5. Run the bot and start using it on Telegram.  

---

## Basic Commands

```text
/start                 — Show welcome message and menu
/toss                  — Flip a coin
/dice                  — Roll a dice
/8ball <question>      — Ask a yes/no question
/predict A or B        — Let the bot decide between two options
/random item1 item2    — Pick one item randomly
/roast <text>          — Get roasted
/roastfriend @username — Roast a tagged friend
/roastbattle @username — Start a roast battle
/failpredict <decision>— Predict how your decision will backfire
/stats                 — View your statistics
/challenges            — View daily challenges
/leaderboard           — See leaderboard rankings
/games                 — Access mini-games
/help                  — Show all available commands


## Admin Commands

