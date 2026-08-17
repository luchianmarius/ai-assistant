import main_functions as mf
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit,
    QLineEdit, QFrame, QSizePolicy, QListWidget,
    QSplitter
)
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtCore import QSize
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPixmap, QPainter


# ---------- SVG icon helper ----------
def svg_icon(svg_path, size=QSize(18, 18)):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
    painter.end()

    return QIcon(pixmap)

# ----- sgv icon renderer (white color) --------
def svg_icon_white(svg_path, size=QSize(18, 18)):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(QColor(0, 0, 0, 0))  # transparent

    p = QPainter(pixmap)
    renderer.render(p, QRectF(0, 0, size.width(), size.height()))
    p.end()

    # Repaint with white using the alpha channel as mask
    white = QPixmap(size)
    white.fill(QColor(255, 255, 255, 255))

    tinted = QPixmap(size)
    tinted.fill(QColor(0, 0, 0, 0))

    p = QPainter(tinted)
    p.setCompositionMode(QPainter.CompositionMode_Source)
    # keep only alpha from original
    p.drawPixmap(0, 0, pixmap)
    p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.drawPixmap(0, 0, white)
    p.end()

    return QIcon(tinted)

# default styles
blue_button = """
        QPushButton {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 10px;
            font-weight: 600;
        }
        QPushButton:hover { background: #1d4ed8; }
    """

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ai_assistant")
        self.setGeometry(700, 100, 1000, 700)

        # central widget (IMPORTANT: make it an instance)
        centralwidget = QWidget()
        self.setCentralWidget(centralwidget)

        # Overall layout: horizontal (sidebar | main)
        root_layout = QHBoxLayout(centralwidget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Optional: splitter makes resizing feel nice
        splitter = QSplitter()
        splitter.setOrientation(1)  # Qt.Horizontal
        root_layout.addWidget(splitter)

        #########################################
        #SIDEBAR
        
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setStyleSheet("""
            QFrame { background: #0f172a; }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        # Sidebar top: app title + new chat
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.title_label = QLabel("AI Assistant")
        self.title_label.setStyleSheet("color: #e5e7eb; font-weight: 600;")
        self.title_label.setFont(QFont("Arial", 14))

        header_row.addWidget(self.title_label, 1)

        self.sidebaricon = QPushButton()
        self.sidebaricon.setIcon(svg_icon_white("icons/layout-sidebar.svg", QSize(18, 18)))
        self.sidebaricon.setIconSize(QSize(18, 18))
        self.sidebaricon.setFixedSize(34, 34)
        self.sidebaricon.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        header_row.addWidget(self.sidebaricon, 0)

        sidebar_layout.addLayout(header_row)

        self.newchatbutton = QPushButton(" New chat")
        self.newchatbutton.setIcon(svg_icon_white("icons/pencil-square.svg", QSize(18, 18)))
        self.newchatbutton.setIconSize(QSize(18, 18))
        self.newchatbutton.setStyleSheet(blue_button)
        sidebar_layout.addWidget(self.newchatbutton)

        # Chat list area (placeholder)
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                color: #e5e7eb;
                border: none;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background: rgba(255,255,255,0.08);
            }
        """)
        # placeholder items
        for name in ["Chat 1", "Chat 2", "Chat 3"]:
            self.chat_list.addItem(name)

        sidebar_layout.addWidget(self.chat_list, 1)

        splitter.addWidget(sidebar)

        # =======================
        # Main panel
        # =======================
        main_panel = QFrame()
        main_panel.setFrameShape(QFrame.StyledPanel)
        main_panel.setStyleSheet("""
            QFrame { background: #111827; }
        """)

        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar (header)
        topbar = QFrame()
        topbar.setStyleSheet("""
            QFrame {
                background: #0b1220;
                border-bottom: 1px solid rgba(255,255,255,0.08);
            }
        """)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(16, 12, 16, 12)

        self.top_title = QLabel("Your chats")
        self.top_title.setStyleSheet("color: #e5e7eb; font-weight: 600;")

        topbar_layout.addWidget(self.top_title, 1)

        # Example action button
        dummy_btn = QPushButton("☰")
        dummy_btn.setFixedSize(36, 36)
        dummy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.06); }
        """)
        topbar_layout.addWidget(dummy_btn, 0)

        main_layout.addWidget(topbar)

        # Chat area
        chat_area = QFrame()
        chat_area.setStyleSheet("""
            QFrame {
                background: #0b1220;
            }
        """)
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(16, 16, 16, 16)

        # Placeholder "messages"
        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.chat_view.setText(
            "Assistant messages will appear here...\n\n"
            "User: Hello!\n"
            "Assistant: Hi! How can I help?"
        )

        chat_layout.addWidget(self.chat_view, 1)
        main_layout.addWidget(chat_area, 1)

        # Bottom input bar
        input_bar = QFrame()
        input_bar.setStyleSheet("""
            QFrame {
                background: #0b1220;
                border-top: 1px solid rgba(255,255,255,0.08);
            }
        """)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.06);
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 13px;
            }
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedHeight(40)
        self.send_button.setStyleSheet(blue_button)

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button, 0)

        main_layout.addWidget(input_bar)

        splitter.addWidget(main_panel)

        # Start sizes for splitter panes
        splitter.setSizes([240, 760])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
