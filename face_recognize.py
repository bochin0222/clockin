import time
import threading

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
import numpy as np

import fe_lightcnn
from model.fd_retain import Retinaface
from model.aligment import FaceAligment

class Thread(QThread):
    camera_frame = pyqtSignal(QImage)
    regist_frame = pyqtSignal(QImage)
    regist_img = pyqtSignal(np.ndarray)
    identify_img = pyqtSignal(np.ndarray)
    status_text = pyqtSignal(str)
    count_text = pyqtSignal(str)
    def __init__(self):
        super(Thread, self).__init__()
        self.detector = Retinaface()
        self.aliger = FaceAligment()
        self.embd_model = fe_lightcnn.LightCNN()
        self.cap = cv2.VideoCapture(0)
        self.face_allow_size = 100
        self.start_recognize = False
        self.mode = "identify"
        self.first_frame = False
        self.frame_count = 0
        self.landmarks=[]

    def _largest_face(self, boxes):
        if len(boxes) == 1:
            return 0

        face_areas = [(int(box[2]) - int(box[0])) * (int(box[3]) - int(box[1])) for box in boxes]

        largest_area = face_areas[0]
        largest_index = 0
        for index in range(1, len(boxes)):
            if face_areas[index] > largest_area:
                largest_index = index
                largest_area = face_areas[index]
        return largest_index
    
    def send_crop_img(self,image,mode):
        print("qqq")
        image = cv2.resize(image,(150,150))
        if mode == "register":
            self.regist_img.emit(image)
        elif mode == "identify":
            self.identify_img.emit(image)

    def show_on_qtlabel(self,frame,mode):
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        
        p = convertToQtFormat.scaled(320, 521)
        if mode == "identify":
            self.camera_frame.emit(p)
        elif mode == "register":
            self.regist_frame.emit(p)

    def run(self):

        while True:
                
            ret, frame = self.cap.read()
            frame = frame[0:480,160:480]
            if self.start_recognize:
                if self.frame_count % 20 == 0:
                    self.frame_count = 0
                    dets = self.detector.detect(frame)
                    boxes, scores, lands = dets
                    if len(boxes) > 0:
                        self.status_text.emit('辨識中..')
                        largest_index = self._largest_face(boxes)
                        box = boxes[largest_index]
                        land = lands[largest_index]
                        # 加寬 face detect area 
                        width = box[2] - box[0]
                        height = box[3] - box[1]
                        add_width = width // 10
                        add_height= height // 10
                        left_bound = int(box[0] - add_width) if box[0] - add_width >= 0 else 0
                        rigth_bound = int(box[2] + add_width) if box[2] + add_width < 320 else 320
                        top_bound = int(box[1] - add_height) if box[1] - add_height >= 0 else 0
                        bottom_bound = int(box[3] + add_height) if box[3] + add_height < 568 else 568
                        for i in land:
                            i[0] = int(i[0] + left_bound)
                            i[1] = int(i[1] + top_bound)

                        if (width * height) > self.face_allow_size ** 2:
                            # register mode													
                            if self.mode == "register":
                                if not self.first_frame :
                                    self.first_frame = True
                                    start_time = time.time()
                                if self.first_frame:
                                    if (start_time + 3) - time.time() > 0:
                                        self.count_text.emit(str(int((start_time + 3) - time.time() + 1)))
                                    else:
                                        crop_img =  frame[top_bound:bottom_bound, left_bound:rigth_bound]

                                        self.landmarks = land
                                        t = threading.Thread(target = self.send_crop_img,args = (crop_img,self.mode,))
                                        t.start()
                                        self.first_frame = False
                                        self.start_recognize = False
                            # identify mode
                            elif self.mode == "identify":
                                crop_img =  frame[top_bound:bottom_bound, left_bound:rigth_bound]
                                self.landmarks = land
                                t = threading.Thread(target = self.send_crop_img,args = (crop_img,self.mode,))
                                t.start()
                                self.start_recognize = False
                        else:

                            self.first_frame = False
                            self.count_text.emit("請靠近一點")
                            self.status_text.emit('請靠近一點')
                    else:
                        self.first_frame = False
                        self.count_text.emit("請將臉放入框內")
                        self.status_text.emit('將臉放在畫面')
                self.frame_count += 1
            self.show_on_qtlabel(frame,self.mode)
    def _stop(self):
        self.start_recognize = False
