import sys
import os
from PySide6.QtWidgets import QApplication
from views.splash import SplashScreen


def main():
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("Qt Robot Demo")
    app.setApplicationVersion("1.0.0")

    # 显示启动页
    splash = SplashScreen()
    splash.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()