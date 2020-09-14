This directory contains terraform scripts to provision GCP Kubernetes

## Install

You will need `terraform` and `gcloud` CLI tools to be installed on your machine

### gcloud CLI

See Google Cloud SDK docs to install `gcloud` CLI https://cloud.google.com/sdk/install

### terraform CLI

Following commands should work for Linux machines. See terraform docs for more https://learn.hashicorp.com/tutorials/terraform/install-cli

```
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform
```

Verify installation

```
terraform -help
```

## Authenticate

Authenticate for GCP

```
gcloud auth application-default login
```

## Deploy

### Install dependencies and validate scripts

```
terraform init
# Output: Terraform has been successfully initialized!

terraform validate
# Output: Success! The configuration is valid.
```

### Plan

Before applying changes, double check expected changes

```
terraform plan

# Output: Terraform will perform the following actions:
#  # module.gke.google_container_cluster.primary will be created
#  + resource "google_container_cluster" "primary" {
#      + additional_zones            = (known after apply)
#      + cluster_ipv4_cidr           = (known after apply)
$  ...
```


### Apply

```
terraform apply
```

## Environment Variabless

Export following following environment variables to deploy production cluster

```
export TF_cluster_name=datahub-production              Kuberntes Cluster Name              (default: datahub-staging)
export TF_load_balancer_ip=35.224.172.105              External IP of loadbalancer         (default: 35.225.241.192)
export TF_node_pool_name=prodcution-node-pool          Node pool name                      (default: staging-node-pool)
```

Other configurable variables

```
export TF_region                  The region to host the cluster      (default: us-central1)
export TF_region                  The zone to host the cluster        (default: us-central1-a)
export TF_kubernetes_version      Kuberntes version                   (default: 1.16.13-gke.1)
```
