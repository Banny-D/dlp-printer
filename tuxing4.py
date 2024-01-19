import sys
import os
import cv2
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt


class DrawRect(QWidget):

    def __init__(self, parent=None):
        super().__init__()
        self.start_point = None
        self.end_point = None
        self.start = False
        self.drawing = False
        self.radius = 0
        self.drawing2 = False
        self.setCursor(Qt.CrossCursor)#改变鼠标形状
        self.setMouseTracking(True)#鼠标监听
        self.setGeometry(QtCore.QRect(0, 0, 1920, 1080))
        self.setPalette(QPalette(QColor(0, 0, 0)))  # 设置背景颜色
        self.setAutoFillBackground(True)  # 设置窗口自动填充背景
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.a)
        self.timer_id = 0

    def a(self):
        self.radius = self.radius - 1
        self.drawing = True
        self.update()

    def paintEvent(self, event):
        # super(DrawRect, self).paintEvent(event)
        if self.drawing:
            painter = QPainter()
            painter.begin(self)
            painter.setBrush(QColor(0, 0, 0))  # 设置画刷用于填充
            pen = QPen(QColor(255, 255, 255), 20)
            painter.setPen(pen)
            painter.drawEllipse(self.start_point, self.radius, self.radius)  # 画圆
            if self.drawing2:
                #painter.setBrush(QColor(0, 0, 0))  # 设置画刷用于填充
                pen = QPen(QColor(255, 255, 255), 45)
                painter.setPen(pen)
                painter.drawEllipse(self.start_point, 60, 60)  # 画圆
            painter.end()

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

    def mouseMoveEvent(self, event):
        if self.start:
            self.end_point = event.pos()
            self.radius = self.calc_radius()
            self.drawing = True
            self.update()

    def calc_radius(self):
        return math.sqrt(
            (self.start_point.x() - self.end_point.x()) ** 2 + (self.start_point.y() - self.end_point.y()) ** 2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # screens = app.screens()
    demo = DrawRect()
    demo.setWindowFlags(Qt.FramelessWindowHint)
    demo.show()
    app.exec_()
