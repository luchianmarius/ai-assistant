import sound_functions as sf
import ai_functions as ai
import json

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit,
    QLineEdit, QFrame, QSizePolicy, QListWidget,
    QSplitter
)
from PyQt5.QtGui import QIcon, QColor, QFont, QKeyEvent
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
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
        self.splitter = QSplitter()
        self.splitter.setOrientation(1)  # Qt.Horizontal
        self.splitter.setFrameShape(QFrame.NoFrame)
        self.splitter.setHandleWidth(0)
        self.splitter.setStyleSheet("""
            QSplitter {
                border: none;
                background: #0b1220;
            }

            QSplitter::handle {
                background: transparent;
                border: none;
                width: 0px;
            }
        """)

        root_layout.addWidget(self.splitter)

        # SOME VARIABLES #########################
        self.chatid = None
        self.sb_visibility = True

        #########################################
        #SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setFrameShape(QFrame.StyledPanel)
        self.sidebar.setStyleSheet("""
            QFrame { background: #0f172a; }
        """)

        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(14, 14, 14, 14)
        self.sidebar_layout.setSpacing(10)

        # Sidebar top: app title + new chat
        self.header_row = QHBoxLayout()
        self.header_row.setSpacing(10)

        self.title_label = QLabel("AI Assistant")
        self.title_label.setStyleSheet("color: #e5e7eb; font-weight: 600;")
        self.title_label.setFont(QFont("Arial", 14))

        self.header_row.addWidget(self.title_label, 1)

        self.sidebaricon = QPushButton()
        self.sidebaricon.setIcon(svg_icon_white("icons/layout-sidebar.svg", QSize(18, 18)))
        self.sidebaricon.setIconSize(QSize(18, 18))
        self.sidebaricon.setFixedSize(34, 34)
        self.sidebaricon.clicked.connect(self.togglesidebar)
        self.sidebaricon.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        self.header_row.addWidget(self.sidebaricon, 0)

        self.sidebar_layout.addLayout(self.header_row)

        self.newchatbutton = QPushButton(" New chat")
        self.newchatbutton.setIcon(svg_icon_white("icons/pencil-square.svg", QSize(18, 18)))
        self.newchatbutton.setIconSize(QSize(18, 18))
        self.newchatbutton.setStyleSheet(blue_button)
        self.newchatbutton.clicked.connect(self.newchat)

        self.sidebar_layout.addWidget(self.newchatbutton)


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

        for name in ai.getchatlist():
            self.chat_list.addItem(name)

        self.chat_list.itemClicked.connect(self.chat_item_clicked)


        self.sidebar_layout.addWidget(self.chat_list, 1)

        self.splitter.addWidget(self.sidebar)

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

        # Chat area
        chat_area = QFrame()
        chat_area.setStyleSheet("""
            QFrame {
                background: #0b1220;
            }
        """)
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(16, 16, 16, 16)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px;
                font-size: 50px;
            }
        """)
        self.chat_view.setText("Welcome to my AI assistant")
        self.chat_view.setAlignment(Qt.AlignCenter)

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

        self.message_input = MessageInput()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.sendRequested.connect(self.sendmsg)
        self.message_input.setMinimumHeight(40)
        self.message_input.setMaximumHeight(120)
        self.message_input.setStyleSheet("""
            QTextEdit {
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
        self.send_button.clicked.connect(self.sendmsg)

        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_button, 0)

        main_layout.addWidget(input_bar)

        self.splitter.addWidget(main_panel)

        self.splitter.setSizes([250, self.width() - 250])

    def togglesidebar(self):
        if self.sb_visibility:
            self.title_label.hide()
            self.chat_list.setVisible(False)

            self.newchatbutton.setText("")
            self.newchatbutton.setToolTip("New chat")
            self.newchatbutton.setFixedSize(40, 40)

            self.sidebar_layout.setContentsMargins(4, 14, 4, 14)
            self.sidebar_layout.setSpacing(8)
            self.sidebar_layout.setAlignment(Qt.AlignTop)

            self.header_row.setContentsMargins(0, 0, 0, 0)
            self.header_row.setSpacing(0)
            self.header_row.setAlignment(Qt.AlignHCenter)

            self.sidebaricon.setFixedSize(40, 40)

            self.sidebar.setMinimumWidth(48)
            self.sidebar.setMaximumWidth(48)
            self.sidebar.setFixedWidth(48)

            self.splitter.setSizes([48, self.width() - 48])

            self.sb_visibility = False

        else:
            self.title_label.show()
            self.chat_list.show()

            self.newchatbutton.setText(" New chat")
            self.newchatbutton.setToolTip("")
            self.newchatbutton.setFixedHeight(40)
            self.newchatbutton.setMinimumWidth(0)
            self.newchatbutton.setMaximumWidth(167)

            self.sidebar_layout.setContentsMargins(14, 14, 14, 14)
            self.sidebar_layout.setSpacing(10)
            self.sidebar_layout.setAlignment(Qt.AlignTop)
            self.sidebar.setMinimumWidth(0)
            self.sidebar.setMaximumWidth(16777215)
            self.sidebar.setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Expanding
            )

            self.header_row.setSpacing(10)
            self.header_row.setAlignment(Qt.AlignVCenter)

            self.newchatbutton.setMinimumWidth(0)
            self.newchatbutton.setMaximumWidth(16777215)
            self.newchatbutton.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )
            self.newchatbutton.setFixedHeight(40)

            self.splitter.setSizes([150, self.width() - 150])

            self.sb_visibility = True

    def newchat(self):
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px;
                font-size: 50px;
            }
        """)
        self.chat_view.setText("Welcome to my AI assistant")
        self.chat_view.setAlignment(Qt.AlignCenter)

    def sendmsg(self):
        message = self.message_input.toPlainText().strip()

        if not message:
            return

        self.message_input.clear()
        
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px;
                font-size: 17px;
            }
        """)

        if self.chatid == None:
            self.chat_view.setText("")
            self.chat_view.setAlignment(Qt.AlignLeft)
    
        self.chat_view.append(
            f"\nYou:\n{message}\n \nAssistant:\n"
        )
        
        """self.chat_view.append(
            f"\nYou:\n{message}\n\nAssistant:\n"
        )"""
        self.worker = AIWorker(self.chatid, message)

        self.worker.token.connect(self.receive_ai_token)
        self.worker.chat_created.connect(self.chat_created)
        self.worker.error.connect(self.receive_ai_error)
        self.worker.finished.connect(self.ai_finished)

        self.worker.start()



    def chat_item_clicked(self, item):
        self.chat_view.setStyleSheet("""
            QTextEdit {
                background: #0b1220;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                padding: 12px;
                font-size: 17px;
            }
        """)
        chat_name = item.text()
        with open("chats/chats.json", "r") as file:
            chats = json.load(file)
            for chat in chats:
                if chat["chatName"] == chat_name:
                    self.chatid = chat["uuid"]
                    self.load_chat(self.chatid)
                    break

    def load_chat(self, uuid):
        try:
            with open(f"chats/{uuid}.json", "r", encoding="utf-8") as file:
                messages = json.load(file)
        except FileNotFoundError:
            self.chat_view.setPlainText("Chat file not found.")
            return
        except json.JSONDecodeError:
            self.chat_view.setPlainText("Invalid chat file.")
            return

        self.chat_view.clear()

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                self.chat_view.append(f"You:\n{content}\n")
            elif role == "assistant":
                self.chat_view.append(f"Assistant:\n{content}\n")
            else:
                self.chat_view.append(f"{role}:\n{content}\n")

    def receive_ai_token(self, text):
        cursor = self.chat_view.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_view.setTextCursor(cursor)

        self.chat_view.insertPlainText(text)
        self.chat_view.ensureCursorVisible()


    def chat_created(self, chatid, chat_name):
        self.chatid = chatid
        self.chat_list.insertItem(0, chat_name)


    def receive_ai_error(self, error):
        self.chat_view.append(f"\n\nFehler: {error}")


    def ai_finished(self):
        self.send_button.setEnabled(True)
        self.worker.deleteLater()

class MessageInput(QTextEdit):
    sendRequested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        # Shift + Enter: normale neue Zeile
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.insertPlainText("\n")
            else:
                self.sendRequested.emit()
        else:
            super().keyPressEvent(event)

class AIWorker(QThread):
    token = pyqtSignal(str)
    chat_created = pyqtSignal(str, str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, chatid, message):
        super().__init__()
        self.chatid = chatid
        self.message = message        

    def run(self):
        try:
            chatid = self.chatid

            if chatid is None:
                chatid = ai.newchat(self.message)

                with open("chats/chats.json", "r", encoding="utf-8") as file:
                    chats = json.load(file)

                chat_name = next(
                    chat["chatName"]
                    for chat in chats
                    if chat["uuid"] == chatid
                )

                self.chat_created.emit(chatid, chat_name)

            for text in ai.ai(chatid, self.message):
                self.token.emit(str(text))

        except Exception as error:
            self.error.emit(f"{type(error).__name__}: {error}")

        finally:
            self.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
