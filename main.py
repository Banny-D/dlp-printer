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
        self.init_ui()
        self.cap = cv2.VideoCapture(0)

    def init_ui(self):
        # TODO 初始化布局
        self.setWindowTitle('DLP绘图')
        
        # 图像显示区域
        self.image_area = QLabel(self)
        self.image_area.setCursor(Qt.CrossCursor)
        self.image_painter =QPainter(self)
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
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
            self.image_area.setPixmap(QPixmap.fromImage(p))

    def update_image(self):
        # TODO 副屏显示更新
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DrawRect()
    window.show()
    sys.exit(app.exec_())
