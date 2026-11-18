import sound_functions as sf
import ai_functions as ai
import json
import os
from pathlib import Path

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit,
    QLineEdit, QFrame, QSizePolicy, QListWidget,
    QSplitter, QFileDialog, QListWidgetItem, QMenu, QAction
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
        self.mic_state = "idle"  # idle | recording | transcribing

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
        self.chat_list.setSpacing(4)
        self.chat_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                color: #e5e7eb;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)
        self.chat_list.itemClicked.connect(self.chat_item_clicked)
        self.refresh_chat_list()
        #"Cancel"

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
        self._mic_idle_style = """
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 8px;
            }
            QPushButton:hover { background: #1d4ed8; }
        """
        self._mic_recording_style = """
            QPushButton {
                background: #dc2626;
                color: #ffffff;
                border: 1px solid #ef4444;
                border-radius: 8px;
            }
            QPushButton:hover { background: #b91c1c; }
        """
        self._mic_transcribing_style = """
            QPushButton {
                background: #2563eb;
                color: #ffffff;
                border: 1px solid #3b82f6;
                border-radius: 8px;
            }
        """
        self.mic_button.setStyleSheet(self._mic_idle_style)
        self.mic_button.clicked.connect(self.toggle_mic)

        self._mic_opacity_effect = QGraphicsOpacityEffect(self.mic_button)
        self.mic_button.setGraphicsEffect(self._mic_opacity_effect)
        self._mic_opacity_effect.setOpacity(1.0)
        self._mic_pulse_anim = QPropertyAnimation(self._mic_opacity_effect, b"opacity", self)
        self._mic_pulse_anim.setLoopCount(-1)
        self._mic_pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)

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
        self.chat_list.clearSelection()
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
        self.chat_view.clear()
        self.chat_view.setAlignment(Qt.AlignCenter)
        self.chat_view.setText("Welcome to my AI assistant")

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

    def _chats_path(self):
        return "chats/chats.json"

    def _load_chats_data(self):
        try:
            with open(self._chats_path(), "r", encoding="utf-8") as file:
                chats = json.load(file)
            if not isinstance(chats, list):
                return []
        except Exception:
            return None

        changed = False
        normalized = []
        for chat in chats:
            if not isinstance(chat, dict):
                changed = True
                continue
            if "pinned" not in chat:
                chat["pinned"] = False
                changed = True
            normalized.append(chat)

        if changed:
            try:
                self._save_chats_data(normalized)
            except Exception:
                pass
        return normalized

    def _save_chats_data(self, chats):
        path = self._chats_path()
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(chats, file, indent=4)
        os.replace(tmp_path, path)

    def _sorted_chats(self, chats):
        pinned = [c for c in chats if c.get("pinned")]
        others = [c for c in chats if not c.get("pinned")]
        return pinned + others

    def refresh_chat_list(self):
        data = self._load_chats_data()
        if data is None:
            return
        chats = self._sorted_chats(data)

        self.chat_list.clear()
        for chat in chats:
            uuid = chat.get("uuid")
            if not uuid:
                continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, uuid)
            item.setSizeHint(QSize(0, 44))
            widget = self.create_chat_item_widget(chat)
            self.chat_list.addItem(item)
            self.chat_list.setItemWidget(item, widget)
            if self.chatid and uuid == self.chatid:
                self.chat_list.setCurrentItem(item)

    def create_chat_item_widget(self, chat):
        uuid = chat.get("uuid")
        name = chat.get("chatName", "")
        pinned = chat.get("pinned", False)

        row = QFrame()
        row.setObjectName("chatRow")
        row.setStyleSheet("""
            QFrame#chatRow {
                background: transparent;
                border-radius: 8px;
            }
            QFrame#chatRow:hover {
                background: rgba(255,255,255,0.08);
            }
            QLabel { color: #e5e7eb; border: none; background: transparent; }
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); }
        """)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(6)

        pin_icon = QLabel()
        if pinned:
            pin_icon.setPixmap(svg_icon_white("icons/pin-angle.svg", QSize(14, 14)).pixmap(QSize(14, 14)))
            pin_icon.setFixedSize(16, 16)
        else:
            pin_icon.setFixedSize(0, 16)
        pin_icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(pin_icon)

        name_label = QLabel(name)
        name_label.setObjectName("chatNameLabel")
        name_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(name_label, 1)

        menu_btn = QPushButton()
        menu_btn.setIcon(svg_icon_white("icons/three-dots-vertical.svg", QSize(16, 16)))
        menu_btn.setIconSize(QSize(16, 16))
        menu_btn.setFixedSize(24, 24)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.clicked.connect(lambda _, u=uuid, b=menu_btn: self.show_chat_menu(u, b))
        layout.addWidget(menu_btn)

        row.chat_uuid = uuid
        row.name_label = name_label
        row.menu_btn = menu_btn
        row.pin_icon = pin_icon
        row.main_layout = layout
        return row

    def _find_item_by_uuid(self, uuid):
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            if item.data(Qt.UserRole) == uuid:
                return item
        return None

    def _select_chat_by_uuid(self, uuid):
        item = self._find_item_by_uuid(uuid)
        if item:
            self.chat_list.setCurrentItem(item)

    def show_chat_menu(self, uuid, button):
        chats = self._load_chats_data() or []
        chat = next((c for c in chats if c.get("uuid") == uuid), None)
        if not chat:
            return
        pinned = chat.get("pinned", False)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #111827; color: #e5e7eb; border: 1px solid rgba(255,255,255,0.12); }
            QMenu::item { padding: 6px 12px; }
            QMenu::item:selected { background: rgba(255,255,255,0.08); }
        """)
        pin_text = "Unpin" if pinned else "Pin"
        pin_action = QAction(svg_icon_white("icons/pin-angle.svg", QSize(14, 14)), pin_text, self)
        rename_action = QAction(svg_icon_white("icons/pencil-square.svg", QSize(14, 14)), "Rename", self)
        delete_action = QAction(svg_icon_white("icons/trash.svg", QSize(14, 14)), "Delete", self)

        pin_action.triggered.connect(lambda _, u=uuid: self.toggle_pin_chat(u))
        rename_action.triggered.connect(lambda _, u=uuid: self.start_rename_chat(u))
        delete_action.triggered.connect(lambda _, u=uuid: self.delete_chat(u))

        menu.addAction(pin_action)
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def toggle_pin_chat(self, uuid):
        chats = self._load_chats_data() or []
        for chat in chats:
            if chat.get("uuid") == uuid:
                chat["pinned"] = not chat.get("pinned", False)
                break
        self._save_chats_data(chats)
        self.refresh_chat_list()
        self._select_chat_by_uuid(self.chatid)

    def delete_chat(self, uuid):
        chats = self._load_chats_data() or []
        chats = [c for c in chats if c.get("uuid") != uuid]
        self._save_chats_data(chats)
        try:
            os.remove(f"chats/{uuid}.json")
        except FileNotFoundError:
            pass
        except Exception:
            pass
        if self.chatid == uuid:
            self.chatid = None
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
        self.refresh_chat_list()

    def start_rename_chat(self, uuid):
        item = self._find_item_by_uuid(uuid)
        if not item:
            return
        row = self.chat_list.itemWidget(item)
        if not row or hasattr(row, "rename_editor"):
            return

        chats = self._load_chats_data() or []
        chat = next((c for c in chats if c.get("uuid") == uuid), None)
        if not chat:
            return
        current_name = chat.get("chatName", "")

        row.name_label.hide()
        row.menu_btn.hide()

        editor = QLineEdit(current_name)
        editor.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.06);
                color: #e5e7eb;
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }
        """)

        cancel_btn = QPushButton()
        cancel_btn.setIcon(svg_icon_white("icons/x-circle.svg", QSize(18, 18)))
        cancel_btn.setIconSize(QSize(15, 15))
        cancel_btn.setFixedSize(30, 30)
        cancel_btn.setToolTip("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        
        rename_btn = QPushButton()
        rename_btn.setIcon(svg_icon_white("icons/check2-circle.svg", QSize(18, 18)))
        rename_btn.setIconSize(QSize(15,15))
        rename_btn.setFixedSize(30, 30)
        rename_btn.setToolTip("Rename")
        rename_btn.setCursor(Qt.PointingHandCursor)
        
        for b in (rename_btn, cancel_btn):
            b.setFixedHeight(28)
            b.setCursor(Qt.PointingHandCursor)
        rename_btn.setStyleSheet("""
            QPushButton { background: #2563eb; color: white; border: none; padding: 4px 8px; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background: #1d4ed8; }
        """)
        cancel_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #e5e7eb; border: 1px solid rgba(255,255,255,0.15); padding: 4px 8px; border-radius: 6px; }
            QPushButton:hover { background: rgba(255,255,255,0.08); }
        """)

        container = QWidget()
        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(6)
        c_layout.addWidget(editor, 1)
        c_layout.addWidget(cancel_btn)
        c_layout.addWidget(rename_btn)

        # insert before menu button (last widget)
        row.main_layout.insertWidget(2, container, 1)

        row.rename_editor = container

        def finish(save):
            if save:
                new_name = editor.text().strip()
                if new_name:
                    chats2 = self._load_chats_data() or []
                    for c in chats2:
                        if c.get("uuid") == uuid:
                            c["chatName"] = new_name
                            break
                    self._save_chats_data(chats2)
            row.main_layout.removeWidget(container)
            container.deleteLater()
            if hasattr(row, "rename_editor"):
                delattr(row, "rename_editor")
            row.name_label.show()
            row.menu_btn.show()
            self.refresh_chat_list()
            self._select_chat_by_uuid(self.chatid)

        rename_btn.clicked.connect(lambda: finish(True))
        cancel_btn.clicked.connect(lambda: finish(False))
        editor.returnPressed.connect(lambda: finish(True))
        editor.setFocus()

    def chat_item_clicked(self, item):
        uuid = item.data(Qt.UserRole)
        if not uuid:
            return
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
        self.chatid = uuid
        self.load_chat(uuid)

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
        self.refresh_chat_list()
        self._select_chat_by_uuid(chatid)


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
        for path in list(self.prompt_files):
            chip = QFrame()
            chip.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.08);
                    border: 1px solid rgba(255,255,255,0.12);
                    border-radius: 8px;
                }
            """)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 6, 4)
            chip_layout.setSpacing(6)

            name_label = QLabel(Path(path).name)
            name_label.setToolTip(path)
            name_label.setStyleSheet("color: #e5e7eb; font-size: 12px; border: none; background: transparent;")

            remove_btn = QPushButton()
            remove_btn.setIcon(svg_icon_white("icons/x-circle.svg", QSize(14, 14)))
            remove_btn.setIconSize(QSize(14, 14))
            remove_btn.setFixedSize(20, 20)
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.08);
                    border-radius: 10px;
                }
            """)
            remove_btn.clicked.connect(lambda _, p=path: self.remove_prompt_file(p))

            chip_layout.addWidget(name_label)
            chip_layout.addWidget(remove_btn)
            self.attachments_layout.addWidget(chip)
        self.attachments_layout.addStretch(1)

    def remove_prompt_file(self, path):
        if path in self.prompt_files:
            self.prompt_files.remove(path)
        self.refresh_attachments()

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
        

    def _start_mic_pulse(self, duration=900, min_opacity=0.35):
        self._mic_pulse_anim.stop()
        self._mic_pulse_anim.setDuration(duration)
        self._mic_pulse_anim.setKeyValueAt(0.0, 1.0)
        self._mic_pulse_anim.setKeyValueAt(0.5, min_opacity)
        self._mic_pulse_anim.setKeyValueAt(1.0, 1.0)
        self._mic_pulse_anim.start()

    def _set_mic_idle(self):
        self.mic_state = "idle"
        self._mic_pulse_anim.stop()
        self._mic_opacity_effect.setOpacity(1.0)
        self.mic_button.setEnabled(True)
        self.mic_button.setStyleSheet(self._mic_idle_style)
        self.mic_button.setToolTip("Voice input")

    def _set_mic_recording(self):
        self.mic_state = "recording"
        self.mic_button.setEnabled(True)
        self.mic_button.setStyleSheet(self._mic_recording_style)
        self.mic_button.setToolTip("Stop recording")
        self._start_mic_pulse(duration=900, min_opacity=0.35)

    def _set_mic_transcribing(self):
        self.mic_state = "transcribing"
        self.mic_button.setEnabled(False)
        self.mic_button.setStyleSheet(self._mic_transcribing_style)
        self.mic_button.setToolTip("Transcribing...")
        self._start_mic_pulse(duration=650, min_opacity=0.45)

    def toggle_mic(self):
        if self.mic_state == "idle":
            try:
                sf.sound.record()
            except Exception as error:
                self.show_toast(f"Mic error: {error}")
                self._set_mic_idle()
                return
            self._set_mic_recording()
            return

        if self.mic_state == "recording":
            try:
                file_id = sf.sound.stop()
            except Exception as error:
                self.show_toast(f"Mic error: {error}")
                self._set_mic_idle()
                return

            audio_path = os.path.join("audio", "stt", f"{file_id}.wav")
            self._set_mic_transcribing()
            self.stt_worker = STTWorker(audio_path)
            self.stt_worker.transcribed.connect(self.receive_transcription)
            self.stt_worker.error.connect(self.receive_stt_error)
            self.stt_worker.finished.connect(self.stt_finished)
            self.stt_worker.start()
            return

        # transcribing: ignore clicks while work is in progress

    def receive_transcription(self, text):
        text = (text or "").strip()
        if not text:
            self.show_toast("No speech detected")
            return

        current = self.message_input.toPlainText()
        if current and not current.endswith((" ", "\n")):
            self.message_input.insertPlainText(" " + text)
        else:
            self.message_input.insertPlainText(text)
        self.message_input.setFocus()

    def receive_stt_error(self, error):
        self.show_toast(f"Transcription error: {error}")

    def stt_finished(self):
        self._set_mic_idle()
        if hasattr(self, "stt_worker"):
            self.stt_worker.deleteLater()

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
            is_new_chat = False

            if chatid is None:
                is_new_chat = True
                chatid, chat_name = ai.newchat(self.display_content or self.message, return_name=True)
                self.chat_created.emit(chatid, chat_name)

            for text in ai.ai(chatid, self.message, files=self.files, display_content=self.display_content, is_new_chat=is_new_chat):
                self.token.emit(str(text))

        except Exception as error:
            self.error.emit(f"{type(error).__name__}: {error}")

        finally:
            self.finished.emit()


class STTWorker(QThread):
    transcribed = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        try:
            text = sf.stt(self.audio_path)
            self.transcribed.emit(text or "")
        except Exception as error:
            self.error.emit(f"{type(error).__name__}: {error}")
        finally:
            self.finished.emit()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
