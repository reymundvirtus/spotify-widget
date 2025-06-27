# 🎵 Spotify Widget with Lyrics & Visualizer

A frameless, draggable, translucent Spotify widget built with PyQt5.  
Displays current track info, album art, and animated visualizer — with Genius lyrics integration (optional).

<p align="center">
  <img src="https://github.com/reymundvirtus/spotify-widget/blob/main/assets/widget.gif" alt="Music Visualizer Demo">
</p>

---

## 🚀 Features

- 🎧 Displays Spotify playback info (title, artist, album art)  
- 🎼 Optional: Show lyrics using Genius API  
- 🌈 Visualizer animation  
- 🪟 Frameless, transparent widget with glass-like style  
- 🖱️ Draggable and resizable  
- 🔐 Credentials stored securely in `.env` file  

---

## ⚙️ Prerequisites

- Python 3.9+
- A Spotify Developer account and app (for access token)
- (Optional) Genius API account (for lyrics)

---

## Step 1: Create `.env`

Create a file named `.env` in the project root and add your credentials:

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
GENIUS_ACCESS_TOKEN=your_genius_token   # Optional, for lyrics
```

---

## Step 2: Install Dependencies

```
python -m venv env
source env/bin/activate   # On Windows: env\Scripts\activate
```
Then install the required libraries:

```
pip install -r requirements.txt
```

---

## Step 3: Run the Widget

```
python main.py
```
