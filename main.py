from PySide6.QtWidgets import QApplication
import sys
from gui.main_window import LaserSpotAnalyzer

app = QApplication(sys.argv)
w = LaserSpotAnalyzer()
w.show()
sys.exit(app.exec())
