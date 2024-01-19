import cv2

cam = cv2.VideoCapture(2)

while True:
    ret, frame = cam.read()  # 读取视频帧
    if ret:
        cv2.imshow('USB Camera', frame)  # 在窗口中显示视频帧
        if cv2.waitKey(1) & 0xFF == ord('q'):  # 按下 'q' 键退出循环
            break

cam.release()  # 释放摄像头
cv2.destroyAllWindows()  # 关闭所有窗口