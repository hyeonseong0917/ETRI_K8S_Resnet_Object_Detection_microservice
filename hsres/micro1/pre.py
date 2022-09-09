from crypt import methods
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
from bson.objectid import ObjectId
import json

app = Flask(__name__)
client=MongoClient("129.254.202.111",27017)
hs_resnet=client['hs_resnet']
hs_requests=hs_resnet['hs_requests']

@app.route('/upload')
def render_file():
    return render_template("upload.html")

@app.route('/fileUpload',methods=['GET','POST'])
def init_upload():
    if request.method=='POST':
        f=request.files['file']
        f.save(secure_filename(f.filename))
        req={
            "FILENAME": f.filename,
            "STATUS": "ENQUEUE",
            "PROCESS_START": datetime.datetime.now(),
            "PREPROCESSING_START": datetime.datetime.now(),
            "PREPROCESSING_END": "WAITING..",
            "INFERENCING_START": "WAITING..",
            "INFERENCING_END": "WAITING..",
            "POSTPROCESSING_START": "WAITING..",
            "POSTPROCESSING_END": "WAITING..",
            "PROCESS_END": "WAITING..",
            "TOTAL": "WAITING..."
        }            
        R_id=hs_resnet.hs_requests.insert_one(req).inserted_id
        os.mkdir(os.path.join("/mnt",str(R_id)))
        os.mkdir(os.path.join("/mnt",str(R_id),"src"))
        os.mkdir(os.path.join("/mnt",str(R_id),"src_frame"))

        saved_file_path=os.path.abspath(f.filename)
        copy_file_path=os.path.join("/mnt",str(R_id),"src",secure_filename(f.filename))
        shutil.copyfile(saved_file_path,copy_file_path)
        if not os.path.exists(copy_file_path):
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"ENQUEUE_ERROR"}})
            return
        else:
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"PREPROCESSING"}})

        cap=cv2.VideoCapture(os.path.join(copy_file_path))
        if cap.isOpened()==False:
            print("OPEN ERROR")
            return
        fcnt=0
        while(cap.isOpened()):
            ret, frame = cap.read()
            if ret == True:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                f_name="frame_"+str(fcnt)+".jpg"
                jpgPath=os.path.join("/mnt",str(R_id),"src_frame",f_name)
                imageio.imwrite(jpgPath, frame)
                fcnt+=1
            else:
                break
        if len(os.listdir(os.path.join("/mnt",str(R_id),"src_frame")))==0:
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"FRAME_CONVERT_ERROR"}})
            print("STATUS: FRAME_CONVERT_ERROR")
        else:
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"STATUS":"PREPROCESSING_COMPLETE"}})
            hs_resnet.hs_requests.update_one({"_id":R_id},{"$set":{"PREPROCESSING_END":datetime.datetime.now()}})

        return render_template("resorback.html",ID=str(R_id))

@app.route('/result',methods=['GET','POST'])
def result():
    result_DB=[]
    for d in hs_resnet["hs_requests"].find():
        result_DB.append(d)        
    return render_template("result.html",result_DB=result_DB)

@app.route('/<R_id>/download',methods=['GET','POST'])        
def Download(R_id):           
    return send_file(os.path.join("/mnt",str(R_id),"target","target_"+str(R_id)+".avi"),as_attachment=True)


@app.route('/<R_id>/delete',methods=['GET','POST'])    
def Delete(R_id):
    hs_doc=hs_requests.find({})
    for to_delete in hs_doc:
        if str(to_delete["_id"])==R_id:
            hs_resnet.hs_requests.delete_one({"_id":to_delete["_id"]})
            shutil.rmtree(os.path.join("/mnt","movies",str(R_id)))
            break
    return render_template("resdelete.html",ID=str(R_id))

@app.route('/requestid/<request_id>/status/<status>',methods=['PUT','GET','POST'])
def update_timeline(request_id, status):
    print("rid: ", request_id, "status: ",status)
    if status=="INFERENCING":
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"INFERENCING_START":datetime.datetime.now()}})
    elif status=="INFERENCING_COMPLETE":
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"INFERENCING_END":datetime.datetime.now()}})
    elif status=="POSTPROCESSING":
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"POSTPROCESSING_START":datetime.datetime.now()}})    
    elif status=="POSTPROCESSING_COMPLETE":
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"POSTPROCESSING_END":datetime.datetime.now()}})
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"PROCESS_END":datetime.datetime.now()}})
        curTime=datetime.datetime.now()
        Q={"_id": ObjectId(request_id)}
        d=hs_requests.find(Q)
        for i in d:
            curTime=i["PROCESS_START"]
        hs_resnet.hs_requests.update_one({"_id":ObjectId(request_id)},{"$set":{"TOTAL":str(datetime.datetime.now()-curTime)}})        
    return jsonify({"status": status})     
if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,threaded=True)