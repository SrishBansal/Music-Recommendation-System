# 🎧 MusicMatch – Your AI-Powered Music Recommendation System

Welcome to **MusicMatch** — a sleek, AI-enhanced music recommendation system built with Python and Gradio. Whether you're looking for song suggestions based on a track you love or want to explore an artist's vibe, MusicMatch has you covered. Build your playlist, discover fresh music, and enjoy a clean, interactive experience.

---

## 🚀 Features

- 🎼 **Song-based recommendations** using TF-IDF & Cosine Similarity  
- 🎤 **Artist-based recommendations** with randomized selections  
- 📂 **Playlist management**: Add your favorite tracks and view them anytime  
- 🎨 **Modern UI** with Gradio and custom CSS for a polished look  
- 🔗 **Exploratory integration with Spotify Developer API** for 30-second song previews *(experimental)*

---

## 🛠️ Tech Stack

- **Python** 🐍  
- **Gradio** – For the user interface  
- **pandas + scikit-learn** – For recommendation logic  
- **SQLite** – To store and manage playlist data  
- **HTML + CSS** – For styling the interface

---

## 📂 Project Structure

├── ex.csv # Sample dataset of songs
├── music_recommendation.py

# Main Python script 
├── music_recommendation.db 
# SQLite DB (auto-created) 

└── README.md # This file


---

## 🧠 How It Works

1. The system uses **TF-IDF vectorization** on song genres to build a similarity matrix.
2. Based on the selected song or artist, it fetches the top 5 similar tracks.
3. You can add songs to a playlist and view them in a styled table.
4. The app is powered by **Gradio Blocks**, styled with custom CSS, and optionally supports song previews via the **Spotify Developer API** (optional exploration).

---

## ▶️ Running the App

1. Make sure you have Python 3.7+ installed.
2. Install dependencies:

```bash
pip install gradio pandas scikit-learn

python music_recommendation.py
