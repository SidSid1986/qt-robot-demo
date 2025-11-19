import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import QTimer, Qt, Property
from PySide6.QtGui import QFont


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # 移除了系统默认的标题栏
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1200, 700)

        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """创建启动页界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)

        # 主容器 - 设置对象名，这样样式只会应用到这个容器
        container = QWidget()
        container.setObjectName("mainContainer")  # 设置对象名
        container.setFixedSize(800, 600)
        container.setStyleSheet("""
             QWidget#mainContainer {
                 background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #667eea, stop: 1 #764ba2);
                 border-radius: 20px;
             }
         """)

        # 容器布局
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(25)
        container_layout.setContentsMargins(40, 40, 40, 40)

        # Logo 和文字作为一个整体 - 这个widget不会有背景色
        logo_text_widget = QWidget()
        logo_text_layout = QVBoxLayout(logo_text_widget)
        logo_text_layout.setSpacing(15)
        logo_text_layout.setAlignment(Qt.AlignCenter)
        logo_text_layout.setContentsMargins(0, 0, 0, 0)

        # Logo 区域
        logo_container = QWidget()
        logo_container.setFixedSize(80, 80)
        logo_container.setStyleSheet("""
             QWidget {
                 background-color: white;
                 border-radius: 40px;
             }
         """)

        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        logo = QLabel("🚀")
        logo.setStyleSheet("""
             QLabel {
                 font-size: 40px;
                 background: transparent;
             }
         """)
        logo.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo)

        # 应用信息
        app_info_widget = QWidget()
        app_info_layout = QVBoxLayout(app_info_widget)
        app_info_layout.setSpacing(5)
        app_info_layout.setAlignment(Qt.AlignCenter)
        app_info_layout.setContentsMargins(0, 0, 0, 0)

        app_name = QLabel("Qt Robot Demo")
        app_name.setStyleSheet("""
             QLabel {
                 font-size: 28px;
                 font-weight: bold;
                 color: white;
                 background: transparent;
             }
         """)
        app_name.setAlignment(Qt.AlignCenter)

        app_desc = QLabel("跨平台桌面应用")
        app_desc.setStyleSheet("""
             QLabel {
                 font-size: 14px;
                 color: #E0E0E0;
                 background: transparent;
             }
         """)
        app_desc.setAlignment(Qt.AlignCenter)

        app_info_layout.addWidget(app_name)
        app_info_layout.addWidget(app_desc)

        # 将 Logo 和文字信息添加到整体布局
        logo_text_layout.addWidget(logo_container, alignment=Qt.AlignCenter)
        logo_text_layout.addWidget(app_info_widget, alignment=Qt.AlignCenter)

        # 加载指示器
        loading_layout = QVBoxLayout()
        loading_layout.setSpacing(15)
        loading_layout.setAlignment(Qt.AlignCenter)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(150, 6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setStyleSheet("""
             QProgressBar {
                 border: none;
                 background-color: rgba(255, 255, 255, 0.3);
                 border-radius: 3px;
             }
             QProgressBar::chunk {
                 background-color: white;
                 border-radius: 3px;
             }
         """)

        self.progress_text = QLabel("正在初始化应用...")
        self.progress_text.setStyleSheet("""
             QLabel {
                 font-size: 12px;
                 color: white;
                 background: transparent;
             }
         """)
        self.progress_text.setAlignment(Qt.AlignCenter)

        loading_layout.addWidget(self.progress_bar)
        loading_layout.addWidget(self.progress_text)

        # 版本信息
        version = QLabel("Version 1.0.0")
        version.setStyleSheet("""
             QLabel {
                 font-size: 10px;
                 color: #C0C0C0;
                 background: transparent;
             }
         """)
        version.setAlignment(Qt.AlignCenter)

        # 添加到容器
        container_layout.addWidget(logo_text_widget, alignment=Qt.AlignCenter)
        container_layout.addLayout(loading_layout)
        container_layout.addWidget(version)

        # 添加到主布局
        main_layout.addWidget(container)

        # 设置窗口居中
        self.center_on_screen()

    def center_on_screen(self):
        """窗口居中显示"""
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def setup_animation(self):
        """设置启动动画"""
        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(80)  # 稍微快一点

    def update_progress(self):
        """更新启动进度"""
        self.progress_value += 5

        # 更新状态文本
        if self.progress_value < 25:
            self.progress_text.setText("正在初始化应用...")
        elif self.progress_value < 50:
            self.progress_text.setText("加载核心模块...")
        elif self.progress_value < 75:
            self.progress_text.setText("准备界面组件...")
        else:
            self.progress_text.setText("启动完成！")

        # 进度完成时关闭启动页并打开主窗口
        if self.progress_value >= 100:
            self.timer.stop()
            # 添加一个短暂的延迟，"启动完成"
            QTimer.singleShot(300, self.open_main_window)

    def open_main_window(self):
        """打开主窗口"""
        from views.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

    def mousePressEvent(self, event):
        """支持拖动窗口"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """支持拖动窗口"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_start_position'):
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
