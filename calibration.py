from PyQt5.QtCore import QObject
import cv2
import numpy as np
import json
import sys
from PyQt5.QtWidgets import QWidget
# from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time

camera_realtime = True
sleep_time = 0.5 # 间隔时间

class PrinterThread(QThread):
    reset_printer_signal = pyqtSignal(int, int)
    completed_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.init_out()
        self.mutex = QMutex() # 线程锁
        self.condition = QWaitCondition()
        self.is_waiting = False # 是否等待
        self.is_running = True # 正在运行
        
    def init_out(self):
        self.out_win = 'out_fullscreen' # 默认输出窗口名称
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
        self.out_geo = geometry
        self.reset_out_img()
        self.out_img = draw_center_cross(self.out_img)
        cv2.imshow(self.out_win, self.out_img)
        cv2.setWindowProperty(self.out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        print('投影设置完成')

    def reset_out_img(self):
        self.out_img = np.zeros((self.out_geo.height(), self.out_geo.width(), 3), np.uint8)
    
    def update_out_window(self):
        cv2.imshow(self.out_win, self.out_img)
        cv2.setWindowProperty(self.out_win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    def run(self):
        # self.reset_out_img()
        l_unit = int(min(self.out_img.shape[0], self.out_img.shape[1]) * 0.1) # 单位间隔
        c_point = (self.out_img.shape[1] // 2, self.out_img.shape[0] // 2)
        for i in range(5):
            # print(f'i = {i}')
            if i == 0:
                self.reset_out_img()
                self.out_img = draw_circle(self.out_img, c_point)
                self.update_out_window()
                self.reset_printer_signal.emit(c_point[0], c_point[1])
                self.wait_signal()
                continue
            for j in range(8):
                if not self.is_running : 
                    print('进程终止')
                    return
                self.reset_out_img()
                point = get_point_by_radius(c_point, l_unit*i, j)
                self.out_img = draw_circle(self.out_img, point)
                self.update_out_window()
                self.reset_printer_signal.emit(point[0], point[1])
                self.wait_signal()
        self.completed_signal.emit()

    def wait_signal(self):
        self.mutex.lock()
        self.is_waiting = True
        self.condition.wait(self.mutex)
        self.mutex.unlock()
    
    def resume(self):
        self.is_waiting = False
        self.condition.wakeAll()

    def kill(self):
        self.is_running = False
        # print('进程终止')
        # return

class CameraThread(QThread):
    camera_list_signal = pyqtSignal(list)
    
    def __init__(self) -> None:
        super().__init__()
        self.is_waiting = False # 等待
        self.is_running = True
        self.cam_list = []
        self.cam_width = 600 # 视频最大宽度
        self.mutex = QMutex() # 线程锁
        self.condition = QWaitCondition()
        self.frame = None
    
    def get_camera_list(self):
        # 读取相机列表
        print('正在读取相机')
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not cap.isOpened():
                break
            self.cam_list.append('相机' + str(i+1))
            cap.release()
            print(f'已读取到相机{i+1}...')
        self.camera_list_signal.emit(self.cam_list)
        print('读取相机列表完成')
    
    def reset(self, cap_num):
        self.is_waiting = True # 暂停
        print(f'reset as cam {cap_num + 1}')
        self.frame = None
        self.cap = cv2.VideoCapture(cap_num, cv2.CAP_DSHOW)
        # 读取原本宽高
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # 等比重置宽高
        if width > self.cam_width:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(self.cam_width/width*height))
        self.resume()
    
    def run(self):
        self.get_camera_list()
        self.reset(0)
        while self.is_running:
            self.mutex.lock()
            if self.is_waiting:
                self.condition.wait(self.mutex)
            ret, frame = self.cap.read()
            if ret: self.frame = frame
            self.mutex.unlock()
    
    def resume(self):
        self.is_waiting = False
        self.condition.wakeAll()
    
    def kill(self):
        self.is_running = False


class CameraCali(QWidget):
    change_camera_signal = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.win_name = 'Camera Calibration' # 默认输出窗口名称
        self.start_cali = False # 是否开始校准程序
        self.center_point = None # 识别到的中心点
        self.init_ui()
        self.init_pinter()
        if camera_realtime:
            self.init_camera()
        else:
            self.brg_frame = cv2.imread('pic.jpg')

    def init_ui(self):
        self.setWindowTitle('相机校准')
        # 下拉框
        self.camera_box = QComboBox(self)
        # 图像显示区域
        self.image_area = QLabel(self)
        # 阈值
        self.thresh_slider = QSlider(Qt.Horizontal)
        self.thresh_slider.setRange(0 , 255)
        self.thresh_slider.setValue(128)
        # 显示样式
        self.image_type_box = QComboBox(self)
        self.image_type_box.addItems(['原图', '阈值黑白图'])
        self.image_type_box.setFixedWidth(100)
        # 开始校准按钮
        self.start_cali_button = QPushButton('开始校准', self)
        # 重新设置阈值
        self.restart_button = QPushButton('重设阈值', self)

        # 信号与槽连接
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        # self.timer.timeout.connect(self.update_out_window)
        self.timer.start(30)
        self.camera_box.currentIndexChanged.connect(self.reset_camera)
        self.thresh_slider.valueChanged.connect(self.update_frame)
        self.start_cali_button.clicked.connect(self.cali_start_func)
        self.restart_button.clicked.connect(self.restart)
        self.image_type_box.currentIndexChanged.connect(self.update_frame)
        
        # 组件布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.camera_box)
        layout.addWidget(self.image_area, alignment = Qt.AlignCenter)
        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(self.thresh_slider)
        thresh_layout.addWidget(self.image_type_box)
        layout.addLayout(thresh_layout)
        layout.addWidget(self.start_cali_button)
        layout.addWidget(self.restart_button)

    def init_camera(self):
        self.camera_thread = CameraThread()
        # 信号连接（线程->主程序）
        self.camera_thread.camera_list_signal.connect(self.reset_cam_list)
        # 信号连接（主程序->线程）
        self.change_camera_signal.connect(self.camera_thread.reset)
        # 开始进程
        self.camera_thread.start()
    
    def init_pinter(self):
        self.printer_thread = PrinterThread()
        # 信号连接（线程->主程序）
        self.printer_thread.reset_printer_signal.connect(self.cali_get_points)
        self.printer_thread.completed_signal.connect(self.output_text)

    def reset_cam_list(self, cam_list):
        for cam_name in cam_list:
            self.camera_box.addItem(cam_name)
        self.camera_box.setCurrentIndex(0)
        self.reset_camera()
    
    def reset_camera(self):
        self.change_camera_signal.emit(self.camera_box.currentIndex())
    
    def update_frame(self):
        self.center_point = None
        if camera_realtime: # 实时成像
            frame = self.camera_thread.frame
        else: # 图片
            frame = self.brg_frame
        if frame is None: return
        frame_bi = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _ , frame_bi = cv2.threshold(frame_bi, self.thresh_slider.value(), 255, cv2.THRESH_BINARY)
        # 找到中心
        self.center_point = find_center(frame_bi)
        # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.image_type_box.currentIndex() == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif self.image_type_box.currentIndex() == 1:
            frame = cv2.cvtColor(frame_bi, cv2.COLOR_GRAY2RGB)
        # 画十字
        if self.center_point is not None:
            frame = draw_cross(frame, self.center_point, 10)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(w, h, Qt.IgnoreAspectRatio)
        self.image_area.setPixmap(QPixmap.fromImage(p))

    def cali_start_func(self):
        self.start_cali = True
        self.thresh_slider.setDisabled(True)
        self.points_cam = []
        self.points_scr = []
        self.printer_thread.start()

    def restart(self):
        self.printer_thread.kill()
        self.init_pinter()
        self.timer.start(30)
        self.start_cali = False
        self.thresh_slider.setDisabled(False)
    
    def cali_get_points(self, x, y): #调试用的函数
        # 停止自动更新图像区域
        self.timer.stop()
        time.sleep(sleep_time)
        self.update_frame()
        if self.center_point is not None:
            self.points_scr.append([x, y])
            self.points_cam.append(self.center_point)
            print([x, y], self.center_point)
        else:
            print(f'{[x, y]}: not found')
        # 继续更新图像区域
        self.timer.start(30)
        # 继续进程
        self.printer_thread.resume()
    
    def output_text(self):# 输出变换矩阵
        points_len = len(self.points_cam)
        if points_len == 0: # 没有匹配的点
            pass
        elif points_len < 4: #
            pass
        np.savetxt('points_scr.csv', self.points_scr, delimiter = ',', fmt='%d')
        np.savetxt('points_cam.csv', self.points_cam, delimiter = ',', fmt='%d')
        print('ok')

def draw_center_cross(img, line_w=2):
    c_x = img.shape[1] // 2
    c_y = img.shape[0] // 2
    # cross_lx = int(img.shape[1] * 0.1)
    # cross_ly = int(img.shape[0] * 0.1)
    cross_l = int(min(img.shape[0], img.shape[1]) * 0.1)
    # img = cv2.line(img, (c_x - cross_lx, c_y), (c_x + cross_lx, c_y), (255, 255, 255), line_w)
    # img = cv2.line(img, (c_x, c_y - cross_ly), (c_x, c_y + cross_ly), (255, 255, 255), line_w)
    img = cv2.line(img, (c_x - cross_l, c_y), (c_x + cross_l, c_y), (255, 255, 255), line_w)
    img = cv2.line(img, (c_x, c_y - cross_l), (c_x, c_y + cross_l), (255, 255, 255), line_w)
    img = cv2.circle(img, (c_x, c_y), int(0.4 * cross_l), (0, 0, 0), -1)
    for i in range(-1,2):
        for j in range(-1,2):
            img = draw_circle(img, (c_x + i*cross_l, c_y + j*cross_l))
    return img

def draw_circle(img, center):
    return cv2.circle(img, center, 3, (255, 255, 255), -1)

def draw_cross(img, center, cr_size):
    cv2.line(img, (center[0]-cr_size, center[1]), (center[0]+cr_size, center[1]), (255, 0, 0), int(cr_size/5))
    cv2.line(img, (center[0], center[1]-cr_size), (center[0], center[1]+cr_size), (255, 0, 0), int(cr_size/5))
    return img

# 轮廓拟合
def find_center(binary_img):
    # 边缘检测
    contours= cv2.findContours(binary_img, cv2.RETR_TREE, 
                                cv2.CHAIN_APPROX_SIMPLE)[0]
    cX = None
    cY = None
    for i in contours:
        M = cv2.moments(i)
        if M["m00"] :
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])
            if cX is None or x < cX:
                cX = x
                cY = y
    if cX is not None and cY is not None:
        return [cX, cY]
    else:
        return

def get_point_by_radius(p_center, radius, index):
    # index = [0, 8)
    angle = index * 0.25*np.pi
    x = p_center[0] + radius * np.sin(angle)
    y = p_center[1] - radius * np.cos(angle)
    return (int(x), int(y))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraCali()
    window.show()
    sys.exit(app.exec_())