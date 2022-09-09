# Pytorch Resnet Object Detection Microservices

<!-- <span style="color:grey"> -->
## Pytorch Resnet Object Detection Microservice 구조

___
- ## 전체 구조
- 작업 상태 구조 및 DB 구조 
- 폴더 구조
  - micro1
    - docker
    - yaml파일들 + (Service)
    - pre.py
    - requirements.txt
  - micro2
    - docker
    - yaml파일들
    - infer.py
    - requirements.txt
  - micro3
    - docker
    - yaml파일들
    - pody.py
    - requirements.txt 
  - clusterrole.yaml
  - clusterrolebinding.yaml
- 시연 과정 및 화면
  - mp4파일을 프레임 단위로 저장하는 PreProcessing
  - 저장된 프레임 단위 이미지를 Resnet50 기반 SSD300 모델을 통해 Inferencing
  - 각각 Inferencing된 결과를 프레임 번호에 해당하는 txt파일에 저장 
  - txt파일과 저장된 프레임을 결합해 탐지된 객체에 BOX가 BOUNDING된 새 프레임을 만들고 avi파일로 만드는 PostProcessing  
  - Kubernetes Python Api를 사용해 Deployment의 Replicaset 조정

# Pytorch로 Resnet Object Detection 을 이용해  Bounding Box를 진행하는 프로젝트의 흐름도
![default](image/flow.PNG)

# Pytorch Resnet Object Detection Microservice 프로젝트의 구조
![default](image/res_arch.PNG)


# 작업 상태 구조 및 DB 구조
- ## lifecycle과 DB 및 마이크로 서비스 간 구조는 다음과 같은 상태로 구성되어 있습니다.

![default](image/res_lifecycle.PNG)

- ObjectId: MongoDB에 데이터를 저장할 때 별도로 지정하지 않은 경우 자동으로 부여되는 값
- FILENAME: 가장 초기에 Request로 들어온 File의 이름
- STATUS: 6개의 정상 상태(ENQUEUE, PREPROCESSING, PREPROCESSING_COMPLETE, INFERENCING, INFERENCING_COMPLETE,POSTPROCESSING, POSTPROCESSING_COMPLETE), 4개의 비정상 상태(ENQUEUE_ERROR, FRAME_CONVERT_ERROR, INFERENCING_ERROR, POSTPROCESSING_ERROR)로 총 10개가 존재
- PROCESS_START: Request가 DB에 들어갔을 때의 Pod1에서의 시간
- PREPROCESSING_START: PREPROCESSING 작업을 시작할 때의 시간
- PREPROCESSING_END: PREPROCESSING 작업을 완료했을 때의 시간
- INFERENCING_START: INFERENCING 작업을 시작할 때의 시간
- INFERENCING_END: INFERENCING 작업을 완료했을 때의 시간 
- POSTPROCESSING_START: POSTPROCESSING 작업을 시작할 때의 시간
- POSTPROCESSING_END: POSTPROCESSING 작업을 완료했을 때의 시간 
- PROCESS_END: 전체적인 작업을 완료했을 때의 시간
- TOTAL: 전체 작업을 완료하는데 소요된 시간 (PROCESS_END - PROCESS_START)


폴더구조
- hs_res
  - hsdef
    - hsdef.py 
  - micro1
    - docker
      - Dockerfile
    - pre-deploy.yaml
    - pre-PV.yaml
    - pre-PVC.yaml
    - pre-SVC.yaml
    - pre.py
    - micro1_python_k8s_api.py
    - requirements.txt
  - micro2
    - docker
      - Dockerfile
    - infer-deploy.yaml
    - infer.py
    - requirements.txt
  - micro3
    - docker
      - Dockerfile
    - post-deploy.yaml
    - post.py
    - micro3_python_k8s_api.py
    - requirements.txt
  - templates
    - resdelete.html
    - resorback.html
    - result.html
    - upload.html
  - clusterrole.yaml
  - clusterrolebinding.yaml
  - micro1_restart.sh
  - micro2_restart.sh
  - micro3_restart.sh


**resdef**
- resdef.py: 자주 사용되는 변수들을 모듈 형태로 저장한 파일입니다.


**micro1**
- docker/Dockerfile: docker 컨테이너를 빌드할 수 있는 Dockerfile이 있는 디렉토리 입니다.
- pre-deploy.yaml: mp4에서 각 프레임을 넘버링 된 jpg로 변환하는 Pod를 실행할 수 있는 yaml파일 입니다.
    타입은 Deployment이며, /mnt/ 위치에 Persistent Volume(PV)를 생성합니다. 해당 PV는 hyeonseong-nfs-pvc라는 이름을 가진 Persistent Volume Claim(PVC)를 통해 각 Pod에 연결됩니다.
- pre-SVC.yaml: label selector로 접근이 가능하며 app: hs-pre를 가진 Pod를 대상으로 서비스 합니다.
  type은 NodePort로, 30232 포트를 사용합니다.
- micro1_python_k8s_api.py: Python에서 k8s API를 접근하기 위해 Pod 내에서 실행할 수 있는 파일입니다.
- requirements.txt: Flask,Pymongo 등 Dockerfile에서 RUN할 모듈들이 txt파일로 저장되어 있습니다.  


**micro2**
- docker/Dockerfile: docker 컨테이너를 빌드할 수 있는 Dockerfile이 있는 디렉토리 입니다.
- infer-deploy.yaml: 넘버링 된 각 프레임을 대상으로 Resnet 기반 SSD300_MODEL을 통해 INFERENCING하여 txt파일로 추출하는 Pod를 실행하는 yaml파일 입니다. 
- SSD300_MODEL은 CUDA Available Device에서만 작동할 수 있으므로, GPU가 있는 WorkerNode에 label을 추가해     nodeSelector에서 해당 노드를 지정하도록 해야합니다. 혹은 Python Code를 통해 적절한 디바이스를 찾아도 문제 없습니다.
- requirements.txt: Flask,Pymongo 등 Dockerfile에서 RUN할 모듈들이 txt파일로 저장되어 있습니다.

**micro3**
- docker/Dockerfile: docker 컨테이너를 빌드할 수 있는 Dockerfile이 있는 디렉토리 입니다.
- post-deploy.yaml: 넘버링 된 각 프레임과 INFERENCING된 txt파일을 결합하여 넘버링 된 tar_frame을 생성하고, tar_frame들을 순차적으로 결합하여 avi파일로 만드는 Pod를 실행하는 yaml파일 입니다.
- micro3_python_k8s_api.py: Python에서 k8s API를 접근하기 위해 Pod 내에서 실행할 수 있는 파일입니다.
- requirements.txt: Flask,Pymongo 등 Dockerfile에서 RUN할 모듈들이 txt파일로 저장되어 있습니다.

**templates**
- 해당하는 REST API가 호출 되었을 때 가져올 html문서들을 관리하는 디렉토리 입니다.

**micro{n}_restart.sh**
- 초기에 700 권한을 준 후 실행하면 현재 running중인 Pod를 삭제하고, Dockerfile을 Build하고, tag를 설정해 Pull하여
  Pod에서 해당 이미지를 사용할 수 있는 상태로 만든 뒤, yaml파일을 실행해 Pod 및 Deployment를 실행합니다.

**clusterrole.yaml**
- Python에서 k8s API 접근을 허용하기 위해 클러스터 범위 리소스의 권한을 정의하는 clusterrole을 생성하는 파일 입니다.

**clusterrolebinding.yaml**
- RBAC 인증을 통해 clusterrole에 정의된 권한을 Python에서 k8s API 접근을 하려는 사용자에게 부여합니다.
- 본 과정에서는 사용자 대상으로 ServiceAccount에 name: default, namespace: default로 설정하였습니다.


Setting
- mongoDB가 잘 연결되었는지 확인
```
$ service mongod status
$ sudo systemctl start mongod
> use hs_resnet
> db.hs_requests.find({})
```
- microservice를 진행하기 전 PV와 PVC 생성
```
$ kubectl apply -f pre-PV.yaml
$ kubectl apply -f pre-PVC.yaml
```  

- microservice를 진행하기 전 clusterrole과 clusterrolevinding 생성 (name과 namespace default인 ServiceAccount는 생성되어 있음)
```
$ kubectl apply -f clusterrole.yaml
$ kubectl apply -f clusterrolebinding.yaml
```  

- Docker Container 이미지 생성 및 Pod 생성
```
$ sudo docker build -t hs_pre -f ./micro1/docker/Dockerfile . &&
sudo docker tag hs_pre hyeonseong0917/hs_pre &&
sudo docker push hyeonseong0917/hs_pre &&
kubectl apply -f ./micro1/pre-deploy.yaml
$ kubectl apply -f pre-SVC.yaml # Pod를 생성한 후에 Service를 적용해야 함
$ sudo docker build -t hs_infer -f ./micro2/docker/Dockerfile . &&
sudo docker tag hs_infer hyeonseong0917/hs_infer &&
sudo docker push hyeonseong0917/hs_infer &&
kubectl apply -f ./micro2/infer-deploy.yaml
$ sudo docker build -t hs_post -f ./micro3/docker/Dockerfile . &&
sudo docker tag hs_post hyeonseong0917/hs_post &&
sudo docker push hyeonseong0917/hs_post &&
kubectl apply -f ./micro3/post-deploy.yaml

# 혹시 마이크로 서비스 실행에 문제가 생겼다면 해당 마이크로 서비스의 Dockerfile로 가셔서, 주석 처리 돼있는 # CMD ["python3",  "/hsapp/main.py"] 를 주석을 풀고, 기존에 있었던 CMD명령어 줄을 주석처리 한 다음에, restart를 합니다. 그 후 pod가 생성되면 
1. kubectl exec -it <pod_name> /bin/bash 를 통해 pod 안쪽으로 접근
2. pod 안에서 기존에 실행하려는 Python파일 실행
과정을 통해 TroubleShooting 하시면 될 것 같습니다.
# main함수는 컨테이너가 종료되지 않게 시간 간격을 두고(time.sleep), while(1) 내에서 무한으로 순회하는 코드입니다.
pods에 접근 후 기존 Python 파일에 cnt를 찍어본다거나 print문을 적절히 사용하여 원활한 TroubleShooting 하시길 바랍니다.
# microservice 2  실행 시 SSD_MODEL을 불러오는데 오류가 생기면 pod 내에서 /root/.cache/ 에 있는 checkpoints 디렉토리를 삭제하시면 됩니다.
```

시연 과정 및 화면
- 인터넷 브라우저를 통해 Workernode 혹은 Masternode의 IP를 입력하고 pre-SVC.yaml에서 정의한 nodeport 번호를 입력 합니다. 그 후 /upload로 이동해 mp4파일을 선택했습니다.

![default](image/res_1.PNG)

- 제출 버튼을 누르면 그 순간부터 microservice를 진행하게 됩니다.

![default](image/res_img1.PNG)

- /fileUpload로 라우팅되며 Object_Id가 표시되고, /upload 로 돌아가는 return, 결과를 볼 수 있는 result 하이러링크가
  표시됩니다. 결과를 보기 위해 result를 누를 수 있습니다.

- DB의 STATUS 및 FILENAME 변환 과정을 보겠습니다.

![default](image/res_img2.PNG)

- 초기 STATUS가 ENQUEUE에서 mp4 파일이 /mnt/src/ 디렉토리에 저장되면 STATUS가 PREPROCESSING으로 바뀌게 됩니다.

![default](image/res_img3.PNG)
- microservice1에서 PreProcessing 작업이 완료되면 STATUS가 PREPROCESSING_COMPLETE로 바뀌게 되며, 이로 인해 microservice2가 작동하게 되어 STATUS가 INFERENCING으로 바뀌게 됩니다.
- PreProcessing 과정을 완료한 후 결과물의 일부는 다음과 같습니다.

![default](image/res_img4.PNG)

- frame들이 순차적으로 넘버링 되어 존재하는 모습입니다.


![default](image/res_img5.PNG)
- microservice2에서 Inferencing 작업이 완료되면 STATUS가 INFERENCING_COMPLETE로 바뀌게 되며, 이로 인해 microservice3가 작동하게 되어 STATUS가 POSTPROCESSING으로 바뀌게 됩니다.
- INFERENCING 과정을 완료한 후 결과물은 다음과 같습니다.


![default](image/res_img6.PNG)

- txt들이 순차적으로 넘버링 되어 존재하는 모습입니다.


- txt들이 어떤 정보들을 가지고 있는지 한 개만 확인해 보겠습니다.

![default](image/res_img7.PNG)
- 해당 프레임에서 탐지된 객체들에 대한 정보로, 직사각형을 그리는 데 있어 minX,minY,maxX,maxY 그리고 COCO Dataset 기반 label의 idx가 출력되는 것을 확인 할 수 있습니다.


![default](image/res_img8.PNG)
- microservice3에서 PostProcessing 작업이 완료되면 STATUS가 POSTPROCESSING_COMPLETE로 바뀌게 되며, 총 소요된 시간이
TOTAL에 나타나게 됩니다.
- POSTPROCESSING의 결과물은 src_frame에 txt가 합쳐진 tar_frame(tar_{n}.jpg)과 tar_frame을 연속적으로 이어 만든 avi(target_{R_id}.avi) 입니다.
- POSTPROCESSING 결과물들의 일부를 확인해 보겠습니다.

![default](image/res_img9.PNG)

![default](image/res_img10.PNG)
- tar_frame들과 target avi가 생성된 것을 확인할 수 있습니다. 

![default](image/res_img11.PNG)
- 이제 /result로 이동하여 웹 페이지를 보면 MongoDB에 있는 내용들이 표시되며 하이퍼링크를 통해 avi 파일을 다운로드 받을 수 있습니다.


![default](image/res_img12.PNG)
- 다운로드 받은 avi 파일을 엽니다.

![default](image/res_img13.PNG)
- Box 형태로 Object Detection을 수행해 해당 객체를 표시한 모습입니다.


# Python 으로 Kubernetes Api 활용
- Python 코드에서 현재 실행되고 있는 deployment의 Replicaset을 조정하는 방법입니다.
- ServiceAccount가 생성 되어 있고 자격 증명을 받았으며, clusterrole, clusterrolebinding이 생성 되어있는 상태여야 합니다.
- microservice 1 혹은 3 의 pod 안쪽으로 접근하여 (kubectl exec 사용) micro{n}_python_k8s_api.py파일을 살펴봅니다.
- 다음은 해당 ServiceAccount의 자격 증명을 받아오는 Python 코드입니다.

![default](image/res_img14.PNG)

- 다음은 API Instance를 생성해 Deployment의 Replicaset을 조정하는 코드입니다.

![default](image/res_img15.PNG)

- 현재  value값이 1로 설정되어 있고

![default](image/res_img16.PNG)

- Type이 Deployment인 hs-pre-deploy 가 1/1인 것을 확인할 수 있습니다. 

![default](image/res_img17.PNG)

- 이제 Replicaset의 value값을 3으로 조정하고 실행해 보겠습니다.

![default](image/res_18.PNG)

- Type이 Deployment인 hs-pre-deploy가 3/3이 된 것을 확인할 수 있습니다.





# Timeline을 설정했던 방법
- 현재 작업 환경이 Masternode 1대, Workernode 2대로, 총 3대가 있지만 각각의 Pod들이 다른 Workernode에 할당된다면
  Timeline이 의도치 않게 표시 될 수 있습니다. 각각 node들의 시간이 같다고 보장할 수 없기 때문이죠.
  이를 해결하기 위해 microservice1(REST API 및 PreProcessing)를 실행하는 yaml파일에 nodeSelector를 통해 해당 Pod는 scale에 관계없이 오직 한 노드에만 할당되도록 하였습니다. 그 다음, microservice 2 혹은 3에서 각각의 작업이 시작되거나 끝났을 때,
  
  (microservice 3를 예로 들었습니다.)

  ![default](image/res_img19.PNG)

  이와 같이 put method를 이용해 R_id,status를 바탕으로 microservice 1의 API에 접근하여

  ![default](image/res_img20.PNG)

  API에 접근했을 때의 timeline을 DB에 기록하는 방식으로 각각의 Timeline을 설정할 수 있었습니다.



