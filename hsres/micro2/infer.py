from crypt import methods
from fileinput import filename
from flask import Flask, render_template, request,jsonify
from werkzeug.utils import secure_filename
import os
import os.path
import shutil
import json
from pymongo import MongoClient
import pymongo
import datetime
import sys
from flask import send_file
from bson.objectid import ObjectId
import pandas as pd
import imageio
import PIL.Image as pilimg
import torch
import torchvision.transforms as transforms
from torch import nn
import cv2
import numpy as np
import time
import requests

ssd_model = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_ssd',force_download=True)
ssd_model.eval()
utils = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_ssd_processing_utils')

from ssd.model import SSD300, ResNet
from ssd.utils import dboxes300_coco, Encoder

app = Flask(__name__)
client=MongoClient("129.254.202.111",27017)
hs_resnet=client['hs_resnet']
hs_requests=hs_resnet['hs_requests']

def decode_results(predictions):
    dboxes = dboxes300_coco()
    encoder = Encoder(dboxes)
    ploc, plabel = [val.float() for val in predictions]
    results = encoder.decode_batch(ploc, plabel, criteria=0.5, max_output=20)

    return [ [ pred.detach().cpu().numpy()
               for pred in detections
             ]
             for detections in results
           ]


def pick_best(detections, treshold):
    bboxes, classes, confidences = detections
    best = np.argwhere(confidences > 0.3).squeeze(axis=1)

    return [pred[best] for pred in detections]

transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((300, 300)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

def INFER():
    ssd_model = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_ssd')
    ssd_model.eval()
    utils = torch.hub.load('NVIDIA/DeepLearningExamples:torchhub', 'nvidia_ssd_processing_utils')
    classes_to_labels = utils.get_coco_object_dictionary()

    q={"STATUS": "PREPROCESSING_COMPLETE"}
    find_Q=hs_requests.find(q)

    for doc in find_Q:
        filename=doc["FILENAME"]
        R_id=doc["_id"]
        print(R_id)
        hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"INFERENCING"}})

        firsturi=os.path.join("http://129.254.202.111:30232","requestid",str(R_id),"status","INFERENCING")
        requests.put(firsturi)

        os.mkdir(os.path.join("/mnt",str(R_id),"txts"))
        for i in range(len(os.listdir(os.path.join("/mnt",str(R_id),"src_frame")))):
            f_name="frame_"+str(i)+".jpg"
            frame=cv2.imread(os.path.join("/mnt",str(R_id),"src_frame",f_name))
            transformed_frame = transform(frame) # [3,300,300] (channel * h * w)
            tensor = torch.tensor(transformed_frame, dtype=torch.float32) 
            tensor = tensor.unsqueeze(0) # [1,3,300,300] (b * channel * h* w)
            print(tensor.shape)
            with torch.no_grad():
                detections = ssd_model(tensor)
            results_per_input = decode_results(detections)
            best_results_per_input = [utils.pick_best(results, 0.1) for results in results_per_input]
            
            infer_name="infer"+str(i)+".txt"
            with open(os.path.join("/mnt",str(R_id),"txts",infer_name),'a') as f:
                for image_idx in range(len(best_results_per_input)):
                    bboxes,classes,confidences=best_results_per_input[image_idx]
                    for idx in range(len(classes)):
                        x1,y1,x2,y2=bboxes[idx]

                        f.write(str(x1)+'\n')
                        f.write(str(y1)+'\n')
                        f.write(str(x2)+'\n')
                        f.write(str(y2)+'\n')
                        f.write(str(classes[idx]-1)+'\n')
            f.close()
        if len(os.listdir(os.path.join("/mnt",str(R_id),"txts")))==0:
            print("INFERENCE_ERROR")
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"INFERENCING_ERROR"}})
        else:
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"INFERENCING_COMPLETE"}})
            seconduri=os.path.join("http://129.254.202.111:30232","requestid",str(R_id),"status","INFERENCING_COMPLETE")
            requests.put(seconduri)
    time.sleep(3)

cnt=0    
while(1):
    
    print(cnt)
    INFER()
    cnt+=1