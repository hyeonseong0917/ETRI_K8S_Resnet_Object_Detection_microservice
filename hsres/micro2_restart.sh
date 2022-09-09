kubectl delete -f ./micro2/infer-pod.yaml &&
sudo docker build -t hs_infer -f ./micro2/docker/Dockerfile . &&
sudo docker tag hs_infer hyeonseong0917/hs_infer &&
sudo docker push hyeonseong0917/hs_infer &&
kubectl apply -f ./micro2/infer-pod.yaml