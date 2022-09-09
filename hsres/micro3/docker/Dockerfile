FROM python:3.6
EXPOSE 5000
RUN mkdir /hsapp
RUN mkdir /hsapp/templates
WORKDIR /hsapp
# COPY ./hsdef/* /hsdef/
# COPY ./hslib/* /hslib/
COPY ./templates/* /hsapp/templates/
ADD ./micro3/ /hsapp/
RUN apt-get upgrade -y
RUN pip install torch==1.7.1+cu101 torchvision==0.8.2+cu101 torchaudio==0.7.2 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install opencv-contrib-python
RUN pip install opencv-python
RUN pip install opencv-python-headless
RUN pip install requests
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
# CMD ["python3",  "/hsapp/main.py"]
CMD ["python3",  "/hsapp/post.py"]