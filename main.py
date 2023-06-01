from PySide6.QtWidgets import QApplication
import sys
from obb_tree.gui.gui import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
