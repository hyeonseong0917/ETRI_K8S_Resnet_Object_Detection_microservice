# kubectl delete -f ./micro1/pre-pod.yaml &&
sudo docker build -t hs_pre -f ./micro1/docker/Dockerfile . &&
sudo docker tag hs_pre hyeonseong0917/hs_pre &&
sudo docker push hyeonseong0917/hs_pre &&
kubectl apply -f ./micro1/pre-deploy.yaml