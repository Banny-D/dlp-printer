import cv2
import numpy as np
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()  # 读取视频帧
    if ret:
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # img = cv2.addWeighted(frame, 1.5, 0,0,0)
        cv2.imshow('USB Camera', frame)  # 在窗口中显示视频帧
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 按下 'q' 键退出循环
            break

cam.release()  # 释放摄像头
cv2.destroyAllWindows()  # 关闭所有窗口