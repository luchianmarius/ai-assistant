#you need to execute this file using the following command:
#QT_QPA_PLATFORM=wayland python3 index.py
#I'm on debian + sway (window manager), thats why it doesnt work on my computer if I just execute it normally

import main_functions as mf
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ai_assistant")
        self.setGeometry(700, 100, 1000, 1000)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

