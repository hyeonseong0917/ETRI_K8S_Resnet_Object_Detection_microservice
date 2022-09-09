from crypt import methods
from doctest import REPORT_UDIFF
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

app = Flask(__name__)
client=MongoClient("129.254.202.111",27017)
hs_resnet=client['hs_resnet']
hs_requests=hs_resnet['hs_requests']
classes_to_labels=['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
        
def POSTPROCESSING():
    q={"STATUS": "INFERENCING_COMPLETE"}
    find_Q=hs_requests.find(q)
    
    for doc in find_Q:
        R_id=doc["_id"]
        hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"POSTPROCESSING"}})

        firsturi=os.path.join("http://129.254.202.111:30232","requestid",str(R_id),"status","POSTPROCESSING")
        print(firsturi)
        requests.put(firsturi)

        os.mkdir(os.path.join("/mnt",str(R_id),"tar_frame"))
        os.mkdir(os.path.join("/mnt",str(R_id),"target"))
        standard_img=cv2.imread(os.path.join("/mnt",str(R_id),"src_frame","frame_0.jpg"))
        frame_height=int(standard_img.shape[0])
        frame_width=int(standard_img.shape[1])

        output_name="target_"+str(R_id)+".avi"
        avi_path=os.path.join("/mnt",str(R_id),"target",output_name)
        out = cv2.VideoWriter(avi_path, 
                      cv2.VideoWriter_fourcc(*'DIVX'), 10, 
                      (frame_width, frame_height))

        for i in range(len(os.listdir(os.path.join("/mnt",str(R_id),"txts")))):
            txt_path=os.path.join("/mnt",str(R_id),"txts","infer"+str(i)+".txt")
            f=open(txt_path,'r')
            x1,y1,x2,y2,idx=0,0,0,0,0
            
            cnt=0
            total=[]
            coordinates=[]
            while True:
                line=f.readline()
                if not line:
                    break
                if cnt%5==0:
                    coordinates=[]
                    x1=np.float32(line)
                    coordinates.append(x1)
                elif cnt%5==1:
                    y1=np.float32(line)
                    coordinates.append(y1)
                elif cnt%5==2:
                    x2=np.float32(line)
                    coordinates.append(x2)
                elif cnt%5==3:
                    y2=np.float32(line)
                    coordinates.append(y2)
                elif cnt%5==4:
                    idx=int(line)
                    coordinates.append(idx)
                    total.append(coordinates)
                cnt+=1
                # print("cnt",cnt)                    
            f.close()
            print(coordinates,"\n")
            print(total,"\n")

            c=[]
            cd=np.array(c)
            tar_image_path=os.path.join("/mnt",str(R_id),"tar_frame","tar_"+str(i)+".jpg")                    
            
            print("total len:",len(total))
            image=cv2.imread(os.path.join("/mnt",str(R_id),"src_frame","frame_"+str(i)+".jpg"))
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            for j in range(len(total)):
                x1=total[j][0]
                y1=total[j][1]
                x2=total[j][2]
                y2=total[j][3]
                idx=total[j][4]
                
                
                orig_h, orig_w = image.shape[0], image.shape[1]
                x1, y1 = int(x1*255), int(y1*255)
                x2, y2 = int(x2*255), int(y2*255)
            
                x1, y1 = int((x1/255)*orig_w), int((y1/255)*orig_h)
                x2, y2 = int((x2/255)*orig_w), int((y2/255)*orig_h)

                print("x1:",x1,"y1:",y1,"x2:",x2,"y2",y2,"\n")            

                cd=cv2.rectangle(
                    image, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA
                )
            
                cd=cv2.putText(
                    image, classes_to_labels[idx], (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.8, (0, 255, 0), 2
                )
            if len(cd)>0:                
                imageio.imwrite(tar_image_path,cd)
            else:
                imageio.imwrite(tar_image_path,cv2.imread(os.path.join("/mnt",str(R_id),"src_frame","frame_"+str(i)+".jpg")))
        for i in range(len(os.listdir(os.path.join("/mnt",str(R_id),"tar_frame")))):            
            frame=cv2.imread(os.path.join("/mnt",str(R_id),"tar_frame","tar_"+str(i)+".jpg"))
            out.write(frame)
        out.release()            
        hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"POSTPROCESSING_COMPLETE"}})
        seconduri=os.path.join("http://129.254.202.111:30232","requestid",str(R_id),"status","POSTPROCESSING_COMPLETE")
        requests.put(seconduri)
    time.sleep(3)
cnt=0
while(1):
    print(cnt)
    POSTPROCESSING()
    cnt+=1    