from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QPushButton, QLabel, QTreeWidget, QTreeWidgetItem,
                               QSplitter, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class TreePage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setMouseTracking(True)
        self.setup_ui()
        self.setup_tree_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧 TreeView 区域
        left_widget = self.create_left_panel()

        # 右侧操作区域
        right_widget = self.create_right_panel()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割比例 (对应Avalonia的列定义)
        splitter.setStretchFactor(0, 1)  # 左侧自适应
        splitter.setStretchFactor(1, 0)  # 右侧固定宽度

        # 设置右侧面板固定宽度
        right_widget.setFixedWidth(260)

        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """创建左侧TreeView面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(20, 20, 10, 20)  # 右边距小一些，给分割线留空间

        # 创建带边框的容器
        container = QFrame()
        container.setStyleSheet("""
              QFrame {
                  background-color: transparent;
                  border: none;
                  border-radius: 0px;
              }
          """)

        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        title_bar = QFrame()
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        title_bar.setFixedHeight(50)
        title_layout = QVBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)

        title_label = QLabel("设备树形结构")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_layout.addWidget(title_label)

        container_layout.addWidget(title_bar)

        # TreeView
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["设备名称", "类型", "状态"])
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                font-size: 14px;
                border: none;
                background-color: white;
                outline: 0;
            }
            QTreeWidget::item {
                padding: 8px 4px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #007BFF;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #F0F0F0;
            }
        """)
        self.tree_widget.setMouseTracking(True)

        # 设置列宽
        self.tree_widget.setColumnWidth(0, 200)
        self.tree_widget.setColumnWidth(1, 100)
        self.tree_widget.setColumnWidth(2, 80)

        container_layout.addWidget(self.tree_widget)
        left_layout.addWidget(container)

        return left_widget

    def create_right_panel(self):
        """创建右侧操作面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 20, 20, 20)
        right_layout.setSpacing(15)

        # 标题
        title_label = QLabel("树形页面")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(title_label)

        # 描述文本
        desc_label = QLabel("使用 TreeView 展示设备层次结构")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(desc_label)

        right_layout.addStretch(1)

        # 刷新数据按钮
        refresh_btn = QPushButton("刷新数据")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 15px 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        right_layout.addWidget(refresh_btn)

        # 展开全部按钮
        expand_btn = QPushButton("展开全部")
        expand_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 15px 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #155724;
            }
        """)
        expand_btn.clicked.connect(self.expand_all)
        right_layout.addWidget(expand_btn)

        # 折叠全部按钮
        collapse_btn = QPushButton("折叠全部")
        collapse_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 15px 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:pressed {
                background-color: #b38f00;
            }
        """)
        collapse_btn.clicked.connect(self.collapse_all)
        right_layout.addWidget(collapse_btn)

        # 返回主页按钮
        back_btn = QPushButton("返回主页")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 15px 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #3d4246;
            }
        """)
        back_btn.clicked.connect(self.back_to_home)  # 确保这里的方法名正确
        right_layout.addWidget(back_btn)

        right_layout.addStretch(2)

        return right_widget

    def setup_tree_data(self):
        """设置树形数据"""
        # 清空现有数据
        self.tree_widget.clear()

        # 添加示例数据 - 模拟设备层次结构
        devices = [
            {
                "name": "主控系统",
                "type": "系统",
                "status": "正常",
                "children": [
                    {
                        "name": "机器人控制单元",
                        "type": "控制器",
                        "status": "运行",
                        "children": [
                            {"name": "机械臂1", "type": "执行器", "status": "就绪", "children": []},
                            {"name": "机械臂2", "type": "执行器", "status": "运行", "children": []},
                            {"name": "视觉系统", "type": "传感器", "status": "正常", "children": []}
                        ]
                    },
                    {
                        "name": "IO模块",
                        "type": "模块",
                        "status": "正常",
                        "children": [
                            {"name": "数字输入", "type": "输入", "status": "正常", "children": []},
                            {"name": "数字输出", "type": "输出", "status": "正常", "children": []},
                            {"name": "模拟输入", "type": "输入", "status": "正常", "children": []}
                        ]
                    }
                ]
            },
            {
                "name": "网络设备",
                "type": "网络",
                "status": "正常",
                "children": [
                    {"name": "交换机", "type": "网络设备", "status": "正常", "children": []},
                    {"name": "路由器", "type": "网络设备", "status": "正常", "children": []},
                    {"name": "防火墙", "type": "安全设备", "status": "正常", "children": []}
                ]
            },
            {
                "name": "外围设备",
                "type": "外围",
                "status": "正常",
                "children": [
                    {"name": "打印机", "type": "输出设备", "status": "就绪", "children": []},
                    {"name": "扫描仪", "type": "输入设备", "status": "空闲", "children": []},
                    {"name": "摄像头", "type": "视频设备", "status": "运行", "children": []}
                ]
            }
        ]

        # 递归添加树节点
        self.add_tree_items(devices, self.tree_widget)

        # 默认展开第一级
        self.tree_widget.expandAll()

    def add_tree_items(self, devices, parent_widget):
        """递归添加树节点"""
        for device in devices:
            item = QTreeWidgetItem(parent_widget)
            item.setText(0, device["name"])
            item.setText(1, device["type"])
            item.setText(2, device["status"])

            # 根据状态设置颜色
            if device["status"] == "运行":
                item.setForeground(2, Qt.darkGreen)
            elif device["status"] == "就绪":
                item.setForeground(2, Qt.blue)
            elif device["status"] == "空闲":
                item.setForeground(2, Qt.darkGray)
            elif device["status"] == "错误":
                item.setForeground(2, Qt.red)

            # 递归添加子节点
            if device["children"]:
                self.add_tree_items(device["children"], item)

    def refresh_data(self):
        """刷新数据按钮点击事件"""
        print("刷新树形数据")
        self.setup_tree_data()

    def expand_all(self):
        """展开全部按钮点击事件"""
        print("展开所有节点")
        self.tree_widget.expandAll()

    def collapse_all(self):
        """折叠全部按钮点击事件"""
        print("折叠所有节点")
        self.tree_widget.collapseAll()

    def back_to_home(self):  # 确保这个方法名与连接时使用的一致
        """返回主页按钮点击事件"""
        print("返回主页")
        if self.main_window:
            self.main_window.home_click()