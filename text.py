import cv2
import numpy as np
import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import cv2
import csv
import codecs

from threading import Thread
import os,time
def data_write_csv(file_name, datas):#file_name为写入CSV文件的路径，datas为要写入数据列表
    file_csv = codecs.open(file_name,'w+','utf-8')#追加
    writer = csv.writer(file_csv, delimiter=' ', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
    for data in datas:
        writer.writerow(data)
    print("保存文件成功，处理结束")

# 读取图片
def ReadImg():
    img = cv2.imread('xibao.jpg', 1)
    # cv2.imshow('src', img)
    return img


# 高斯滤波
def GausBlur(src):
    dst = cv2.GaussianBlur(src, (5, 5), 1.5)
    # cv2.imshow('GausBlur', dst)
    return dst


# 灰度处理
def Gray_img(src):
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    # cv2.imshow('gray', gray)
    return gray


# 二值化
def threshold_img(src):
    ret, binary = cv2.threshold(src, 230, 255, cv2.THRESH_BINARY)
    # cv2.bitwise_not(binary, binary)
    # ret, binary = cv2.threshold(src, 225, 255, cv2.THRESH_BINARY_INV)
    print("threshold value %s" % ret)
    # cv2.imshow('threshold', binary)
    return binary


# 开运算操作
def open_mor(src):
    kernel = np.ones((8, 8), np.uint8)
    opening = cv2.morphologyEx(src, cv2.MORPH_OPEN, kernel, iterations=3)  # iterations进行3次操作
    # cv2.imshow('open', opening)
    return opening

def close_mor(src):
    kernel = np.ones((8, 8), np.uint8)
    opening = cv2.morphologyEx(src, cv2.MORPH_CLOSE, kernel, iterations=3)  # iterations进行3次操作
    # cv2.imshow('close', opening)
    return opening

# 轮廓拟合
def draw_shape(open_img):
    cv2.imshow('under_purchase',open_img)
    h1, w1 = open_img.shape
    contours_, cnt = cv2.findContours(open_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(len(contours_))
    show = np.zeros([h1, w1], dtype=open_img.dtype)
    if len(contours_)==0:
        center=[]
    else:
        for contours in contours_:
            M = cv2.moments(contours)  # 计算第一条轮廓的各阶矩,字典形式
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            center=[center_x,center_y,1]
            cv2.drawContours(show, contours, 0, 255, -1)  # 绘制轮廓，填充
            cv2.circle(show, (center_x, center_y), 7, 128, -1)  # 绘制中心点
    return center

class PaintArea(QWidget):
    def __init__(self):
        super().__init__()
        # videoCaputer=cv2.VideoCapture(0)
        # videoCaputer.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # videoCaputer.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
        self.setGeometry(QtCore.QRect(1920, 0, 1920, 1200))
        self.setPalette(QPalette(QColor(0, 0, 0)))  # 设置背景颜色
        self.setAutoFillBackground(True)  # 设置窗口自动填充背景
        self.painter = QPainter()  # 创建绘图类
        self.painter.setRenderHint(QPainter.Antialiasing)
        self._timer = QTimer()
        self._timer.timeout.connect(self.repaintEvent)
        self.i = 500
        self.j = 100
        self._timer.start(1500)
        self.l = QRect(self.i-5, self.j-5, 4, 4)
        self.center_v=[]
        self.center_p=[]
        self.cam=cv2.VideoCapture(1)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
    def repaintEvent(self):
        if [self.i,self.j]==[1200,1000]:
            self._timer.stop()
            del self.center_v[0]
            del self.center_v[0]
            del self.center_p[0]
            del self.center_p[0]
            del self.center_v[0]
            k = []

            for index, value in enumerate(self.center_v):
                if value == []:
                    print(index)
                    k.append(index)
            for i in reversed(k):
                del self.center_v[i]
                del self.center_p[i]
            del self.center_p[-1]
            print('self.center_v', self.center_v)
            print('self.center_p', self.center_p)

            self.center_v=np.array(self.center_v)

            self.center_v=np.linalg.pinv(self.center_v)
            self.center_p = np.array(self.center_p)
            print(self.center_v.shape)
            print(self.center_p.shape)
            self.matrix=np.dot(self.center_v,self.center_p)
            b = np.array([[1,2,3]])
            # print(np.dot(self.l,self.matrix))
            # print(self.center_p)
            self.matrix = np.insert(self.matrix, 0, values=b, axis=0)
            self.matrix=self.matrix.tolist()
            np.savetxt('Matrix2.csv', self.matrix, delimiter=',')
        else:
            self.center_p.append([self.i, self.j, 1])
            flag, self.image = self.cam.read()  # 从视频流中读取
            show = cv2.resize(self.image, (1280, 960))  # 把读到的帧的大小重新设置为 640x480
            # cv2.imshow('show',show)
            gaus_img = GausBlur(show)
            # src = ReadImg()
            # gaus_img = GausBlur(src)
            gray_img = Gray_img(gaus_img)
            thres_img = threshold_img(gray_img)
            # close_img = close_mor(thres_img)
            open_img = open_mor(thres_img)
            center=draw_shape(open_img)
            self.center_v.append(center)
            cv2.waitKey(1000)
            # cv2.destroyWindow('show')
            cv2.destroyWindow('under_purchase')

            if self.j==1000:
                self.i += 100
                self.j = 100
            else:
                self.j += 100
            self.l.moveTo(self.i-5, self.j-5)
            self.update()
        # self._timer.stop()
    def paintEvent(self, event):  # 重写事件
        self.painter.begin(self)  # 开始
        self.painter.setRenderHints(QtGui.QPainter.Antialiasing)
        # self.rect_base.moveTo()
        self.painter.setBrush(QColor(0, 0, 0))  # 设置画刷用于填充
        self.painter.setPen(QPen(QColor(255, 255, 255), 6, Qt.SolidLine))  # 设置画笔，画边缘
        self.painter.drawEllipse(self.l)  # 画圆形
        self.painter.end()  # 结束
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # mainwindow = Ui_Form(cv2.VideoCapture(0))
    Painwindow = PaintArea()
    # mainwindow.show()
    Painwindow.show()
    sys.exit (app.exec_())

# src = ReadImg()
# gaus_img = GausBlur(src)
# gray_img = Gray_img(gaus_img)
# thres_img = threshold_img(gray_img)
# # close_img = close_mor(thres_img)
# open_img = open_mor(thres_img)
# draw_shape(open_img, src)
# cv2.waitKey(0)
