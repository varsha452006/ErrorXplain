"""
main.py
-------
Entry point for ErrorXplain Desktop Application (Member 1 - Desktop UI).

Usage:
    python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from core.api_engine import ApiRuleEngine
from ui.main_window import MainWindow


def main():
    # Enable High-DPI display scaling if supported
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ErrorXplain")
    app.setOrganizationName("ErrorXplain Team")

    # Initialize the rule engine (composition root) and inject into MainWindow
    engine = ApiRuleEngine()
    window = MainWindow(engine=engine)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
