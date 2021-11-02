#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 18 18:35:06 2021

@author: pomchi
"""
import sys
sys.path.append('/home/pomchi/jimmy-development/face_recogination/retain_demo/model/')

import os
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from utils.functions.prior_box import PriorBox
from utils.nms.py_cpu_nms import py_cpu_nms
import cv2
from model.models.retinaface import RetinaFace
from utils.box_utils import decode, decode_landm

def check_keys(model, pretrained_state_dict):
    ckpt_keys = set(pretrained_state_dict.keys())
    model_keys = set(model.state_dict().keys())
    used_pretrained_keys = model_keys & ckpt_keys
    unused_pretrained_keys = ckpt_keys - model_keys
    missing_keys = model_keys - ckpt_keys
    print('Missing keys:{}'.format(len(missing_keys)))
    print('Unused checkpoint keys:{}'.format(len(unused_pretrained_keys)))
    print('Used keys:{}'.format(len(used_pretrained_keys)))
    assert len(used_pretrained_keys) > 0, 'load NONE from pretrained checkpoint'
    return True


def remove_prefix(state_dict, prefix):
    ''' Old style model is stored with all names of parameters sharing common prefix 'module.' '''
    print('remove prefix \'{}\''.format(prefix))
    f = lambda x: x.split(prefix, 1)[-1] if x.startswith(prefix) else x
    return {f(key): value for key, value in state_dict.items()}


def load_model(model, pretrained_path, load_to_cpu):
    print('Loading pretrained model from {}'.format(pretrained_path))
    if load_to_cpu:
        pretrained_dict = torch.load(pretrained_path, map_location=lambda storage, loc: storage)
    else:
        device = torch.cuda.current_device()
        pretrained_dict = torch.load(pretrained_path, map_location=lambda storage, loc: storage.cuda(device))
    if "state_dict" in pretrained_dict.keys():
        pretrained_dict = remove_prefix(pretrained_dict['state_dict'], 'module.')
    else:
        pretrained_dict = remove_prefix(pretrained_dict, 'module.')
    check_keys(model, pretrained_dict)
    model.load_state_dict(pretrained_dict, strict=False)
    return model

class Retinaface:
    def __init__(self):
        self.cfg = {
                'name': 'mobilenet0.25',
                'min_sizes': [[16, 32], [64, 128], [256, 512]],
                'steps': [8, 16, 32],
                'variance': [0.1, 0.2],
                'clip': False,
                'loc_weight': 2.0,
                'gpu_train': True,
                'batch_size': 32,
                'ngpu': 1,
                'epoch': 250,
                'decay1': 190,
                'decay2': 220,
                'image_size': 640,
                'pretrain': False,
                'return_layers': {'stage1': 1, 'stage2': 2, 'stage3': 3},
                'in_channel': 32,
                'out_channel': 64
            }

        self.net = RetinaFace(cfg=self.cfg, phase = 'test')##.cuda()
        self.net = load_model(self.net, './weight/mobilenet0.25_Final.pth', True)
        self.size = (640,480)
        self.device = 'cpu'
        self.threshold = 0.9
        self.topK = 1000
        self.nms_threshold = 0.4
        self.keep_top_k = 500
    def detect(self,image):
        """

        Parameters
        ----------
        image : TYPE
            DESCRIPTION.

        Returns
        -------
        locs : TYPE
            x,y,x,y
        scores : TYPE
            Confidence score.
        lands : TYPE
            With crop face location.    

        """
        img = np.float32(image)

        im_height, im_width, _ = img.shape
        scale = torch.Tensor([img.shape[1], img.shape[0], img.shape[1], img.shape[0]])
        # img -= (104, 117, 123)
        img = img.transpose(2, 0, 1)
        img = torch.from_numpy(img).unsqueeze(0)
        img = img.to(self.device)
        scale = scale.to(self.device)

        loc, conf, landms = self.net(img)  # forward pass

        priorbox = PriorBox(self.cfg, image_size=(im_height, im_width))
        priors = priorbox.forward()
        priors = priors.to(self.device)
        prior_data = priors.data
        boxes = decode(loc.data.squeeze(0), prior_data, self.cfg['variance'])
        boxes = torch.clamp(boxes,0,1)
        boxes = boxes * scale / 1
        boxes = boxes.cpu().numpy()
        scores = conf.squeeze(0).data.cpu().numpy()[:, 1]
        landms = decode_landm(landms.data.squeeze(0), prior_data, self.cfg['variance'])
        scale1 = torch.Tensor([img.shape[3], img.shape[2], img.shape[3], img.shape[2],
                               img.shape[3], img.shape[2], img.shape[3], img.shape[2],
                               img.shape[3], img.shape[2]])
        scale1 = scale1.to(self.device)
        landms = landms * scale1 / 1
        landms = landms.cpu().numpy()

        # ignore low scores
        inds = np.where(scores > self.threshold)[0]
        boxes = boxes[inds]
        landms = landms[inds]
        scores = scores[inds]

        # keep top-K before NMS
        order = scores.argsort()[::-1][:self.topK]
        boxes = boxes[order]
        landms = landms[order]
        scores = scores[order]

        # do NMS
        dets = np.hstack((boxes, scores[:, np.newaxis])).astype(np.float32, copy=False)
        keep = py_cpu_nms(dets, self.nms_threshold)
        # keep = nms(dets, args.nms_threshold,force_cpu=args.cpu)
        dets = dets[keep, :]
        landms = landms[keep]

        # keep top-K faster NMS
        dets = dets[:self.keep_top_k, :]
        landms = landms[:self.keep_top_k, :]

        dets = np.concatenate((dets, landms), axis=1)
        locs = dets[:,:4].reshape(-1,4)
        scores = dets[:,4].reshape(-1,1)
        lands = dets[:,5:].reshape(-1,5,2)
        
        lands[:,:,0] -= np.repeat(locs[:,0],5,axis=0).reshape(-1,5)
        lands[:,:,1] -= np.repeat(locs[:,1],5,axis=0).reshape(-1,5)
        
        return locs,scores,lands
        
