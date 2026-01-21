"""
保持旧入口名，但转向模块化实现，方便逐步扩展。
"""

import sys
from PySide6.QtWidgets import QApplication

from ui_main_window import EzMapWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = EzMapWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()