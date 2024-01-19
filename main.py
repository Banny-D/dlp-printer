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
        self.start = False
        self.drawing = False
        self.radius = 0

        self.init_ui()
        self.cap = cv2.VideoCapture(0)

    def init_ui(self):
        # TODO 初始化布局
        self.setWindowTitle('DLP绘图')
        
        # 图像显示区域
        self.image_area = QLabel(self)
        self.image_area.setCursor(Qt.CrossCursor)
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
        layout.addStretch(1)
        layout.addWidget(self.image_area)
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

    def show_mouse_position(self, event):
        x = event.x()
        y = event.y()
        self.mouse_x.setText(f'X: {x}')
        self.mouse_y.setText(f'Y: {y}')
        if self.start:
            self.end_point = event.pos()
            self.radius = self.calc_radius()
            self.drawing = True
        self.update()
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.drawing:
                cv2.circle(frame, (int(self.start_point.x()), int(self.start_point.y())), self.radius, (255, 255, 255), 20)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.IgnoreAspectRatio)
            # self.pw = p.width()
            # self.ph = p.height()
            self.image_area.setPixmap(QPixmap.fromImage(p))
            self.image_area.lower()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if not self.start:
                self.start_point = event.pos()  # 获取鼠标位置
                self.start = True
        elif event.buttons() == Qt.RightButton:
            if not self.start:
                self.timer_id = self.timer.start(800)
                self.start = True
            else:
                self.timer.stop()
                self.start = False
        else:
            self.drawing2 = True
            self.update()

    def wheelEvent(self, event):# 滚轮事件
        angle = event.angleDelta() / 8  # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
        angleY = angle.y()
        if angleY > 0:# 滚轮上滚
            self.radius = self.radius - 1
            self.drawing = True
            self.update()
        else:  # 滚轮下滚
            self.radius = self.radius + 1
            self.drawing = True
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            self.start = False
    
    def calc_radius(self):
        return int(math.sqrt(
            (self.start_point.x() - self.end_point.x()) ** 2 + (self.start_point.y() - self.end_point.y()) ** 2))
    
    def update_image(self):
        # TODO 副屏显示更新
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DrawRect()
    window.show()
    sys.exit(app.exec_())
