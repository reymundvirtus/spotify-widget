import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QTimer, QRect
import sys
from io import BytesIO
import requests
import random

# initialize spotipy and genius API's
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id='d2f069d8b5254a0ca7f3a6127e801b6b',
    client_secret='7d1744a60c664983b86df397910cf59b',
    redirect_uri='http://localhost:8888/callback',
    scope='user-read-playback-state'
))
genius = lyricsgenius.Genius('2AGGl5eymo2ig3TU7AqOWgt6rJmLIPBSPeq9--z24HmQN62u15JAHldh25TMIVxl')

# === Horizontal Moving Effect for Label and Artist ===
class ScrollingLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 15))
        self.setStyleSheet("color: white; font-weight: bold")
        self.setFixedHeight(24)
        # self.setWordWrap(False)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self._full_text = text
        self._pos = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._scroll_text)
        self.timer.start(150) # adjust timer interval as needed
    
    def setText(self, text):
        self._full_text = text
        self._pos = 0
        super().setText(text)
    
    def _scroll_text(self):
        if len(self._full_text) <= 30:
            self.setText(self._full_text) # no scroll needed
            return
        
        scroll_text = self._full_text[self._pos:] + '       ' + self._full_text[:self._pos]
        super().setText(scroll_text)
        self._pos = (self._pos + 1) % len(self._full_text)

# === Music Bar Visualizer ===
class VisualizerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = [random.randint(10, 100) for _ in range(90)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100) # update every 100 ms

        self.setMinimumHeight(40)
        self.setMaximumHeight(40) # optional: cap height to keep layout tight
    
    def animate(self):
        # Randomize bar heights
        self.bars = [random.randint(10, self.height()) for _ in self.bars]
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width() // len(self.bars)
        for i, height in enumerate(self.bars):
            x = i * width
            y = self.height() - height
            painter.setBrush(QColor(255, 255, 255)) # white
            painter.setPen(Qt.NoPen) # no border
            painter.drawRect(x, y, width - 2, height) # draw bar

# === Draggable Transparent Widget ===
class DraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None


# === Function to Get Current Song Info ===
def fetch_current_track():
    current = sp.current_playback()
    if not current or not current['is_playing']:
        return None

    track = current['item']
    title = track['name']
    artist = track['artists'][0]['name']
    image_url = track['album']['images'][0]['url']
    img_data = requests.get(image_url).content

    # try:
    #     song = genius.search_song(title, artist)
    #     raw_lyrics = song.lyrics if song else "Lyrics not found"
    #     if song:
    #         # Remove metadata and descriptions before first [Verse] or [Chorus]
    #         parts = raw_lyrics.split('[')
    #         if len(parts) > 1:
    #             lyrics = "[" + "[".join(parts[1:])  # Keep everything from the first tag
    #         else:
    #             lyrics = raw_lyrics
    #     else:
    #         lyrics = "Lyrics not found"
    # except:
    #     lyrics = "Lyrics not found"

    return {
        "title": title,
        "artist": artist,
        "img_data": img_data,
        # "lyrics": lyrics
    }


# === UI Setup ===
def create_ui():
    # Window Setup
    window = DraggableWidget()
    window.setWindowTitle("Spotify Lyrics Widget")
    window.setGeometry(100, 100, 500, 500) # x, y, width, height
    window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    window.setAttribute(Qt.WA_TranslucentBackground)

    # Layouts
    main_layout = QVBoxLayout()
    top_layout = QHBoxLayout()
    info_layout = QVBoxLayout()

    # Widgets
    album_label = QLabel()
    album_label.setFixedSize(104, 104)

    title_label = ScrollingLabel()
    artist_label = ScrollingLabel()
    visualizer = VisualizerBar()

    # Styling of title
    for lbl in [title_label]:
        lbl.setStyleSheet("color: white; font-weight: bold")
        lbl.setFont(QFont("Segoe UI", 15))
        lbl.setContentsMargins(5, 0, 0, 0)
        lbl.setWordWrap(True)

    # Styling of artist
    for lbl in [artist_label]:
        lbl.setStyleSheet("color: white; font-weight: bold")
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setContentsMargins(5, 0, 0, 0)
        lbl.setWordWrap(True)

    # lyrics_label = QLabel()
    # lyrics_label.setStyleSheet("color: white")
    # lyrics_label.setFont(QFont("Segoe UI", 8))
    # lyrics_label.setWordWrap(True)
    # lyrics_label.setContentsMargins(10, 10, 10, 10) # left, top, right, bottom

    # Add to layout
    top_layout.addWidget(album_label)
    info_layout.addWidget(title_label)
    info_layout.addWidget(artist_label)
    info_layout.addWidget(visualizer)
    top_layout.addLayout(info_layout)

    main_layout.addLayout(top_layout)
    # main_layout.addWidget(visualizer)
    # main_layout.addWidget(lyrics_label)

    window.setLayout(main_layout)

    return window, album_label, title_label, artist_label # lyrics_label


# === Periodic Update Function ===
def setup_auto_refresh(window, album_label, title_label, artist_label):  # lyrics_label
    window.timer = QTimer()  # 🔁 Store it as an attribute so it's not garbage-collected

    def update():
        print("[DEBUG] Timer tick")
        current = sp.current_playback()
        if not current or not current['is_playing']:
            print("[DEBUG] Nothing playing")
            return

        track = current['item']
        title = track['name']
        artist = track['artists'][0]['name']
        image_url = track['album']['images'][0]['url']
        img_data = requests.get(image_url).content

        # try:
        #     song = genius.search_song(title, artist)
        #     raw_lyrics = song.lyrics if song else "Lyrics not found"
        #     parts = raw_lyrics.split('[')
        #     lyrics = "[" + "[".join(parts[1:]) if len(parts) > 1 else raw_lyrics
        # except Exception as e:
        #     print("[ERROR]", e)
        #     lyrics = "Lyrics not found"

        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        album_label.setPixmap(pixmap.scaled(104, 104, Qt.KeepAspectRatio))

        title_label.setText(title)
        artist_label.setText(artist)
        # lyrics_label.setText(lyrics)

    window.timer.timeout.connect(update)
    window.timer.start(10000)  # every 10 seconds
    update()  # immediate first run


# === Main Application ===
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Build UI and start
    window, album_label, title_label, artist_label  = create_ui() # lyrics_label
    setup_auto_refresh(window, album_label, title_label, artist_label) # lyrics_label

    window.show()
    sys.exit(app.exec_())
