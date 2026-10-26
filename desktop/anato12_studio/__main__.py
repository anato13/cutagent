import sys
from PySide6.QtWidgets import QApplication
from .window import MainWindow

STYLE = """
QWidget { font-family: 'Segoe UI', 'DejaVu Sans'; font-size: 12px; color: #e7ebf2; }
QMainWindow, QWidget { background: #141820; }
QMenuBar, QMenu, QTabBar::tab { background: #1d2430; padding: 5px; }
QMenu::item:selected, QTabBar::tab:selected { background: #344253; }
QLabel#brand { font-size: 25px; font-weight: 800; color: #f3c65a; padding: 8px 0; }
QLabel#muted { color: #aeb9cb; }
QLabel#section { font-weight: 700; color: #f3c65a; padding-bottom: 12px; }
QPushButton { background: #293344; border: 1px solid #465165; border-radius: 5px; padding: 8px 10px; }
QPushButton:hover { background: #3a4860; }
QPushButton:disabled { color: #778194; background: #202733; border-color: #303846; }
QPushButton#primary { background: #f3c65a; color: #151922; font-weight: 800; padding: 13px; }
QLineEdit, QDoubleSpinBox, QComboBox { background: #0d1119; border: 1px solid #465165; border-radius: 4px; padding: 6px; }
QListWidget, QTableWidget, QGraphicsView { background: #0b0e14; border: 1px solid #303a4a; selection-background-color: #364f6b; }
QHeaderView::section { background: #242d3b; border: 0; padding: 6px; }
QSplitter::handle { background: #303846; }
QProgressBar { background: #10151d; border: 1px solid #3b4557; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #d7aa42; }
QSlider::groove:horizontal { height: 5px; background: #475268; border-radius: 2px; }
QSlider::handle:horizontal { background: #f3c65a; width: 14px; margin: -5px 0; border-radius: 7px; }
QCheckBox { spacing: 6px; }
"""


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("Anato12 Studio")
    application.setOrganizationName("Anato12")
    application.setStyle("Fusion")
    application.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
