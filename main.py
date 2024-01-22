from PyQt5.QtWidgets import QWidget
import cv2
import numpy as np
import math
import sys

# from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class DrawRect(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.start_point = None
        self.end_point = None
        self.radius_tracking = False
        self.radius = 0
        # 默认设置
        self.r_size = 20  # 默认线宽
        self.out_win = 'out_fullscreen' # 默认输出窗口名称

        self.init_ui()
        self.init_out_window()
        self.cap = cv2.VideoCapture(0)

    def init_ui(self):
        # TODO 初始化布局
        self.setWindowTitle('DLP绘图')
        
        # 图像显示区域
        self.image_area = QLabel(self)
        self.image_area.setCursor(Qt.CrossCursor)
        # self.image_area.setFixedSize(640, 480) # 默认大小
        # self.image_area.setScaledContents(True) # 自适应调整大小
        # 鼠标坐标
        self.mouse_x = QLabel('X:', self)
        self.mouse_y = QLabel('y:', self)
        # 下拉框
        self.shape_box = QComboBox(self)
        self.shape_box.addItems(['圆环', '正方形', '三角形'])
        # 曝光按钮
        self.update_button = QPushButton('曝光', self)
        # 退出按钮
        self.quit_button = QPushButton('退出', self)
        
        # 组件布局
        layout = QVBoxLayout(self)
        # layout.addStretch(1)
        layout.addWidget(self.image_area, alignment=Qt.AlignCenter)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.mouse_x)
        hbox.addWidget(self.mouse_y)
        layout.addLayout(hbox)
        layout.addWidget(self.shape_box)
        layout.addWidget(self.update_button)
        layout.addWidget(self.quit_button)
        
        
        # 信号与槽连接
        self.update_button.clicked.connect(self.update_image)
        self.quit_button.clicked.connect(self.close)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.image_area.setMouseTracking(True) # 图像区域跟踪
        self.image_area.mouseMoveEvent = self.show_mouse_position
        self.image_area.mousePressEvent = self.mousePressEvent

    def init_out_window(self):
        cv2.namedWindow(self.out_win, cv2.WND_PROP_FULLSCREEN)
        # 屏幕设置
        screens = QApplication.desktop()
        if screens.screenCount() > 1:
            # 屏幕位置大小
            geometry = QApplication.desktop().screenGeometry(1)
            # 移动屏幕
            cv2.moveWindow(self.out_win, geometry.x(), geometry.y())
        else:
            geometry = QApplication.desktop().screenGeometry()
        self.out_img = np.zeros((geometry.height(), geometry.width(), 3), np.uint8)
        cv2.imshow(self.out_win, self.out_img)
        cv2.setWindowProperty(self.out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def show_mouse_position(self, event):
        x = event.x()
        y = event.y()
        self.mouse_x.setText(f'X: {x}')
        self.mouse_y.setText(f'Y: {y}')
        if self.radius_tracking:
            self.end_point = event.pos()
            self.radius = self.calc_radius()
        self.update()
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.start_point is not None:
                cv2.circle(frame, (int(self.start_point.x()), int(self.start_point.y())), self.radius, (255, 255, 255), self.r_size)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(w, h, Qt.IgnoreAspectRatio)
            self.image_area.setPixmap(QPixmap.fromImage(p))
            self.image_area.lower()

    def mousePressEvent(self, event):
        # 左键点击
        if event.buttons() == Qt.LeftButton:
            if self.start_point is None or not self.radius_tracking: # 未确定圆心
                self.start_point = event.pos()  # 获取鼠标位置确定圆心
                self.radius = 0
                self.radius_tracking = True # 根据鼠标位置实时绘画
            elif self.start_point is not None and self.radius_tracking: # 没有确定终点
                self.radius_tracking = False # 停止跟踪
                # self.end_point = event.pos()
                # self.radius = self.calc_radius()
        if event.buttons() == Qt.RightButton:
            self.start_point = None
            self.end_point = None
            self.radius_tracking = False
            self.radius = 0
        self.update()

    def wheelEvent(self, event):# 滚轮事件
        if self.start_point is not None:
            angle = event.angleDelta() / 8  # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
            angleY = angle.y()
            if angleY > 0:# 滚轮上滚
                if self.r_size > 1:
                    self.r_size = self.r_size - 1
                    self.update()
            else:  # 滚轮下滚
                if self.r_size < self.radius:
                    self.r_size = self.r_size + 1
                    self.update()
    
    def calc_radius(self):
        return int(math.sqrt(
            (self.start_point.x() - self.end_point.x()) ** 2 + (self.start_point.y() - self.end_point.y()) ** 2))
    
    def update_image(self):
        img = np.zeros((self.image_area.height(), self.image_area.width(), 3), np.uint8)
        if self.start_point is not None:
                cv2.circle(img, (int(self.start_point.x()), int(self.start_point.y())), self.radius, (255, 255, 255), self.r_size)
        self.out_img = cv2.resize(img, (self.out_img.shape[1], self.out_img.shape[0]))
        cv2.imshow(self.out_win, self.out_img)
        # cv2.setWindowProperty(self.out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DrawRect()
    window.show()
    sys.exit(app.exec_())
