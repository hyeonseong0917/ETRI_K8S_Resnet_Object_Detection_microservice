# kubectl delete -f ./micro3/post-deploy.yaml &&
sudo docker build -t hs_post -f ./micro3/docker/Dockerfile . &&
sudo docker tag hs_post hyeonseong0917/hs_post &&
sudo docker push hyeonseong0917/hs_post &&
kubectl apply -f ./micro3/post-deploy.yaml