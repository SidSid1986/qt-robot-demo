import sys
import psutil
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QWidget, QLabel, QProgressBar, QHBoxLayout,
                               QPushButton, QTextEdit, QGridLayout)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont


class ResourceMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.pid = os.getpid()  # 获取当前进程ID
        self.process = psutil.Process(self.pid)
        self.cpu_readings = []  # 存储CPU读数用于平滑
        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        title = QLabel("📊 实时资源监控")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 15px;")
        layout.addWidget(title)

        # 进程信息
        self.process_label = QLabel()
        self.process_label.setFont(QFont("Segoe UI", 9))
        self.process_label.setStyleSheet("color: #7f8c8d; background-color: #ecf0f1; padding: 8px; border-radius: 5px;")
        self.process_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.process_label)

        # 创建网格布局来组织监控项
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # CPU 监控
        cpu_title = QLabel("💻 CPU 使用率")
        cpu_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        grid_layout.addWidget(cpu_title, 0, 0)

        self.cpu_label = QLabel("0.0%")
        self.cpu_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        grid_layout.addWidget(self.cpu_label, 0, 1)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setMinimumHeight(25)
        grid_layout.addWidget(self.cpu_bar, 1, 0, 1, 2)

        # 内存监控
        memory_title = QLabel("🧠 内存使用")
        memory_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        grid_layout.addWidget(memory_title, 2, 0)

        self.memory_label = QLabel("0.0 MB")
        self.memory_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        grid_layout.addWidget(self.memory_label, 2, 1)

        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(100)
        self.memory_bar.setMinimumHeight(25)
        grid_layout.addWidget(self.memory_bar, 3, 0, 1, 2)

        # 系统信息
        system_title = QLabel("🖥️ 系统信息")
        system_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        grid_layout.addWidget(system_title, 4, 0)

        self.system_label = QLabel("正在加载...")
        self.system_label.setFont(QFont("Segoe UI", 9))
        self.system_label.setWordWrap(True)
        grid_layout.addWidget(self.system_label, 4, 1)

        layout.addLayout(grid_layout)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
            }
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                border-radius: 6px;
            }
        """)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)  # 每秒更新

    def update_stats(self):
        try:
            # 获取当前进程的CPU使用率（平滑处理）
            current_cpu = self.process.cpu_percent()
            self.cpu_readings.append(current_cpu)
            if len(self.cpu_readings) > 3:  # 保持最近3个读数
                self.cpu_readings.pop(0)
            cpu_percent = sum(self.cpu_readings) / len(self.cpu_readings)

            # 获取当前进程的内存使用
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # 转换为MB

            # 获取系统总内存用于百分比计算
            system_memory = psutil.virtual_memory()
            memory_percent = (memory_info.rss / system_memory.total) * 100

            # 获取系统CPU信息
            system_cpu = psutil.cpu_percent(interval=None)

            # 更新界面
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            self.cpu_bar.setValue(int(cpu_percent))

            self.memory_label.setText(f"{memory_mb:.1f} MB")
            self.memory_bar.setValue(int(memory_percent))

            # 更新进程信息
            self.process_label.setText(
                f"进程ID: {self.pid} | "
                f"线程数: {self.process.num_threads()} | "
                f"状态: {self.process.status().capitalize()}"
            )

            # 更新系统信息
            self.system_label.setText(
                f"系统CPU: {system_cpu:.1f}% | "
                f"总内存: {system_memory.total / (1024 ** 3):.1f} GB"
            )

            # 根据使用率改变颜色
            self.update_bar_color(self.cpu_bar, cpu_percent)
            self.update_bar_color(self.memory_bar, memory_percent)

        except Exception as e:
            print(f"监控更新错误: {e}")

    def update_bar_color(self, bar, percent):
        """根据百分比改变进度条颜色"""
        if percent < 50:
            color = "#2ecc71"  # 绿色
        elif percent < 80:
            color = "#f39c12"  # 橙色
        else:
            color = "#e74c3c"  # 红色

        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)


class DemoApplication(QWidget):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.log_text = None  # 先初始化为 None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🚀 我的 Qt 桌面应用")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        layout.addWidget(title)

        # 说明文本
        description = QLabel(
            "这是一个带资源监控的 Qt 桌面应用演示。\n"
            "右侧面板实时显示当前应用的 CPU 和内存使用情况。"
        )
        description.setFont(QFont("Segoe UI", 11))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #7f8c8d; margin-bottom: 20px;")
        layout.addWidget(description)

        # 模拟一些控件
        self.add_demo_controls(layout)

        # 日志区域
        log_title = QLabel("📝 操作日志")
        log_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setPlaceholderText("操作日志将显示在这里...")
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.log_text)

        self.log_message("应用启动成功")
        self.log_message("监控面板已激活")

    def add_demo_controls(self, layout):
        """添加一些演示控件来模拟真实应用"""
        # 按钮组
        button_layout = QHBoxLayout()

        btn1 = QPushButton("🔧 执行轻量任务")
        btn1.clicked.connect(lambda: self.simulate_work("轻量任务", 500000))
        btn1.setStyleSheet(self.get_button_style("#3498db"))

        btn2 = QPushButton("⚡ 执行重量任务")
        btn2.clicked.connect(lambda: self.simulate_work("重量任务", 5000000))
        btn2.setStyleSheet(self.get_button_style("#e74c3c"))

        btn3 = QPushButton("📊 添加日志")
        btn3.clicked.connect(self.add_log_entry)
        btn3.setStyleSheet(self.get_button_style("#2ecc71"))

        btn4 = QPushButton("🗑️ 清空日志")
        btn4.clicked.connect(self.clear_log)
        btn4.setStyleSheet(self.get_button_style("#95a5a6"))

        button_layout.addWidget(btn1)
        button_layout.addWidget(btn2)
        button_layout.addWidget(btn3)
        button_layout.addWidget(btn4)
        layout.addLayout(button_layout)

    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color};
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: {color};
                opacity: 0.8;
            }}
        """

    def clear_log(self):
        """清空日志"""
        if self.log_text:
            self.log_text.clear()
            self.log_message("日志已清空")

    def simulate_work(self, task_name, iterations):
        """模拟一些工作来测试资源监控"""
        self.log_message(f"开始执行 {task_name}...")

        # 模拟一些CPU工作
        result = 0
        for i in range(iterations):
            result += i * i

        self.log_message(f"✅ {task_name} 完成 (结果: {result % 1000})")

    def add_log_entry(self):
        """添加测试日志"""
        self.counter += 1
        self.log_message(f"测试日志条目 #{self.counter}")

    def log_message(self, message):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if self.log_text:
            self.log_text.append(f"[{timestamp}] {message}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Qt 桌面应用 - 实时资源监控")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 左右分栏
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 左侧 - 应用内容 (70% 宽度)
        left_widget = DemoApplication()
        main_layout.addWidget(left_widget, 7)  # 7份宽度

        # 右侧 - 监控面板 (30% 宽度)
        right_widget = ResourceMonitor()
        right_widget.setMinimumWidth(350)
        main_layout.addWidget(right_widget, 3)  # 3份宽度


def main():
    # 创建应用实例
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    # 设置应用属性
    app.setApplicationName("Qt Resource Monitor")
    app.setApplicationVersion("1.0.0")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    print("🎉 应用已启动！")
    print("📊 右侧监控面板显示当前应用的CPU和内存使用情况")
    print("🔧 点击左侧按钮可以测试资源占用变化")

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()