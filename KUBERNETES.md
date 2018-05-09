# Datahq Kubernetes Environment


## Using Minikube for local infrastructure development

* Install Minikube according to the instructions in latest [release notes](https://github.com/kubernetes/minikube/releases)
* Create the local minikube cluster
  * `minikube start`
* Verify you are connected to the cluster
  * `kubectl get nodes`


## Deployment

Deployment is managed using [helm charts](https://helm.sh/)

* [Install helm](https://docs.helm.sh/using_helm/#quickstart)
* Initialize helm on the cluster (Might need to setup RBAC in some cases, refer to helm docs)
  * `helm init --history-max 1 --upgrade --wait`
* Verify that it works
  * `helm ls`


## Deploying charts

For example, to deploy the filemanager chart

```
helm upgrade filemanager ./charts/filemanager/ -if ./minikube-values.yaml
```

Wait for rollout to complete

```
kubectl rollout status deployment/filemanager
```

Check the resources

```
kubectl get all
```
