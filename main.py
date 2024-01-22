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
        # self.radius = 0
        # 默认设置
        # self.r_size = 20  # 默认线宽
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
        # 鼠标坐标
        self.mouse_lct = QLabel('X: Y:', self)
        # 下拉框
        self.shape_box = QComboBox(self)
        self.shape_box.addItems(['圆', '正方形', '三角形'])
        # 是否中空
        self.is_hollow = QCheckBox('中空')
        self.is_hollow.setChecked(True)
        # 是否固定形状
        self.is_stable = QCheckBox('固定形状')
        self.is_stable.setChecked(True)
        # 自定义半径
        self.radius_box = QSpinBox(self)
        self.radius_box.setValue(0)
        self.radius_box.setMaximum(2147483647)
        # 自定义线宽
        self.r_size_box = QSpinBox(self)
        self.r_size_box.setValue(20)
        self.r_size_box.setMaximum(2147483647)
        self.r_size_box.setMinimum(0)
        # 自定义转角
        self.rotate_box = QSpinBox(self)
        self.rotate_box.setValue(0)
        self.rotate_box.setMaximum(180)
        self.rotate_box.setMinimum(-180)
        # 曝光按钮
        self.update_button = QPushButton('曝光', self)
        # 退出按钮
        self.quit_button = QPushButton('退出', self)
        
        # 组件布局
        layout = QVBoxLayout(self)
        # layout.addStretch(1)
        layout.addWidget(self.image_area, alignment = Qt.AlignCenter)
        layout.addWidget(self.mouse_lct, alignment = Qt.AlignRight)
        settings_layout = QGridLayout()
        settings_layout.addWidget(QLabel('形状', self), 0, 0, Qt.AlignRight)
        settings_layout.addWidget(self.shape_box, 0, 1, Qt.AlignLeft)
        settings_layout.addWidget(self.is_hollow, 0, 3, Qt.AlignLeft)
        settings_layout.addWidget(self.is_stable, 0, 5, Qt.AlignLeft)
        settings_layout.addWidget(QLabel('大小', self), 1, 0, Qt.AlignRight)
        settings_layout.addWidget(self.radius_box, 1, 1, Qt.AlignLeft)
        settings_layout.addWidget(QLabel('宽度', self), 1, 2, Qt.AlignRight)
        settings_layout.addWidget(self.r_size_box, 1, 3, Qt.AlignLeft)
        settings_layout.addWidget(QLabel('旋转', self), 1, 4, Qt.AlignRight)
        settings_layout.addWidget(self.rotate_box, 1, 5, Qt.AlignLeft)
        layout.addLayout(settings_layout)
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
        self.image_area.mousePressEvent = self.paint_event

        # self.is_stable.stateChanged.connect(self.paint_area_reset)
        self.is_stable.stateChanged.connect(self.checkbox_changed)
        self.is_hollow.stateChanged.connect(self.checkbox_changed)

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
        self.mouse_lct.setText(f'X: {x}, Y: {y}')
        if self.radius_tracking:
            self.end_point = event.pos()
            self.radius_box.setValue(self.calc_radius())
        self.update()
    
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.start_point is not None:
                self.paint_by_cv2(frame)
            #     if self.shape_box.currentText() == '圆':
            #         if self.is_hollow.isChecked(): # 空心
            #             cv2.circle(frame, (int(self.start_point.x()), int(self.start_point.y())), 
            #                self.radius_box.value(), (255, 255, 255), self.r_size_box.value())
            #         else: #实心
            #             cv2.circle(frame, (int(self.start_point.x()), int(self.start_point.y())), 
            #                self.radius_box.value(), (255, 255, 255), -1)
            #     elif self.shape_box.currentText() == '正方形':
            #         pass
            #     elif self.shape_box.currentText() == '三角形':
            #         pass
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(w, h, Qt.IgnoreAspectRatio)
            self.image_area.setPixmap(QPixmap.fromImage(p))
            self.image_area.lower()

    def paint_event(self, event):
        # 左键点击
        if event.buttons() == Qt.LeftButton:
            if self.is_stable.isChecked():
                self.start_point = event.pos()  # 获取鼠标位置确定圆心
                self.update()
                return
            else:
                if self.start_point is None or not self.radius_tracking: # 未确定圆心
                    self.start_point = event.pos()  # 获取鼠标位置确定圆心
                    self.radius_box.setValue(0)
                    self.radius_tracking = True # 根据鼠标位置实时绘画
                elif self.start_point is not None and self.radius_tracking: # 没有确定终点
                    self.radius_tracking = False # 停止跟踪
                self.update()
                return
        # 右键点击，全部重置
        if event.buttons() == Qt.RightButton:
            self.paint_area_reset()
            self.update()
            return

    def wheelEvent(self, event):# 滚轮事件
        if self.start_point is not None and self.is_hollow.isChecked():
            angle = event.angleDelta() / 8  # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
            angleY = angle.y()
            if angleY > 0:# 滚轮上滚
                if self.r_size_box.value() > 1:
                    self.r_size_box.setValue(self.r_size_box.value() - 1)
                    self.update()
            else:  # 滚轮下滚
                if self.r_size_box.value() < 2 * self.radius_box.value():
                    self.r_size_box.setValue(self.r_size_box.value() + 1)
                    self.update()
    
    def calc_radius(self):
        return int(math.sqrt(
            (self.start_point.x() - self.end_point.x()) ** 2 + (self.start_point.y() - self.end_point.y()) ** 2))
    
    def update_image(self):
        img = np.zeros((self.image_area.height(), self.image_area.width(), 3), np.uint8)
        if self.start_point is not None:
            self.paint_by_cv2(img)
        self.out_img = cv2.resize(img, (self.out_img.shape[1], self.out_img.shape[0]))
        cv2.imshow(self.out_win, self.out_img)
        # cv2.setWindowProperty(self.out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def paint_area_reset(self):
        self.start_point = None
        self.end_point = None
        self.radius_tracking = False
        # self.radius_box.setValue(0)

    def paint_by_cv2(self,img):
        if self.shape_box.currentText() == '圆':
            if self.is_hollow.isChecked(): # 空心
                cv2.circle(img, (int(self.start_point.x()), int(self.start_point.y())), 
                           self.radius_box.value(), (255, 255, 255), self.r_size_box.value())
            else: #实心
                cv2.circle(img, (int(self.start_point.x()), int(self.start_point.y())), 
                           self.radius_box.value(), (255, 255, 255), -1)
        elif self.shape_box.currentText() == '正方形':
            a = int(0.5* math.sqrt(2)*self.radius_box.value())
            p1 = (self.start_point.x() - a, self.start_point.y() - a)
            p2 = (self.start_point.x() + a, self.start_point.y() + a)
            if self.is_hollow.isChecked(): # 空心
                cv2.rectangle(img, p1, p2, (255, 255, 255), self.r_size_box.value())
            else: #实心
                cv2.rectangle(img, p1, p2, (255, 255, 255), -1)
        elif self.shape_box.currentText() == '三角形':
            r = self.radius_box.value()
            a = int(0.5 * r)
            b = int(0.5 * math.sqrt(3) * r)
            p1 = (self.start_point.x() + b, self.start_point.y() + a)
            p2 = (self.start_point.x()    , self.start_point.y() - int(r))
            p3 = (self.start_point.x() - b, self.start_point.y() + a)
            if self.is_hollow.isChecked(): # 空心
                cv2.line(img, p1, p2, (255, 255, 255), thickness = self.r_size_box.value())
                cv2.line(img, p2, p3, (255, 255, 255), thickness = self.r_size_box.value())
                cv2.line(img, p3, p1, (255, 255, 255), thickness = self.r_size_box.value())
            else: #实心
                pts = np.array([p1, p2, p3], np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.fillPoly(img, [pts], color=(255, 255, 255))

    def checkbox_changed(self):
        if self.is_hollow.isChecked():
            # 中空
            self.r_size_box.setReadOnly(False)
            self.r_size_box.setStyleSheet("")
        else:
            # 不中空
            self.r_size_box.setReadOnly(True)
            self.r_size_box.setStyleSheet("QSpinBox { background-color: grey; }")
        
        if self.is_stable.isChecked():
            # 如果固定形状
            self.radius_box.setReadOnly(False)
            self.rotate_box.setReadOnly(False)
            self.radius_box.setStyleSheet("")
            self.rotate_box.setStyleSheet("")
        else:
            # 形状不固定（鼠标绘制）
            self.radius_box.setReadOnly(True)
            self.r_size_box.setReadOnly(True)
            self.rotate_box.setReadOnly(True)
            self.radius_box.setStyleSheet("QSpinBox { background-color: grey; }")
            self.r_size_box.setStyleSheet("QSpinBox { background-color: grey; }")
            self.rotate_box.setStyleSheet("QSpinBox { background-color: grey; }")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DrawRect()
    window.show()
    sys.exit(app.exec_())
