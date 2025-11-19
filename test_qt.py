import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("环境测试窗口")
        self.setGeometry(300, 300, 400, 200)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局和控件
        layout = QVBoxLayout(central_widget)

        label = QLabel("🎉 恭喜！PySide6 环境配置成功！")
        label.setAlignment(Qt.AlignCenter)

        button = QPushButton("点击测试")
        button.clicked.connect(lambda: print("按钮工作正常！"))

        layout.addWidget(label)
        layout.addWidget(button)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("应用启动成功！")
    sys.exit(app.exec())