from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QSplitter, QFrame,
                               QFileDialog, QSlider)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QMouseEvent
import os
import numpy as np
import json
import time


class URDFViewerPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_urdf_path = None
        self.robot_id = None
        self.physics_client = None

        # 相机参数
        self.camera_distance = 2.0
        self.camera_yaw = 45
        self.camera_pitch = -30
        self.camera_target = [0, 0, 0.5]

        # 鼠标控制参数
        self.last_mouse_pos = None
        self.is_rotating = False
        self.is_panning = False

        # 关节控制参数
        self.joint_sliders = []
        self.joint_labels = []

        # 坐标系参数
        self.coordinate_axes_ids = []  # 存储坐标系物体的ID
        self.show_coordinate = True  # 是否显示坐标系

        # 轨迹记录参数
        self.is_recording = False
        self.trajectory_data = []  # 存储轨迹数据
        self.recording_start_time = 0
        self.playback_index = 0
        self.is_playing_back = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.playback_next_frame)

        # 渲染相关变量
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.update_render)

        # 尝试导入pybullet
        self.pybullet_available = False
        try:
            import pybullet as p
            import pybullet_data
            self.p = p
            self.pybullet_data = pybullet_data
            self.pybullet_available = True
            print("PyBullet 导入成功")
        except ImportError as e:
            print(f"PyBullet 导入失败: {e}")
            self.show_pybullet_error()

        self.setup_ui()
        if self.pybullet_available:
            self.initialize_pybullet()

    def setup_ui(self):
        """设置基础UI"""
        print("开始设置PyBullet URDF查看器UI...")

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 左侧 3D 视图区域
        left_widget = self.create_left_panel()

        # 右侧控制区域
        right_widget = self.create_right_panel()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setStretchFactor(0, 4)  # 3D视图占4份
        splitter.setStretchFactor(1, 1)  # 控制面板占1份

        main_layout.addWidget(splitter)

        print("PyBullet URDF查看器UI设置完成")

    def create_left_panel(self):
        """创建左侧 3D 视图面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 3D 视图容器
        self.view_3d_container = QFrame()
        self.view_3d_container.setFrameStyle(QFrame.Box)
        self.view_3d_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #34495E;
            }
        """)

        self.container_layout = QVBoxLayout(self.view_3d_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        # 创建渲染显示标签
        self.render_label = QLabel("正在初始化3D渲染引擎...")
        self.render_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.render_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a; 
                color: #ECF0F1; 
                font-size: 14px;
                border: none;
                min-height: 400px;
            }
        """)
        self.render_label.setMinimumSize(400, 400)

        # 启用鼠标跟踪
        self.render_label.setMouseTracking(True)
        self.render_label.installEventFilter(self)

        self.container_layout.addWidget(self.render_label)
        left_layout.addWidget(self.view_3d_container)

        # 添加操作提示 - 减小高度
        controls_label = QLabel("鼠标操作: 左键旋转 | 右键平移 | 滚轮缩放")
        controls_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 9px;
                padding: 1px 5px;
                background-color: #2c3e50;
                margin: 0px;
            }
        """)
        controls_label.setFixedHeight(14)
        left_layout.addWidget(controls_label)

        return left_widget

    def create_right_panel(self):
        """创建右侧控制面板"""
        right_widget = QWidget()
        right_widget.setMinimumWidth(280)
        right_widget.setMaximumWidth(320)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(3)

        # 文件和控制按钮合并到一个框
        control_group = QFrame()
        control_group.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(3)

        # 选择文件按钮
        self.load_file_btn = QPushButton("选择URDF文件")
        self.load_file_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 5px 3px;
                background-color: #3498DB; 
                color: white;
                border: none;
                border-radius: 2px;
                font-weight: bold;
                min-height: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #2471A3;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        self.load_file_btn.clicked.connect(self.select_urdf_file)
        control_layout.addWidget(self.load_file_btn)

        # 相机控制按钮水平布局
        camera_layout = QHBoxLayout()
        camera_layout.setSpacing(3)

        # 重置相机按钮
        reset_camera_btn = QPushButton("重置视角")
        reset_camera_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #F39C12; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #D68910;
            }
        """)
        reset_camera_btn.clicked.connect(self.reset_camera)
        camera_layout.addWidget(reset_camera_btn)

        # 重置缩放按钮
        reset_zoom_btn = QPushButton("重置缩放")
        reset_zoom_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #8E44AD; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #7D3C98;
            }
        """)
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        camera_layout.addWidget(reset_zoom_btn)

        control_layout.addLayout(camera_layout)
        right_layout.addWidget(control_group)

        # 坐标系控制区域
        coordinate_group = QFrame()
        coordinate_group.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        coordinate_layout = QHBoxLayout(coordinate_group)
        coordinate_layout.setSpacing(3)

        # # 坐标系开关
        # self.coordinate_toggle = QPushButton("隐藏坐标系")
        # self.coordinate_toggle.setStyleSheet("""
        #     QPushButton {
        #         font-size: 9px;
        #         padding: 3px 2px;
        #         background-color: #27AE60;
        #         color: white;
        #         border: none;
        #         border-radius: 2px;
        #         min-height: 12px;
        #     }
        #     QPushButton:hover {
        #         background-color: #219A52;
        #     }
        # """)
        # self.coordinate_toggle.clicked.connect(self.toggle_coordinate)
        # coordinate_layout.addWidget(self.coordinate_toggle)

        # # 坐标系说明
        # coord_label = QLabel("X:右 Y:里 Z:上")
        # coord_label.setStyleSheet("""
        #     QLabel {
        #         color: #ECF0F1;
        #         font-size: 8px;
        #         font-weight: bold;
        #     }
        # """)
        # coordinate_layout.addWidget(coord_label)
        #
        # right_layout.addWidget(coordinate_group)

        # 轨迹记录区域
        trajectory_group = QFrame()
        trajectory_group.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        trajectory_layout = QVBoxLayout(trajectory_group)
        trajectory_layout.setSpacing(3)

        # 轨迹记录标题
        trajectory_title = QLabel("轨迹记录")
        trajectory_title.setStyleSheet("""
            QLabel {
                color: #ECF0F1;
                font-size: 10px;
                font-weight: bold;
                margin-bottom: 1px;
            }
        """)
        trajectory_layout.addWidget(trajectory_title)

        # 轨迹记录按钮布局
        traj_buttons_layout1 = QHBoxLayout()
        traj_buttons_layout1.setSpacing(3)

        # 开始记录按钮
        self.start_record_btn = QPushButton("开始记录")
        self.start_record_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #E74C3C; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        self.start_record_btn.clicked.connect(self.start_recording)
        traj_buttons_layout1.addWidget(self.start_record_btn)

        # 停止记录按钮
        self.stop_record_btn = QPushButton("停止记录")
        self.stop_record_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #95A5A6; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.stop_record_btn.setEnabled(False)
        traj_buttons_layout1.addWidget(self.stop_record_btn)

        trajectory_layout.addLayout(traj_buttons_layout1)

        # 轨迹回放和导出按钮布局
        traj_buttons_layout2 = QHBoxLayout()
        traj_buttons_layout2.setSpacing(3)

        # 回放轨迹按钮
        self.playback_btn = QPushButton("回放轨迹")
        self.playback_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #9B59B6; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        self.playback_btn.clicked.connect(self.playback_trajectory)
        self.playback_btn.setEnabled(False)
        traj_buttons_layout2.addWidget(self.playback_btn)

        # 导出数据按钮
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setStyleSheet("""
            QPushButton {
                font-size: 9px;
                padding: 3px 2px;
                background-color: #3498DB; 
                color: white;
                border: none;
                border-radius: 2px;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:disabled {
                background-color: #7F8C8D;
            }
        """)
        self.export_btn.clicked.connect(self.export_trajectory_data)
        self.export_btn.setEnabled(False)
        traj_buttons_layout2.addWidget(self.export_btn)

        trajectory_layout.addLayout(traj_buttons_layout2)

        # 轨迹信息显示
        self.trajectory_info_label = QLabel("未记录轨迹")
        self.trajectory_info_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 8px;
                font-style: italic;
            }
        """)
        self.trajectory_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trajectory_layout.addWidget(self.trajectory_info_label)

        right_layout.addWidget(trajectory_group)

        # 关节控制区域
        self.joints_group = QFrame()
        self.joints_group.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.joints_layout = QVBoxLayout(self.joints_group)
        self.joints_layout.setSpacing(2)

        # 关节控制标题
        joints_title = QLabel("关节控制")
        joints_title.setStyleSheet("""
            QLabel {
                color: #ECF0F1;
                font-size: 10px;
                font-weight: bold;
                margin-bottom: 1px;
            }
        """)
        self.joints_layout.addWidget(joints_title)

        # 初始化关节控制区域（会在加载URDF后更新）
        self.init_joints_control()

        right_layout.addWidget(self.joints_group)

        # 状态信息
        self.status_label = QLabel("正在初始化...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ECF0F1; 
                font-size: 8px;
                padding: 4px;
                background-color: #34495E;
                border-radius: 2px;
                min-height: 30px;
            }
        """)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.status_label)

        right_layout.addStretch()

        # 返回主页按钮
        back_btn = QPushButton("返回主页")
        back_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 5px 3px;
                background-color: #E74C3C; 
                color: white;
                border: none;
                border-radius: 2px;
                font-weight: bold;
                min-height: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
        back_btn.clicked.connect(self.back_to_home)
        right_layout.addWidget(back_btn)

        return right_widget

    def create_coordinate_axes(self):
        """创建坐标系 - 只有轴线"""
        if not self.pybullet_available:
            return

        # 清除现有的坐标系
        self.remove_coordinate_axes()

        # 坐标系参数
        axis_length = 1.5  # 轴线长度
        axis_radius = 0.01  # 轴线半径

        # 创建X轴 (红色)
        x_axis_visual = self.p.createVisualShape(
            self.p.GEOM_CYLINDER,
            radius=axis_radius,
            length=axis_length,
            rgbaColor=[1, 0, 0, 1]  # 红色
        )
        x_axis = self.p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=x_axis_visual,
            basePosition=[axis_length / 2, 0, 0],
            baseOrientation=self.p.getQuaternionFromEuler([0, np.pi / 2, 0])
        )
        self.coordinate_axes_ids.append(x_axis)

        # 创建Y轴 (绿色)
        y_axis_visual = self.p.createVisualShape(
            self.p.GEOM_CYLINDER,
            radius=axis_radius,
            length=axis_length,
            rgbaColor=[0, 1, 0, 1]  # 绿色
        )
        y_axis = self.p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=y_axis_visual,
            basePosition=[0, axis_length / 2, 0],
            baseOrientation=self.p.getQuaternionFromEuler([np.pi / 2, 0, 0])
        )
        self.coordinate_axes_ids.append(y_axis)

        # 创建Z轴 (蓝色)
        z_axis_visual = self.p.createVisualShape(
            self.p.GEOM_CYLINDER,
            radius=axis_radius,
            length=axis_length,
            rgbaColor=[0, 0, 1, 1]  # 蓝色
        )
        z_axis = self.p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=z_axis_visual,
            basePosition=[0, 0, axis_length / 2],
            baseOrientation=[0, 0, 0, 1]
        )
        self.coordinate_axes_ids.append(z_axis)

        print("坐标系创建成功 - 只有轴线")

    def remove_coordinate_axes(self):
        """移除坐标系"""
        for axis_id in self.coordinate_axes_ids:
            try:
                self.p.removeBody(axis_id)
            except:
                pass
        self.coordinate_axes_ids = []

    def toggle_coordinate(self):
        """切换坐标系显示"""
        self.show_coordinate = not self.show_coordinate

        if self.show_coordinate:
            self.coordinate_toggle.setText("隐藏坐标系")
            self.create_coordinate_axes()
        else:
            self.coordinate_toggle.setText("显示坐标系")
            self.remove_coordinate_axes()

    def init_joints_control(self):
        """初始化关节控制区域"""
        # 清除现有的关节控制
        for i in reversed(range(self.joints_layout.count())):
            widget = self.joints_layout.itemAt(i).widget()
            if widget and widget != self.joints_layout.itemAt(0).widget():  # 保留标题
                widget.deleteLater()

        self.joint_sliders = []
        self.joint_labels = []

        # 添加提示信息
        hint_label = QLabel("加载URDF后显示关节控制")
        hint_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 8px;
                font-style: italic;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.joints_layout.addWidget(hint_label)

    def update_joints_control(self, num_joints):
        """更新关节控制滑块"""
        # 清除现有的关节控制（除了标题）
        for i in reversed(range(self.joints_layout.count())):
            widget = self.joints_layout.itemAt(i).widget()
            if widget and widget != self.joints_layout.itemAt(0).widget():  # 保留标题
                widget.deleteLater()

        self.joint_sliders = []
        self.joint_labels = []

        # 为每个关节创建控制
        for i in range(min(6, num_joints)):  # 最多显示6个关节
            # 关节控制行 - 名称、滑块、角度值在同一行
            joint_row_layout = QHBoxLayout()
            joint_row_layout.setSpacing(3)

            # 关节名称标签
            joint_name_label = QLabel(f"J{i + 1}:")
            joint_name_label.setStyleSheet("""
                QLabel {
                    color: #ECF0F1;
                    font-size: 8px;
                    font-weight: bold;
                    min-width: 20px;
                }
            """)
            joint_row_layout.addWidget(joint_name_label)

            # 关节滑块
            joint_slider = QSlider(Qt.Orientation.Horizontal)
            joint_slider.setRange(-180, 180)  # -180° 到 180°
            joint_slider.setValue(0)
            joint_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #34495E;
                    height: 2px;
                    border-radius: 1px;
                }
                QSlider::handle:horizontal {
                    background: #3498DB;
                    width: 8px;
                    height: 8px;
                    border-radius: 4px;
                    margin: -3px 0;
                }
                QSlider::handle:horizontal:hover {
                    background: #2980B9;
                }
            """)
            joint_slider.valueChanged.connect(lambda value, idx=i: self.on_joint_slider_change(idx, value))
            self.joint_sliders.append(joint_slider)
            joint_row_layout.addWidget(joint_slider)

            # 关节值标签
            joint_value_label = QLabel("0°")
            joint_value_label.setStyleSheet("""
                QLabel {
                    color: #3498DB;
                    font-size: 8px;
                    min-width: 25px;
                }
            """)
            joint_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.joint_labels.append(joint_value_label)
            joint_row_layout.addWidget(joint_value_label)

            self.joints_layout.addLayout(joint_row_layout)

        # 如果关节数超过6个，显示提示
        if num_joints > 6:
            hint_label = QLabel(f"... 还有 {num_joints - 6} 个关节")
            hint_label.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    font-size: 7px;
                    font-style: italic;
                }
            """)
            hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.joints_layout.addWidget(hint_label)

    def on_joint_slider_change(self, joint_index, value):
        """关节滑块值改变时的回调"""
        # 更新标签显示
        self.joint_labels[joint_index].setText(f"{value}°")

        # 在PyBullet中设置关节位置（转换为弧度）
        if self.pybullet_available and self.robot_id is not None:
            try:
                # 设置关节位置（转换为弧度）
                self.p.resetJointState(self.robot_id, joint_index, np.radians(value))
            except Exception as e:
                print(f"设置关节 {joint_index} 位置失败: {e}")

    def eventFilter(self, obj, event):
        """事件过滤器处理鼠标事件"""
        if obj == self.render_label:
            if event.type() == QMouseEvent.Type.MouseButtonPress:
                self.mouse_press_event(event)
                return True
            elif event.type() == QMouseEvent.Type.MouseMove:
                self.mouse_move_event(event)
                return True
            elif event.type() == QMouseEvent.Type.MouseButtonRelease:
                self.mouse_release_event(event)
                return True
            elif event.type() == QMouseEvent.Type.Wheel:
                self.wheel_event(event)
                return True
        return super().eventFilter(obj, event)

    def mouse_press_event(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = True
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
        self.last_mouse_pos = event.position()

    def mouse_move_event(self, event):
        """鼠标移动事件"""
        if self.last_mouse_pos is None:
            return

        current_pos = event.position()
        dx = current_pos.x() - self.last_mouse_pos.x()
        dy = current_pos.y() - self.last_mouse_pos.y()

        if self.is_rotating:
            # 旋转相机
            self.camera_yaw += dx * 0.5
            self.camera_pitch += dy * 0.5
            # 限制俯仰角范围
            self.camera_pitch = max(-89.0, min(89.0, self.camera_pitch))

        elif self.is_panning:
            # 平移相机目标
            self.camera_target[0] -= dx * 0.01
            self.camera_target[1] += dy * 0.01

        self.last_mouse_pos = current_pos

    def mouse_release_event(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_rotating = False
        elif event.button() == Qt.MouseButton.RightButton:
            self.is_panning = False
        self.last_mouse_pos = None

    def wheel_event(self, event):
        """鼠标滚轮事件 - 缩放"""
        delta = event.angleDelta().y()

        # 根据滚轮方向调整相机距离
        zoom_factor = 1.1
        if delta > 0:
            # 滚轮向上，缩小（相机靠近）
            self.camera_distance /= zoom_factor
        else:
            # 滚轮向下，放大（相机远离）
            self.camera_distance *= zoom_factor

        # 限制缩放范围
        self.camera_distance = max(0.1, min(20.0, self.camera_distance))

        # 更新状态显示
        self.update_status_with_camera_info()

    def reset_camera(self):
        """重置相机到默认位置"""
        self.camera_distance = 2.0
        self.camera_yaw = 45
        self.camera_pitch = -30
        self.camera_target = [0, 0, 0.5]
        self.update_status_with_camera_info()

    def reset_zoom(self):
        """重置缩放"""
        self.camera_distance = 2.0
        self.update_status_with_camera_info()

    def update_status_with_camera_info(self):
        """更新状态信息显示相机参数"""
        if hasattr(self, 'status_label'):
            # 获取基础状态文本（如果有机器人信息）
            base_text = "就绪"
            if hasattr(self, 'robot_id') and self.robot_id is not None:
                # 如果有加载的机器人，保持机器人信息
                current_text = self.status_label.text()
                if "✅" in current_text or "❌" in current_text:
                    lines = current_text.split('\n')
                    if len(lines) > 0:
                        base_text = lines[0]

            # 压缩相机信息到一行
            camera_info = f"距离:{self.camera_distance:.1f}m 俯仰:{self.camera_pitch:.1f}° 偏航:{self.camera_yaw:.1f}°"
            self.status_label.setText(f"{base_text}\n{camera_info}")

    def show_pybullet_error(self):
        """显示PyBullet错误信息"""
        error_text = (
            "PyBullet 未安装或导入失败\n\n"
            "请安装PyBullet:\n"
            "pip install pybullet\n\n"
            "如果已安装但仍报错，请检查Python环境"
        )
        self.render_label.setText(error_text)
        self.status_label.setText("PyBullet 未安装")

        # 禁用按钮
        self.load_file_btn.setEnabled(False)

    def initialize_pybullet(self):
        """初始化PyBullet - 使用DIRECT模式在界面内渲染"""
        if not self.pybullet_available:
            return

        try:
            print("正在初始化PyBullet...")

            # 连接到物理引擎（DIRECT模式用于界面内渲染）
            self.physics_client = self.p.connect(self.p.DIRECT)
            print(f"PyBullet物理客户端连接成功: {self.physics_client}")

            # 设置附加搜索路径
            self.p.setAdditionalSearchPath(self.pybullet_data.getDataPath())

            # 设置重力
            self.p.setGravity(0, 0, -9.8)

            # 创建地面
            self.p.loadURDF("plane.urdf")

            # 创建坐标系
            self.create_coordinate_axes()

            # 更新状态
            self.status_label.setText("PyBullet 初始化成功\n正在加载默认机器人...")
            self.render_label.setText("正在加载默认机器人...")

            print("PyBullet DIRECT模式初始化成功")

            # 自动加载默认机器人
            self.load_default_urdf()

            # 开始渲染循环
            self.render_timer.start(33)  # 约30fps

        except Exception as e:
            error_msg = f"PyBullet初始化失败: {e}"
            print(error_msg)
            self.status_label.setText("PyBullet 初始化失败")
            self.render_label.setText(f"PyBullet初始化失败:\n{str(e)}")

    def load_default_urdf(self):
        """自动加载默认URDF文件"""
        try:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            urdf_path = os.path.join(current_dir, "assets", "kr1", "urdf", "kr1.urdf")

            print(f"尝试自动加载默认URDF: {urdf_path}")

            if not os.path.exists(urdf_path):
                print(f"默认URDF文件不存在: {urdf_path}")
                self.status_label.setText("默认URDF文件不存在\n请使用选择文件按钮加载其他URDF")
                return

            self.load_urdf_model(urdf_path)

        except Exception as e:
            print(f"自动加载默认URDF失败: {e}")
            self.status_label.setText(f"自动加载默认URDF失败:\n{str(e)}")

    def update_render(self):
        """更新渲染"""
        if not self.pybullet_available or self.physics_client is None:
            return

        try:
            # 如果正在记录轨迹，记录当前末端位置
            if self.is_recording and self.robot_id is not None:
                end_effector_pos = self.get_end_effector_position()
                if end_effector_pos:
                    current_time = time.time() - self.recording_start_time
                    self.trajectory_data.append({
                        'timestamp': current_time,
                        'position': end_effector_pos
                    })

            # 获取标签尺寸
            width = self.render_label.width()
            height = self.render_label.height()

            if width <= 10 or height <= 10:
                return

            # 获取相机视图矩阵
            view_matrix = self.p.computeViewMatrixFromYawPitchRoll(
                self.camera_target,
                self.camera_distance,
                self.camera_yaw,
                self.camera_pitch,
                0,
                2
            )

            # 设置投影矩阵
            aspect_ratio = width / max(1, height)
            projection_matrix = self.p.computeProjectionMatrixFOV(
                fov=60,
                aspect=aspect_ratio,
                nearVal=0.1,
                farVal=100.0
            )

            # 获取渲染图像
            try:
                # 尝试使用BULLET_HARDWARE_OPENGL渲染器
                _, _, rgb_array, _, _ = self.p.getCameraImage(
                    width=width,
                    height=height,
                    viewMatrix=view_matrix,
                    projectionMatrix=projection_matrix,
                    renderer=self.p.ER_BULLET_HARDWARE_OPENGL
                )

                self.process_render_result(rgb_array, width, height)

            except Exception as hardware_error:
                print(f"硬件渲染失败，尝试软件渲染: {hardware_error}")
                try:
                    # 回退到TINY_RENDERER
                    _, _, rgb_array, _, _ = self.p.getCameraImage(
                        width=width,
                        height=height,
                        viewMatrix=view_matrix,
                        projectionMatrix=projection_matrix,
                        renderer=self.p.ER_TINY_RENDERER
                    )
                    self.process_render_result(rgb_array, width, height)
                except Exception as software_error:
                    print(f"软件渲染也失败: {software_error}")
                    self.show_blank_image(width, height, "渲染失败")

        except Exception as e:
            print(f"渲染更新失败: {e}")

    def process_render_result(self, rgb_array, width, height):
        """处理渲染结果"""
        try:
            # 确保rgb_array是numpy数组
            rgb_array = np.array(rgb_array, dtype=np.uint8)

            # 处理不同的数组格式
            if len(rgb_array.shape) == 1:
                # 一维数组 - 重新整形为(height, width, 4)
                if rgb_array.size == width * height * 4:
                    rgb_array = rgb_array.reshape((height, width, 4))
                    # 从RGBA转换为RGB
                    rgb_array = rgb_array[:, :, :3]
                else:
                    raise ValueError(f"不支持的1D数组大小: {rgb_array.size}")
            elif len(rgb_array.shape) == 3:
                # 三维数组
                if rgb_array.shape[2] == 4:
                    # RGBA -> RGB
                    rgb_array = rgb_array[:, :, :3]
                elif rgb_array.shape[2] == 3:
                    # 已经是RGB，直接使用
                    pass
                else:
                    raise ValueError(f"不支持的3D数组形状: {rgb_array.shape}")
            else:
                raise ValueError(f"不支持的数组维度: {len(rgb_array.shape)}")

            # 确保数组是C连续的
            if not rgb_array.flags['C_CONTIGUOUS']:
                rgb_array = np.ascontiguousarray(rgb_array)

            # 创建QImage
            bytes_per_line = 3 * width
            image = QImage(rgb_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            if image.isNull():
                raise ValueError("创建QImage失败")

            # 转换为QPixmap并显示
            pixmap = QPixmap.fromImage(image)
            self.render_label.setPixmap(pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

        except Exception as e:
            print(f"处理渲染结果失败: {e}")
            self.show_blank_image(width, height, f"渲染错误: {str(e)}")

    def show_blank_image(self, width, height, message=None):
        """显示空白图像"""
        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.darkGray)

        pixmap = QPixmap.fromImage(image)
        self.render_label.setPixmap(pixmap)

    def select_urdf_file(self):
        """选择并加载URDF文件"""
        try:
            urdf_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择URDF模型文件",
                "",
                "URDF模型文件 (*.urdf);;所有文件 (*)"
            )

            if urdf_path and os.path.exists(urdf_path):
                self.load_urdf_model(urdf_path)
            else:
                print("未选择有效的URDF文件")
                self.status_label.setText("未选择有效的URDF文件")

        except Exception as e:
            print(f"选择URDF文件失败: {e}")
            self.status_label.setText(f"选择文件失败:\n{str(e)}")

    def load_urdf_model(self, urdf_path):
        """加载URDF模型"""
        if not self.pybullet_available:
            self.status_label.setText("PyBullet未安装")
            return

        try:
            print(f"正在加载URDF模型: {urdf_path}")
            self.status_label.setText("正在加载URDF模型...")

            # 清除现有模型
            if self.robot_id is not None:
                self.p.removeBody(self.robot_id)
                self.robot_id = None

            # 获取URDF文件所在目录
            urdf_dir = os.path.dirname(urdf_path)
            print(f"URDF文件目录: {urdf_dir}")

            # 设置附加搜索路径，包括URDF文件所在目录
            self.p.setAdditionalSearchPath(urdf_dir)

            # 加载URDF - 将机器人放在地面上
            start_pos = [0, 0, 0]  # 直接放在地面上
            start_orientation = self.p.getQuaternionFromEuler([0, 0, 0])

            self.robot_id = self.p.loadURDF(
                urdf_path,
                start_pos,
                start_orientation,
                useFixedBase=True,
                flags=self.p.URDF_USE_INERTIA_FROM_FILE
            )

            if self.robot_id < 0:
                raise Exception("URDF加载失败，返回无效的机器人ID")

            # 获取模型信息
            num_joints = self.p.getNumJoints(self.robot_id)

            # 更新关节控制
            self.update_joints_control(num_joints)

            # 更新状态
            model_name = os.path.basename(urdf_path)
            status_text = f"✅ 加载成功\n模型: {model_name} 关节数: {num_joints}"
            self.status_label.setText(status_text)
            self.update_status_with_camera_info()
            self.render_label.setText("")

            print(f"✅ URDF模型加载成功: {model_name}, 关节数: {num_joints}")

        except Exception as e:
            print(f"加载URDF模型失败: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"❌ 加载失败\n错误: {str(e)}")

    # 轨迹记录相关方法
    def start_recording(self):
        """开始记录轨迹"""
        if not self.pybullet_available or self.robot_id is None:
            return

        self.is_recording = True
        self.trajectory_data = []
        self.recording_start_time = time.time()

        # 更新按钮状态
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
        self.playback_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.trajectory_info_label.setText("记录中...")
        self.status_label.setText("开始记录末端轨迹")

        print("开始记录机械臂末端轨迹")

    def stop_recording(self):
        """停止记录轨迹"""
        self.is_recording = False

        # 更新按钮状态
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)

        if len(self.trajectory_data) > 0:
            self.playback_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            duration = time.time() - self.recording_start_time
            self.trajectory_info_label.setText(f"已记录: {len(self.trajectory_data)} 点\n时长: {duration:.1f}秒")
            self.status_label.setText(f"轨迹记录完成: {len(self.trajectory_data)} 个数据点")

            # 打印轨迹数据数组
            print("\n=== 轨迹数据数组 ===")
            for i, point in enumerate(self.trajectory_data):
                print(f"点 {i}: 时间={point['timestamp']:.2f}s, "
                      f"位置=({point['position'][0]:.3f}, {point['position'][1]:.3f}, {point['position'][2]:.3f})")
            print("===================\n")
        else:
            self.trajectory_info_label.setText("无轨迹数据")
            self.status_label.setText("轨迹记录停止 - 无数据")

    def get_end_effector_position(self):
        """获取机械臂末端执行器位置"""
        if self.robot_id is None:
            return None

        try:
            # 假设末端关节是最后一个关节
            num_joints = self.p.getNumJoints(self.robot_id)
            if num_joints == 0:
                return None

            # 获取末端关节状态
            joint_state = self.p.getLinkState(self.robot_id, num_joints - 1)
            if joint_state:
                # 返回末端位置
                return list(joint_state[4])  # 世界坐标系中的位置
            return None
        except:
            return None

    def playback_trajectory(self):
        """回放轨迹"""
        if len(self.trajectory_data) == 0:
            return

        self.is_playing_back = True
        self.playback_index = 0
        self.playback_btn.setEnabled(False)
        self.start_record_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

        self.status_label.setText("轨迹回放中...")
        self.trajectory_info_label.setText(f"回放: 0/{len(self.trajectory_data)}")

        # 开始回放计时器
        self.playback_timer.start(50)  # 20fps

    def playback_next_frame(self):
        """回放下一个轨迹点"""
        if self.playback_index >= len(self.trajectory_data):
            # 回放结束
            self.playback_timer.stop()
            self.is_playing_back = False
            self.playback_btn.setEnabled(True)
            self.start_record_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.status_label.setText("轨迹回放完成")
            self.trajectory_info_label.setText(f"已记录: {len(self.trajectory_data)} 点")
            return

        # 显示当前轨迹点信息
        point = self.trajectory_data[self.playback_index]
        self.trajectory_info_label.setText(f"回放: {self.playback_index + 1}/{len(self.trajectory_data)}")

        # 这里可以添加可视化轨迹点的代码
        # 例如在末端位置显示一个临时标记

        self.playback_index += 1

    def export_trajectory_data(self):
        """导出轨迹数据到文件"""
        if len(self.trajectory_data) == 0:
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出轨迹数据",
                f"trajectory_{time.strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json);;所有文件 (*)"
            )

            if file_path:
                # 准备导出数据
                export_data = {
                    "metadata": {
                        "recorded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "data_points": len(self.trajectory_data),
                        "duration": self.trajectory_data[-1]['timestamp'] if self.trajectory_data else 0
                    },
                    "trajectory": self.trajectory_data
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                self.status_label.setText(f"轨迹数据已导出: {file_path}")
                print(f"轨迹数据已导出到: {file_path}")

        except Exception as e:
            self.status_label.setText(f"导出失败: {str(e)}")
            print(f"导出轨迹数据失败: {e}")

    def back_to_home(self):
        """返回主页"""
        print("返回主页")
        if self.render_timer.isActive():
            self.render_timer.stop()
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        if self.pybullet_available and self.physics_client is not None:
            self.p.disconnect(self.physics_client)
        if self.main_window:
            self.main_window.home_click()

    def closeEvent(self, event):
        """关闭事件"""
        # 清理资源
        if self.render_timer.isActive():
            self.render_timer.stop()
        if self.playback_timer.isActive():
            self.playback_timer.stop()

        if self.pybullet_available and self.physics_client is not None:
            self.p.disconnect(self.physics_client)

        event.accept()