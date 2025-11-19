from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QPushButton, QLabel, QSplitter, QFrame,
                               QSlider, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QVector3D, QQuaternion
from PySide6.Qt3DCore import Qt3DCore
from PySide6.Qt3DExtras import Qt3DExtras
from PySide6.Qt3DRender import Qt3DRender
from PySide6.QtCore import QUrl
import os


class GLBViewerPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setMouseTracking(True)
        self.setup_ui()
        self.setup_3d_viewer()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧 3D 视图区域
        left_widget = self.create_left_panel()

        # 右侧操作区域
        right_widget = self.create_right_panel()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setStretchFactor(0, 3)  # 左侧 3D 视图占 75%
        splitter.setStretchFactor(1, 1)  # 右侧操作面板占 25%

        # 设置右侧面板固定宽度
        right_widget.setFixedWidth(300)

        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """创建左侧 3D 视图面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(20, 20, 10, 20)

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

        title_label = QLabel("机械臂 3D 模型查看器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_layout.addWidget(title_label)

        container_layout.addWidget(title_bar)

        # 3D 视图容器
        self.view_3d_container = QWidget()
        container_layout.addWidget(self.view_3d_container)

        left_layout.addWidget(container)

        return left_widget

    def create_right_panel(self):
        """创建右侧操作面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 20, 20, 20)
        right_layout.setSpacing(15)

        # 标题
        title_label = QLabel("模型控制")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333333;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title_label)

        # 描述文本
        desc_label = QLabel("查看和操作机械臂 3D 模型")
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666666;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(desc_label)

        right_layout.addStretch(1)

        # 模型控制组
        model_group = QGroupBox("模型控制")
        model_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        model_layout = QVBoxLayout(model_group)

        # 加载模型按钮
        load_btn = QPushButton("加载机械臂模型")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 8px;
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
        load_btn.clicked.connect(self.load_robot_model)
        model_layout.addWidget(load_btn)

        # 重置视图按钮
        reset_btn = QPushButton("重置视图")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 8px;
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
        reset_btn.clicked.connect(self.reset_view)
        model_layout.addWidget(reset_btn)

        right_layout.addWidget(model_group)

        # 动画控制组
        animation_group = QGroupBox("动画控制")
        animation_group.setStyleSheet(model_group.styleSheet())
        animation_layout = QVBoxLayout(animation_group)

        # 旋转控制
        rotation_label = QLabel("模型旋转:")
        rotation_label.setStyleSheet("font-size: 12px; color: #333333;")
        animation_layout.addWidget(rotation_label)

        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.rotate_model)
        animation_layout.addWidget(self.rotation_slider)

        # 缩放控制
        scale_label = QLabel("模型缩放:")
        scale_label.setStyleSheet("font-size: 12px; color: #333333;")
        animation_layout.addWidget(scale_label)

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(10, 200)
        self.scale_slider.setValue(100)
        self.scale_slider.valueChanged.connect(self.scale_model)
        animation_layout.addWidget(self.scale_slider)

        # 自动旋转
        self.auto_rotate_check = QCheckBox("自动旋转")
        self.auto_rotate_check.setStyleSheet("font-size: 12px;")
        self.auto_rotate_check.toggled.connect(self.toggle_auto_rotate)
        animation_layout.addWidget(self.auto_rotate_check)

        right_layout.addWidget(animation_group)

        # 视图控制组
        view_group = QGroupBox("视图控制")
        view_group.setStyleSheet(model_group.styleSheet())
        view_layout = QGridLayout(view_group)

        # 视图按钮
        front_btn = QPushButton("前视图")
        front_btn.clicked.connect(lambda: self.set_camera_view("front"))
        view_layout.addWidget(front_btn, 0, 0)

        back_btn = QPushButton("后视图")
        back_btn.clicked.connect(lambda: self.set_camera_view("back"))
        view_layout.addWidget(back_btn, 0, 1)

        top_btn = QPushButton("顶视图")
        top_btn.clicked.connect(lambda: self.set_camera_view("top"))
        view_layout.addWidget(top_btn, 1, 0)

        bottom_btn = QPushButton("底视图")
        bottom_btn.clicked.connect(lambda: self.set_camera_view("bottom"))
        view_layout.addWidget(bottom_btn, 1, 1)

        right_layout.addWidget(view_group)

        right_layout.addStretch(2)

        # 返回主页按钮
        back_btn = QPushButton("返回主页")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 8px;
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
        back_btn.clicked.connect(self.back_to_home)
        right_layout.addWidget(back_btn)

        return right_widget

    def setup_3d_viewer(self):
        """设置 3D 查看器"""
        # 创建 3D 窗口
        self.view_3d = Qt3DExtras.Qt3DWindow()
        self.container = self.createWindowContainer(self.view_3d)

        # 添加到左侧面板
        left_layout = self.view_3d_container.layout()
        if left_layout is None:
            left_layout = QVBoxLayout(self.view_3d_container)
        left_layout.addWidget(self.container)

        # 设置场景
        self.setup_3d_scene()

    def setup_3d_scene(self):
        """设置 3D 场景"""
        # 根实体
        self.root_entity = Qt3DCore.QEntity()

        # 相机
        self.camera = self.view_3d.camera()
        self.camera.lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 1000.0)
        self.camera.setPosition(QVector3D(0, 0, 10))
        self.camera.setViewCenter(QVector3D(0, 0, 0))

        # 相机控制器
        self.cam_controller = Qt3DExtras.QOrbitCameraController(self.root_entity)
        self.cam_controller.setLinearSpeed(50.0)
        self.cam_controller.setLookSpeed(180.0)
        self.cam_controller.setCamera(self.camera)

        # 灯光
        self.setup_lighting()

        # 设置根实体
        self.view_3d.setRootEntity(self.root_entity)

        # 初始化模型实体
        self.model_entity = None
        self.model_transform = None

        # 自动旋转定时器
        self.auto_rotate_timer = None
        self.rotation_angle = 0

    def setup_lighting(self):
        """设置灯光"""
        # 使用点光源
        point_light_entity = Qt3DCore.QEntity(self.root_entity)
        point_light = Qt3DRender.QPointLight(point_light_entity)
        point_light.setColor("white")
        point_light.setIntensity(0.6)
        point_light_entity.addComponent(point_light)

        # 方向光
        directional_light_entity = Qt3DCore.QEntity(self.root_entity)
        directional_light = Qt3DRender.QDirectionalLight(directional_light_entity)
        directional_light.setColor("white")
        directional_light.setIntensity(0.8)
        directional_light_entity.addComponent(directional_light)

        # 灯光变换 - 使用 QQuaternion
        light_transform = Qt3DCore.QTransform(directional_light_entity)
        light_transform.setRotation(QQuaternion.fromEulerAngles(-45, 45, 0))
        directional_light_entity.addComponent(light_transform)

    def load_robot_model(self):
        """加载机械臂模型"""
        # 获取当前文件所在目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建模型文件的绝对路径
        model_path = os.path.join(current_dir, "../../assets/1.glb")
        model_path = os.path.abspath(model_path)  # 规范化路径

        print(f"尝试加载模型: {model_path}")  # 调试信息

        if not os.path.exists(model_path):
            print(f"模型文件不存在: {model_path}")
            # 显示可用的文件
            assets_dir = os.path.join(current_dir, "../../assets")
            assets_dir = os.path.abspath(assets_dir)
            if os.path.exists(assets_dir):
                files = os.listdir(assets_dir)
                print(f"assets目录下的文件: {files}")
            return

        # 如果之前有模型，先移除
        if self.model_entity:
            self.model_entity.setParent(Qt3DCore.QEntity())

        # 创建新的模型实体
        self.model_entity = Qt3DCore.QEntity(self.root_entity)

        # 创建变换组件
        self.model_transform = Qt3DCore.QTransform()
        self.model_entity.addComponent(self.model_transform)

        # 创建 GLB 加载器
        model_loader = Qt3DRender.QSceneLoader(self.model_entity)
        model_loader.setSource(QUrl.fromLocalFile(model_path))

        # 连接加载完成信号
        model_loader.statusChanged.connect(self.on_model_loaded)

        self.model_entity.addComponent(model_loader)

        print(f"正在加载模型: {model_path}")

    def on_model_loaded(self, status):
        """模型加载完成回调"""
        if status == Qt3DRender.QSceneLoader.Ready:
            print("机械臂模型加载成功!")
        elif status == Qt3DRender.QSceneLoader.Error:
            print("机械臂模型加载失败!")

    def reset_view(self):
        """重置视图"""
        self.camera.setPosition(QVector3D(0, 0, 10))
        self.camera.setViewCenter(QVector3D(0, 0, 0))
        self.camera.setUpVector(QVector3D(0, 1, 0))

        if self.model_transform:
            self.model_transform.setRotation(QQuaternion.fromEulerAngles(0, 0, 0))
            self.model_transform.setScale(1.0)

        self.rotation_slider.setValue(0)
        self.scale_slider.setValue(100)

    def rotate_model(self, angle):
        """旋转模型"""
        if self.model_transform:
            self.model_transform.setRotation(
                QQuaternion.fromEulerAngles(0, angle, 0)
            )

    def scale_model(self, scale_percent):
        """缩放模型"""
        if self.model_transform:
            scale = scale_percent / 100.0
            self.model_transform.setScale(scale)

    def toggle_auto_rotate(self, enabled):
        """切换自动旋转"""
        if enabled:
            # 开始自动旋转
            if not self.auto_rotate_timer:
                from PySide6.QtCore import QTimer
                self.auto_rotate_timer = QTimer()
                self.auto_rotate_timer.timeout.connect(self.auto_rotate)
            self.auto_rotate_timer.start(50)  # 20 FPS
        else:
            # 停止自动旋转
            if self.auto_rotate_timer:
                self.auto_rotate_timer.stop()

    def auto_rotate(self):
        """自动旋转"""
        if self.model_transform:
            self.rotation_angle = (self.rotation_angle + 1) % 360
            self.model_transform.setRotation(
                QQuaternion.fromEulerAngles(0, self.rotation_angle, 0)
            )
            self.rotation_slider.setValue(self.rotation_angle)

    def set_camera_view(self, view_type):
        """设置相机视图"""
        if view_type == "front":
            self.camera.setPosition(QVector3D(0, 0, 10))
        elif view_type == "back":
            self.camera.setPosition(QVector3D(0, 0, -10))
        elif view_type == "top":
            self.camera.setPosition(QVector3D(0, 10, 0))
        elif view_type == "bottom":
            self.camera.setPosition(QVector3D(0, -10, 0))

        self.camera.setViewCenter(QVector3D(0, 0, 0))

    def back_to_home(self):
        """返回主页按钮点击事件"""
        print("返回主页")
        if self.main_window:
            self.main_window.home_click()