import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lyricsgenius
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPainterPath, QFontMetrics
from PyQt5.QtCore import Qt, QTimer
import sys
import requests
import random, os
from dotenv import load_dotenv

load_dotenv()

# === Spotify & Genius Auth ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
    scope='user-read-playback-state'
))
genius = lyricsgenius.Genius(os.getenv('GENIUS_ACCESS_TOKEN'))

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
        if len(text) > 35:
            # Stop scrolling and show elided text
            self.timer.stop()
            metrics = QFontMetrics(self.font())
            elided = metrics.elidedText(text, Qt.ElideRight, self.width())
            super().setText(elided)
        else:
            # Start scrolling
            self.timer.start(150)
            super().setText(text)

    def resizeEvent(self, event):
        # Reapply text formatting when the widget resizes
        self.setText(self._full_text)
        super().resizeEvent(event)

    def _scroll_text(self):
        if len(self._full_text) <= 25:
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
        self.bar_color = QColor(30, 215, 96)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(100)
        self.setFixedHeight(40)

    def animate(self):
        self.bars = [random.randint(10, self.height()) for _ in self.bars]
        self.update()

    def pause(self):
        self.timer.stop()
        self.bars = [1 for _ in self.bars]
        self.update()

    def resume(self):
        if not self.timer.isActive():
            self.timer.start(100)

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
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Frosted glass background (semi-transparent white)
        bg_color = QColor(255, 255, 255, 25)  # low opacity white
        border_color = QColor(255, 255, 255, 80)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(bg_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(rect, 20, 20)  # radius 20 for curves

# === Create UI ===
def create_ui():
    window = DraggableWidget()
    window.setWindowTitle("Spotify Lyrics Widget")
    window.setGeometry(100, 100, 500, 100)  # Set the initial window size
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

    return window, album_label, title_label, artist_label, window.visualizer

# === Auto Refresh Logic ===
def setup_auto_refresh(window, album_label, title_label, artist_label, visualizer):
    window.timer = QTimer()

    def update():
        try:
            current = sp.current_playback()

            if not current or not current.get("is_playing") or not current.get("item"):
                album_label.clear()
                title_label.setText("No track playing")
                artist_label.setText("Play or check your connection")
                visualizer.pause()
                return

            track = current['item']
            title = track['name']
            artist = track['artists'][0]['name']
            image_url = track['album']['images'][0]['url']
            img_data = requests.get(image_url).content

            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            pixmap = pixmap.scaled(104, 104, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

            # Create a rounded pixmap
            rounded = QPixmap(pixmap.size())
            rounded.fill(Qt.transparent)

            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 16, 16)  # 16px radius
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            album_label.setPixmap(rounded)

            title_label.setText(title)
            artist_label.setText(artist)
            visualizer.resume()
        except Exception:
            album_label.clear()
            title_label.setText("No connection")
            artist_label.setText("Please check your connection")
            visualizer.pause()

    window.timer.timeout.connect(update)
    window.timer.start(10000)
    update()

# === Main ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window, album_label, title_label, artist_label, visualizer = create_ui()
    setup_auto_refresh(window, album_label, title_label, artist_label, visualizer)
    window.show()
    sys.exit(app.exec_())
