import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QTimer
import sys
import requests
import random

# === Spotify & Genius Auth ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id='d2f069d8b5254a0ca7f3a6127e801b6b',
    client_secret='7d1744a60c664983b86df397910cf59b',
    redirect_uri='http://localhost:8888/callback',
    scope='user-read-playback-state'
))
genius = lyricsgenius.Genius('2AGGl5eymo2ig3TU7AqOWgt6rJmLIPBSPeq9--z24HmQN62u15JAHldh25TMIVxl')

# === Scrolling Label ===
class ScrollingLabel(QLabel):
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 15))
        self.setFixedHeight(24)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self._full_text = text
        self._pos = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._scroll_text)
        self.timer.start(150)

    def setText(self, text):
        self._full_text = text
        self._pos = 0
        super().setText(text)

    def _scroll_text(self):
        if len(self._full_text) <= 30:
            super().setText(self._full_text)
            return
        scroll_text = self._full_text[self._pos:] + '       ' + self._full_text[:self._pos]
        super().setText(scroll_text)
        self._pos = (self._pos + 1) % len(self._full_text)

# === Visualizer Bar ===
class VisualizerBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = [random.randint(10, 100) for _ in range(90)]
        self.bar_color = QColor(255, 255, 255)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100)
        self.setFixedHeight(40)

    def set_color(self, color_name):
        self.bar_color = QColor(255, 255, 255) if color_name == 'white' else QColor(0, 0, 0)
        self.update()

    def animate(self):
        self.bars = [random.randint(10, self.height()) for _ in self.bars]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width() // len(self.bars)
        for i, height in enumerate(self.bars):
            x = i * width
            y = self.height() - height
            painter.setBrush(self.bar_color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(x, y, width - 2, height)

# === Draggable Transparent Widget ===
class DraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.dark_theme = True
        self.title_label = None
        self.artist_label = None
        self.visualizer = None

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            self.dark_theme = not self.dark_theme
            self.toggle_theme()

    def toggle_theme(self):
        color = 'white' if self.dark_theme else 'black'
        self.title_label.setStyleSheet(f"color: {color}; font-weight: bold")
        self.artist_label.setStyleSheet(f"color: {color}; font-weight: bold")
        self.visualizer.set_color(color)

# === Create UI ===
def create_ui():
    window = DraggableWidget()
    window.setWindowTitle("Spotify Lyrics Widget")
    window.setGeometry(100, 100, 500, 500)
    window.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus | Qt.X11BypassWindowManagerHint)
    window.setAttribute(Qt.WA_TranslucentBackground)

    main_layout = QVBoxLayout()
    top_layout = QHBoxLayout()
    info_layout = QVBoxLayout()

    album_label = QLabel()
    album_label.setFixedSize(104, 104)

    title_label = ScrollingLabel()
    title_label.setContentsMargins(5, 0, 0, 0)
    title_label.setStyleSheet("color: white; font-weight: bold")
    title_label.setFont(QFont("Segoe UI", 15))

    artist_label = ScrollingLabel()
    artist_label.setContentsMargins(5, 0, 0, 0)
    artist_label.setStyleSheet("color: gray; font-weight: bold")
    artist_label.setFont(QFont("Segoe UI", 10))

    visualizer = VisualizerBar()

    info_layout.addWidget(title_label)
    info_layout.addWidget(artist_label)
    info_layout.addWidget(visualizer)

    top_layout.addWidget(album_label)
    top_layout.addLayout(info_layout)
    main_layout.addLayout(top_layout)

    window.setLayout(main_layout)
    window.title_label = title_label
    window.artist_label = artist_label
    window.visualizer = visualizer

    return window, album_label, title_label, artist_label

# === Auto Refresh Logic ===
def setup_auto_refresh(window, album_label, title_label, artist_label):
    window.timer = QTimer()

    def update():
        # print("[DEBUG] Timer tick")
        current = sp.current_playback()
        
        if not current or not current.get("is_playing") or not current.get("item"):
            # print("[DEBUG] Nothing is currently playing.")
            album_label.clear()
            title_label.setText("No track playing")
            artist_label.setText("")
            return

        track = current['item']
        title = track['name']
        artist = track['artists'][0]['name']
        image_url = track['album']['images'][0]['url']
        img_data = requests.get(image_url).content

        pixmap = QPixmap()
        pixmap.loadFromData(img_data)
        album_label.setPixmap(pixmap.scaled(104, 104, Qt.KeepAspectRatio))

        title_label.setText(title)
        artist_label.setText(artist)

    window.timer.timeout.connect(update)
    window.timer.start(10000)
    update()

# === Main ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window, album_label, title_label, artist_label = create_ui()
    setup_auto_refresh(window, album_label, title_label, artist_label)
    window.show()
    sys.exit(app.exec_())
