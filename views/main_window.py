import os
import sys
import psutil
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QPushButton, QLabel, QStackedWidget,
                               QMessageBox, QApplication)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPixmap, QCursor, QMouseEvent


class DraggableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt Robot Demo")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 600)

        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        # 窗口控制变量
        self.is_dragging = False
        self.drag_start_position = QPoint()
        self.is_resizing = False
        self.resize_direction = None
        self.resize_start_position = QPoint()
        self.resize_start_geometry = QRect()
        self.border_width = 8

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            self.resize_direction = self.get_resize_direction(pos)

            if self.resize_direction:
                self.is_resizing = True
                self.resize_start_position = event.globalPosition().toPoint()
                self.resize_start_geometry = self.geometry()
            elif pos.y() <= 40:  # 标题栏高度
                self.is_dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()

        if not self.is_dragging and not self.is_resizing:
            direction = self.get_resize_direction(pos)
            self.update_cursor(direction)

        if self.is_dragging:
            self.move(global_pos - self.drag_start_position)
        elif self.is_resizing and self.resize_direction:
            self.handle_resize(global_pos)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.is_resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    def get_resize_direction(self, pos):
        x, y = pos.x(), pos.y()
        width, height = self.width(), self.height()
        margin = self.border_width

        left = x <= margin
        right = x >= width - margin
        top = y <= margin
        bottom = y >= height - margin

        if left and top:
            return "top_left"
        elif right and top:
            return "top_right"
        elif left and bottom:
            return "bottom_left"
        elif right and bottom:
            return "bottom_right"
        elif left:
            return "left"
        elif right:
            return "right"
        elif top:
            return "top"
        elif bottom:
            return "bottom"
        else:
            return None

    def update_cursor(self, direction):
        cursor_map = {
            "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
            "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor,
            "top_left": Qt.SizeFDiagCursor, "top_right": Qt.SizeBDiagCursor,
            "bottom_left": Qt.SizeBDiagCursor, "bottom_right": Qt.SizeFDiagCursor,
        }
        self.setCursor(cursor_map.get(direction, Qt.ArrowCursor))

    def handle_resize(self, global_pos):
        if not self.resize_start_geometry:
            return

        start_geo = self.resize_start_geometry
        delta = global_pos - self.resize_start_position
        new_geo = QRect(start_geo)
        min_width, min_height = self.minimumWidth(), self.minimumHeight()

        if "left" in self.resize_direction:
            new_width = max(min_width, start_geo.width() - delta.x())
            new_geo.setX(start_geo.x() + (start_geo.width() - new_width))
            new_geo.setWidth(new_width)
        if "right" in self.resize_direction:
            new_geo.setWidth(max(min_width, start_geo.width() + delta.x()))
        if "top" in self.resize_direction:
            new_height = max(min_height, start_geo.height() - delta.y())
            new_geo.setY(start_geo.y() + (start_geo.height() - new_height))
            new_geo.setHeight(new_height)
        if "bottom" in self.resize_direction:
            new_geo.setHeight(max(min_height, start_geo.height() + delta.y()))

        self.setGeometry(new_geo)


class MainWindow:
    def __init__(self):
        # 获取进程信息用于监控
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)
        self.cpu_readings = []

        # 创建可拖拽的主窗口
        self.ui = DraggableWindow()

        # 创建中央部件
        central_widget = QWidget()
        central_widget.setMouseTracking(True)
        self.ui.setCentralWidget(central_widget)

        # 主布局：标题栏 + 内容区域
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 自定义标题栏（带监控）
        self.setup_title_bar(main_layout)

        # 内容区域：2行 (15% | 85%)
        content_widget = QWidget()
        content_widget.setMouseTracking(True)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 第一行：15% 高度
        self.setup_row1(content_layout)

        # 第二行：85% 高度
        self.setup_row2(content_layout)

        # 设置内容区域的拉伸因子
        content_layout.setStretch(0, 15)  # 第一行 15%
        content_layout.setStretch(1, 85)  # 第二行 85%

        main_layout.addWidget(content_widget)

        # 连接信号槽
        self.setup_connections()

        # 启动监控定时器
        self.setup_monitor()

        # 窗口居中
        self.center_on_screen()

    def setup_main_content(self, left_layout):
        """主内容区域 - 可替换的组件容器"""
        # 创建堆叠窗口用于组件切换
        self.main_content = QStackedWidget()
        self.main_content.setMouseTracking(True)
        self.main_content.setContentsMargins(0, 0, 0, 0)

        # 创建默认主页（后续可以替换为其他组件）
        self.setup_home_page()

        # 设置主页为默认显示
        self.main_content.setCurrentIndex(0)
        self.original_content = self.main_content.currentWidget()

        left_layout.addWidget(self.main_content)

    def setup_home_page(self):
        """设置主页内容 - 后续可以替换为其他组件"""
        home_page = QWidget()
        home_page.setMouseTracking(True)
        home_layout = QGridLayout(home_page)
        home_layout.setSpacing(8)
        home_layout.setContentsMargins(0, 0, 0, 0)

        # 功能按钮文本
        button_texts = [
            ["用户登录", "工程管理", "程序编辑", "程序数据", "IO检测"],
            ["点动管理", "日志管理", "通用设置", "高级设置", "用户应用"],
            ["机器人点位", "用户坐标系", "工具坐标系", "状态监视", "机械臂"]
        ]

        # 创建3x5的按钮网格
        for row in range(3):
            for col in range(5):
                button = QPushButton()
                button.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #E0E0E0;
                        border-radius: 8px;
                        background: white;
                    }
                    QPushButton:hover {
                        background: #f0f0f0;
                    }
                """)
                button.setFixedSize(120, 120)
                button.setMouseTracking(True)

                button_layout = QVBoxLayout(button)

                # 图标
                icon = QLabel("📱")
                icon.setAlignment(Qt.AlignCenter)
                icon.setStyleSheet("font-size: 32px; margin-bottom: 8px;")
                icon.setMouseTracking(True)
                button_layout.addWidget(icon)

                # 文字
                text = QLabel(button_texts[row][col])
                text.setAlignment(Qt.AlignCenter)
                text.setStyleSheet("font-size: 12px; font-weight: bold; color: #333333;")
                text.setMouseTracking(True)
                button_layout.addWidget(text)

                # 连接点击事件
                if row == 1 and col == 0:  # 工程管理按钮
                    button.clicked.connect(self.setting_click)
                elif row == 2 and col == 4:  # 机械臂按钮
                    button.clicked.connect(self.robot_click)
                else:
                    button.clicked.connect(self.code_click)

                home_layout.addWidget(button, row, col)

        # 添加到堆叠窗口
        self.main_content.addWidget(home_page)

    def switch_to_component(self, component):
        """切换到指定组件"""
        # 移除当前所有组件
        while self.main_content.count() > 0:
            widget = self.main_content.widget(0)
            self.main_content.removeWidget(widget)
            widget.deleteLater()

        # 添加新组件
        self.main_content.addWidget(component)
        self.main_content.setCurrentWidget(component)

    def switch_to_page(self, page_index):
        """切换到指定页面（备用方法）"""
        if 0 <= page_index < self.main_content.count():
            self.main_content.setCurrentIndex(page_index)

    def home_click(self):
        """返回主页"""
        print("homeClick - 返回主页")
        # 这里可以重新设置主页内容
        self.setup_home_page()
        self.switch_to_page(0)

    def tree_click(self):
        """跳转到树形页面"""
        print("treeClick - 跳转到树形页面")
        # 后续可以在这里切换到树形组件
        # from .tree_component import TreeComponent
        # tree_component = TreeComponent()
        # self.switch_to_component(tree_component)

    def code_click(self):
        """跳转到代码页面"""
        print("codeClick - 跳转到代码页面")
        # 后续可以在这里切换到代码组件

    def setting_click(self):
        """跳转到设置页面"""
        print("settingClick - 跳转到设置页面")
        # 后续可以在这里切换到设置组件

    def robot_click(self):
        """跳转到机械臂页面"""
        print("robotClick - 跳转到机械臂页面")
        # 后续可以在这里切换到机械臂组件

    # 其他方法保持不变...
    def setup_title_bar(self, main_layout):
        """自定义标题栏，包含监控信息"""
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
                border: none;
            }
        """)
        self.title_bar.setMouseTracking(True)

        layout = QHBoxLayout(self.title_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(20)

        # 应用标题
        title_label = QLabel("🚀 Qt Robot Demo")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        title_label.setMouseTracking(True)

        # 监控信息区域
        monitor_widget = QWidget()
        monitor_widget.setMouseTracking(True)
        monitor_layout = QHBoxLayout(monitor_widget)
        monitor_layout.setSpacing(15)

        # CPU 监控
        self.cpu_monitor = QLabel("CPU: --%")
        self.cpu_monitor.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                background-color: #34495e;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        self.cpu_monitor.setMouseTracking(True)

        # 内存监控
        self.memory_monitor = QLabel("内存: -- MB")
        self.memory_monitor.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                background-color: #34495e;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        self.memory_monitor.setMouseTracking(True)

        monitor_layout.addWidget(self.cpu_monitor)
        monitor_layout.addWidget(self.memory_monitor)
        monitor_layout.addStretch()

        # 窗口控制按钮
        control_widget = QWidget()
        control_widget.setMouseTracking(True)
        control_layout = QHBoxLayout(control_widget)
        control_layout.setSpacing(5)

        btn_minimize = QPushButton("−")
        btn_minimize.setFixedSize(20, 20)
        btn_minimize.clicked.connect(self.ui.showMinimized)
        btn_minimize.setMouseTracking(True)

        btn_close = QPushButton("×")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self.ui.close)
        btn_close.setMouseTracking(True)

        button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid #5a6c7d;
                border-radius: 2px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6c7d;
            }
        """
        btn_minimize.setStyleSheet(button_style)
        btn_close.setStyleSheet(button_style)

        control_layout.addWidget(btn_minimize)
        control_layout.addWidget(btn_close)

        # 添加到标题栏
        layout.addWidget(title_label)
        layout.addWidget(monitor_widget)
        layout.addStretch()
        layout.addWidget(control_widget)

        main_layout.addWidget(self.title_bar)

    def setup_monitor(self):
        """设置资源监控"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor)
        self.monitor_timer.start(1000)

    def update_monitor(self):
        """更新标题栏监控信息"""
        try:
            current_cpu = self.process.cpu_percent()
            self.cpu_readings.append(current_cpu)
            if len(self.cpu_readings) > 3:
                self.cpu_readings.pop(0)
            cpu_percent = sum(self.cpu_readings) / len(self.cpu_readings)

            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)

            self.cpu_monitor.setText(f"CPU: {cpu_percent:.1f}%")
            self.memory_monitor.setText(f"内存: {memory_mb:.1f} MB")

            self.update_monitor_color(self.cpu_monitor, cpu_percent)
            self.update_monitor_color(self.memory_monitor, memory_mb / 100)

        except Exception as e:
            print(f"监控更新错误: {e}")

    def update_monitor_color(self, label, value):
        if value < 50:
            color = "#2ecc71"
        elif value < 80:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        new_style = f"""
            QLabel {{
                color: #ecf0f1;
                background-color: {color};
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
            }}
        """
        label.setStyleSheet(new_style)

    def center_on_screen(self):
        screen_geometry = self.ui.screen().availableGeometry()
        x = (screen_geometry.width() - self.ui.width()) // 2
        y = (screen_geometry.height() - self.ui.height()) // 2
        self.ui.move(x, y)

    def setup_row1(self, main_layout):
        """第一行：左10% | 中80% | 右10%"""
        row1_widget = QWidget()
        row1_widget.setMouseTracking(True)
        row1_layout = QHBoxLayout(row1_widget)
        row1_layout.setSpacing(0)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧 10%
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_widget.setMouseTracking(True)
        left_layout = QVBoxLayout(left_widget)

        self.home_button = QPushButton()
        self.home_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.home_button.setFixedSize(100, 100)
        self.home_button.setMouseTracking(True)

        home_layout = QVBoxLayout(self.home_button)
        home_icon = QLabel("🏠")
        home_icon.setAlignment(Qt.AlignCenter)
        home_icon.setStyleSheet("font-size: 40px;")
        home_icon.setMouseTracking(True)
        home_layout.addWidget(home_icon)

        left_layout.addWidget(self.home_button, alignment=Qt.AlignCenter)
        row1_layout.addWidget(left_widget)

        # 中间 80%
        middle_widget = QWidget()
        middle_widget.setStyleSheet("background: lightgreen;")
        middle_widget.setMouseTracking(True)
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setSpacing(0)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        self.setup_top_modules(middle_layout)
        self.setup_bottom_modules(middle_layout)

        middle_layout.setStretch(0, 50)
        middle_layout.setStretch(1, 50)
        row1_layout.addWidget(middle_widget)

        # 右侧 10%
        right_widget = QLabel("右侧 10%")
        right_widget.setStyleSheet("background: purple; color: white; font-size: 16px;")
        right_widget.setAlignment(Qt.AlignCenter)
        right_widget.setMouseTracking(True)
        row1_layout.addWidget(right_widget)

        row1_layout.setStretch(0, 10)
        row1_layout.setStretch(1, 80)
        row1_layout.setStretch(2, 10)
        main_layout.addWidget(row1_widget)

    def setup_top_modules(self, middle_layout):
        """中间上半部分：15个小模块"""
        top_widget = QWidget()
        top_widget.setMouseTracking(True)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 模块1
        module1 = QWidget()
        module1.setStyleSheet("background: lightcyan;")
        module1.setMouseTracking(True)
        module1_layout = QVBoxLayout(module1)

        self.module1_icon = QLabel("📱")
        self.module1_icon.setAlignment(Qt.AlignCenter)
        self.module1_icon.setStyleSheet("font-size: 20px;")
        self.module1_icon.mousePressEvent = self.pc_click
        self.module1_icon.setMouseTracking(True)

        self.module1_text = QLabel("按钮")
        self.module1_text.setAlignment(Qt.AlignCenter)
        self.module1_text.setStyleSheet("font-size: 10px;")
        self.module1_text.setMouseTracking(True)

        module1_layout.addWidget(self.module1_icon)
        module1_layout.addWidget(self.module1_text)
        top_layout.addWidget(module1)

        # 模块2
        module2 = QLabel("2")
        module2.setStyleSheet("background: lightyellow; font-size: 10px;")
        module2.setAlignment(Qt.AlignCenter)
        module2.setMouseTracking(True)
        top_layout.addWidget(module2)

        # 模块3 (Tree按钮)
        self.tree_button = QPushButton("Tree")
        self.tree_button.setStyleSheet("""
            QPushButton {
                background: lightsalmon;
                border: none;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #e9967a;
            }
        """)
        self.tree_button.setMouseTracking(True)
        top_layout.addWidget(self.tree_button)

        # 其他模块...
        modules_data = [
            ("4", "mistyrose"), ("5", "lavender"), ("6", "honeydew"),
            ("7", "lightblue"), ("8", "pink"), ("9", "khaki"),
            ("10", "palegreen"), ("11", "thistle"), ("12", "tan"),
            ("NullTool", "wheat"), ("World", "plum")
        ]

        for text, color in modules_data:
            module = QLabel(text)
            module.setStyleSheet(f"background: {color}; font-size: 10px;")
            module.setAlignment(Qt.AlignCenter)
            module.setMouseTracking(True)
            top_layout.addWidget(module)

        # 模块15 (对话框按钮)
        self.dialog_button = QPushButton()
        self.dialog_button.setStyleSheet("""
            QPushButton {
                background: lightgoldenrodyellow;
                border: none;
            }
            QPushButton:hover {
                background: #fafad2;
            }
        """)
        self.dialog_button.setMouseTracking(True)

        dialog_icon = QLabel("💬")
        dialog_icon.setAlignment(Qt.AlignCenter)
        dialog_icon.setStyleSheet("font-size: 20px;")
        dialog_icon.setMouseTracking(True)

        dialog_layout = QVBoxLayout(self.dialog_button)
        dialog_layout.addWidget(dialog_icon)
        top_layout.addWidget(self.dialog_button)

        stretches = [1, 1.5, 1, 1, 1, 1, 1, 1, 1.5, 1.5, 2, 1.5, 2, 2, 1]
        for i, stretch in enumerate(stretches):
            top_layout.setStretch(i, int(stretch * 10))

        middle_layout.addWidget(top_widget)

    def setup_bottom_modules(self, middle_layout):
        """中间下半部分：左85% | 右15%"""
        bottom_widget = QWidget()
        bottom_widget.setMouseTracking(True)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setSpacing(0)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        left_bottom = QLabel("预警信息")
        left_bottom.setStyleSheet("background: orange; font-size: 14px;")
        left_bottom.setAlignment(Qt.AlignCenter)
        left_bottom.setMouseTracking(True)
        bottom_layout.addWidget(left_bottom)

        right_bottom = QLabel("右模块 (15%)")
        right_bottom.setStyleSheet("background: lightcoral; font-size: 14px;")
        right_bottom.setAlignment(Qt.AlignCenter)
        right_bottom.setMouseTracking(True)
        bottom_layout.addWidget(right_bottom)

        bottom_layout.setStretch(0, 85)
        bottom_layout.setStretch(1, 15)
        middle_layout.addWidget(bottom_widget)

    def setup_row2(self, main_layout):
        """第二行：左95% | 右5%"""
        row2_widget = QWidget()
        row2_widget.setMouseTracking(True)
        row2_layout = QHBoxLayout(row2_widget)
        row2_layout.setSpacing(0)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧 95%
        left_widget = QWidget()
        left_widget.setMouseTracking(True)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 主内容区域 (85%)
        self.setup_main_content(left_layout)

        # 中间行 (5%)
        self.setup_middle_row(left_layout)

        # 底行 (10%)
        self.setup_bottom_row(left_layout)

        left_layout.setStretch(0, 85)
        left_layout.setStretch(1, 5)
        left_layout.setStretch(2, 10)
        row2_layout.addWidget(left_widget)

        # 右侧 5%
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_widget.setMouseTracking(True)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(1, 7):
            module = QLabel(f"模块 {i}")
            colors = ["yellow", "lightgreen", "lightblue", "wheat", "khaki", "plum"]
            module.setStyleSheet(f"background: {colors[i - 1]}; font-size: 10px;")
            module.setAlignment(Qt.AlignCenter)
            module.setMouseTracking(True)
            right_layout.addWidget(module)

        row2_layout.addWidget(right_widget)
        row2_layout.setStretch(0, 95)
        row2_layout.setStretch(1, 5)
        main_layout.addWidget(row2_widget)

    def setup_middle_row(self, left_layout):
        """中间行：3个模块"""
        middle_widget = QWidget()
        middle_widget.setMouseTracking(True)
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setSpacing(0)
        middle_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(1, 4):
            module = QLabel(f"模块 2-{i}")
            colors = ["orange", "lightcoral", "gold"]
            module.setStyleSheet(f"background: {colors[i - 1]}; font-size: 10px;")
            module.setAlignment(Qt.AlignCenter)
            module.setMouseTracking(True)
            middle_layout.addWidget(module)

        left_layout.addWidget(middle_widget)

    def setup_bottom_row(self, left_layout):
        """底行：7个模块"""
        bottom_widget = QWidget()
        bottom_widget.setMouseTracking(True)
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setSpacing(0)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(1, 8):
            module = QLabel(f"模块 3-{i}")
            colors = ["lightgreen", "lightskyblue", "mistyrose", "lavender", "honeydew", "khaki", "lightskyblue"]
            module.setStyleSheet(f"background: {colors[i - 1]}; font-size: 10px;")
            module.setAlignment(Qt.AlignCenter)
            module.setMouseTracking(True)
            bottom_layout.addWidget(module)

        left_layout.addWidget(bottom_widget)

    def setup_connections(self):
        """连接信号槽"""
        self.home_button.clicked.connect(self.home_click)
        self.tree_button.clicked.connect(self.tree_click)
        self.dialog_button.clicked.connect(self.show_custom_dialog)
        self.is_clicked = False

    def pc_click(self, event):
        """PC按钮点击事件"""
        if self.is_clicked:
            self.module1_text.setText("按钮")
        else:
            self.module1_text.setText("已点击")
        self.is_clicked = not self.is_clicked

    def show_custom_dialog(self):
        """显示自定义对话框"""
        print("显示确认对话框")
        reply = QMessageBox.question(self.ui, '确认跳转', '确认要跳转到操作页吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print("跳转到操作页")
            QMessageBox.information(self.ui, "提示", "跳转到操作页")

    def show(self):
        """显示窗口"""
        self.ui.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())