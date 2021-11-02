# coding: utf-8
import dlib
import torchvision.transforms as trns
import torch
import cv2
import numpy as np
import time
from model.light_cnn import LightCNN_29Layers_v2
from model.aligment import FaceAligment
from PIL import Image

def _bbox_to_rect(bbox):
    """
    Convert a tuple in (left, top, right, bottom) order to a dlib `rect` object
    :param css:  plain tuple representation of the rect in (left, top, right, bottom) order
    :return: a dlib `rect` object
    """
    return dlib.rectangle(bbox[0], bbox[1], bbox[2], bbox[3])

def cv_to_cuda(image,device):
    image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    image = image.transpose((2,0,1))
    tensor = torch.from_numpy(image).to(device)
    tensor = tensor.float().div(255).unsqueeze(0)
    return tensor

class FaceExtractLightcnn:
    def __init__(self,device = 'cpu'):
        self.device = device
        self.shape_predictor = dlib.shape_predictor("./weight/shape_predictor_5_face_landmarks.dat")
        self.model = LightCNN_29Layers_v2(num_classes = 89816).to(self.device)
        self.model.load_state_dict(torch.load("./weight/lightcnn_weight.pth", map_location='cpu'))
        self.model.eval()
        self.cos = torch.nn.CosineSimilarity(dim=1, eps=1e-6)
    
    def get_face_encoding(self, image, face_rect=None):
        '''
        image must be 3-dimensional
        '''
        if len(image.shape) != 3:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        face_height, face_width = image.shape[:2]
        if face_rect is None:
            face_rect = _bbox_to_rect((0, 0, face_width, face_height))
        # face_pose = self.shape_predictor(image, face_rect)
        # chip = dlib.get_face_chip(image, face_pose)
        
        # print('chip')
        # cv2.imshow('chip',image)
        # cv2.waitKey(1)
        # chip = Image.fromarray(chip, 'RGB')
        embedding = self.model(cv_to_cuda(image,self.device))[1]
        return embedding.detach().numpy()

class LightCNN:
    def __init__(self):
        self.net = FaceExtractLightcnn(device='cpu')
    def predict(self,image):
        return self.net.get_face_encoding(image)


    # def preprocess(self, img):
    #     shape = self.shape_predictor(img, dlib.rectangle(0,0,img.shape[1], img.shape[0]))
    #     chip = dlib.get_face_chip(img, shape)
    #     chip = Image.fromarray(chip, 'RGB')
    #     return self.transform(chip).unsqueeze(0)
