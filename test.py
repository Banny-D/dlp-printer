import cv2
import numpy as np


p_cam = np.array([[0,0],[3,4],[7,8],[5,9]], dtype=np.float32)
p_scr = np.array([[0,0],[6,8],[14,16],[10,18]], dtype=np.float32)
M = cv2.findHomography(p_cam, p_scr)[0]
print(p_cam)
print(p_scr)
print()
print(M)