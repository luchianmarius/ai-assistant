import sound_functions as sf
import ai_functions as ai
import json
from pathlib import Path

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit,
    QLineEdit, QFrame, QSizePolicy, QListWidget,
    QSplitter, QFileDialog
)
from PyQt5.QtGui import QIcon, QColor, QFont, QKeyEvent, QPixmap, QPainter
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal, QRectF, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QGraphicsOpacityEffect


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
        self.prompt_files = []

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
        input_layout = QVBoxLayout(input_bar)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.attachments_container = QWidget()
        self.attachments_layout = QHBoxLayout(self.attachments_container)
        self.attachments_layout.setContentsMargins(0, 0, 0, 0)
        self.attachments_layout.setSpacing(8)
        self.attachments_layout.addStretch(1)
        self.attachments_container.setVisible(False)
        input_layout.addWidget(self.attachments_container)

        self.paperclip_button = QPushButton()
        self.paperclip_button.setIcon(svg_icon_white("icons/paperclip.svg", QSize(18, 18)))
        self.paperclip_button.setIconSize(QSize(18, 18))
        self.paperclip_button.setFixedSize(40, 40)
        self.paperclip_button.setToolTip("Attach file")
        self.paperclip_button.setCursor(Qt.PointingHandCursor)
        self.paperclip_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        self.paperclip_button.clicked.connect(self.uploadFile)

        self.mic_button = QPushButton()
        self.mic_button.setIcon(svg_icon_white("icons/mic.svg", QSize(18, 18)))
        self.mic_button.setIconSize(QSize(18, 18))
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setToolTip("Voice input")
        self.mic_button.setCursor(Qt.PointingHandCursor)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        self.mic_button.clicked.connect(self.toggle_mic)

        self.message_input = MessageInput()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.sendRequested.connect(self.sendmsg)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.06);
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)

        self.send_button = QPushButton("Send")
        self.send_button.setFixedHeight(36)
        self.send_button.setStyleSheet(blue_button)
        self.send_button.clicked.connect(self.sendmsg)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        input_row.addWidget(self.message_input, 1)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)
        buttons_row.addWidget(self.paperclip_button)
        buttons_row.addWidget(self.mic_button)
        buttons_row.addStretch(1)
        buttons_row.addWidget(self.send_button, 0)

        input_layout.addLayout(input_row)
        input_layout.addLayout(buttons_row)

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
        self.chatid = None
        self.prompt_files = []
        self.refresh_attachments()
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
        original_message = self.message_input.toPlainText().strip()

        if not original_message:
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

        files = None
        model_message = original_message
        display_message = original_message

        if self.prompt_files:
            try:
                files, model_message = ai.nomic_embed_text(self.prompt_files, original_message)
            except Exception as error:
                self.show_toast(f"File error: {error}")
                return
            file_lines = "\n".join([f"[{Path(f['path']).name}]" for f in files])
            display_message = f"{file_lines}\n{original_message}" if file_lines else original_message

        self.chat_view.append(
            f"\nYou:\n{display_message}\n \nAssistant:\n"
        )
    
        self.worker = AIWorker(self.chatid, model_message, files=files, display_content=original_message)

        self.worker.token.connect(self.receive_ai_token)
        self.worker.chat_created.connect(self.chat_created)
        self.worker.error.connect(self.receive_ai_error)
        self.worker.finished.connect(self.ai_finished)

        self.worker.start()

        self.prompt_files = []
        self.refresh_attachments()

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
            files = message.get("files") or []

            if role == "user":
                if files:
                    file_lines = "\n".join([f"[{Path(f.get('path', '')).name}]" for f in files])
                    self.chat_view.append(f"You:\n{file_lines}\n{content}\n")
                else:
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

    def uploadFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file")
        if path:
            with open("supported_file_types.json", "r", encoding="utf-8") as file:
                supported_ft = json.load(file)

            if Path(path).suffix.lower() in supported_ft:
                if path not in self.prompt_files:
                    self.prompt_files.append(path)
                    self.refresh_attachments()
            else:
                self.show_toast("File type not supported")

    def refresh_attachments(self):
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self.prompt_files:
            self.attachments_container.setVisible(False)
            return

        self.attachments_container.setVisible(True)
        for path in self.prompt_files:
            name = Path(path).name
            chip = QLabel(name)
            chip.setToolTip(path)
            chip.setStyleSheet("""
                QLabel {
                    background: rgba(255,255,255,0.08);
                    color: #e5e7eb;
                    border: 1px solid rgba(255,255,255,0.12);
                    border-radius: 8px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
            """)
            self.attachments_layout.addWidget(chip)
        self.attachments_layout.addStretch(1)

    def show_toast(self, message, duration=1500):
        toast = QLabel(message, self)
        toast.setStyleSheet("""
            QLabel {
                background: #dc2626;
                color: white;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
        """)
        toast.setAlignment(Qt.AlignCenter)
        toast.adjustSize()

        margin_bottom = 120
        x = (self.width() - toast.width()) // 2
        y = self.height() - toast.height() - margin_bottom
        toast.move(max(12, x), max(12, y))
        toast.show()
        toast.raise_()

        effect = QGraphicsOpacityEffect(toast)
        toast.setGraphicsEffect(effect)
        effect.setOpacity(1.0)

        fade = QPropertyAnimation(effect, b"opacity", self)
        fade.setDuration(500)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)

        def start_fade():
            fade.start()

        fade.finished.connect(toast.deleteLater)
        QTimer.singleShot(duration, start_fade)

        if not hasattr(self, "_toasts"):
            self._toasts = []
        self._toasts.append((toast, fade, effect))
        

    def toggle_mic(self):
        print("Mic button clicked")

class MessageInput(QTextEdit):
    sendRequested = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._min_height = 36
        self._max_height = 150
        self.setMinimumHeight(self._min_height)
        self.setMaximumHeight(self._max_height)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.document().documentLayout().documentSizeChanged.connect(self.adjust_height)
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()

    def adjust_height(self):
        doc_height = self.document().size().height()
        margins = self.contentsMargins()
        height = int(doc_height + margins.top() + margins.bottom() + self.frameWidth() * 2)
        height = max(self._min_height, min(height, self._max_height))
        self.setFixedHeight(height)

        if self.document().size().height() + margins.top() + margins.bottom() + self.frameWidth() * 2 > self._max_height:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

    def __init__(self, chatid, message, files=None, display_content=None):
        super().__init__()
        self.chatid = chatid
        self.message = message
        self.files = files
        self.display_content = display_content

    def run(self):
        try:
            chatid = self.chatid

            if chatid is None:
                chatid = ai.newchat(self.display_content or self.message)

                with open("chats/chats.json", "r", encoding="utf-8") as file:
                    chats = json.load(file)

                chat_name = next(
                    chat["chatName"]
                    for chat in chats
                    if chat["uuid"] == chatid
                )

                self.chat_created.emit(chatid, chat_name)

            for text in ai.ai(chatid, self.message, files=self.files, display_content=self.display_content):
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
