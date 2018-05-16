[![Build Status](https://travis-ci.org/datahq/deploy.svg?branch=master)](https://travis-ci.org/datahq/deploy)

This repo manages datahub.io infrastructure as code.

DataHub.io uses a microservices architecture. We use docker for containerisation and Kubernetes for orchestration.

This repo is focused on the orchestration uses Kubernetes. It assumes each service is responsible for its own dockerisation and publication to the container registry i.e. dockerhub.

# Quickstart

*If you want to boot a DataHub instance manually or just play around ...*

0. [Prerequisites] Install docker :smile:
1. Run a local docker environment with all the tools installed: ```docker run -it --entrypoint bash -v `pwd`:/ops orihoch/sk8s-ops```
2. Authenticate with Google Cloud Platform `gcloud auth login`

*Note: most of the time this will all run automatically, here's how ...*

1. Every time a service builds it should update this repo (in some way - how? Ans: By Travis)
2. The travis script here then gets triggered and automatically updates the relevant k8s clusters ... see travis.yml for details.

DevOps team: adding a new service, or updating configuration ...

# Interacting with the environment

## Prerequisites

* Using Linux / OSX? Use [Docker](https://docs.docker.com/install/)
* Using Windows? Use [Google Cloud Shell](https://cloud.google.com/shell/docs/quickstart)

## Setting up and connecting to the environment

### Manage production environments on Google Kubernetes Engine

* Start a bash shell with all required dependencies and the deploy code
  * `docker run -it --entrypoint bash -e OPS_REPO_SLUG=datahq/deploy orihoch/sk8s-ops`
  * If you want to install locally, see these Dockerfiles: [sk8s-ops](https://github.com/OriHoch/sk8s-ops/blob/master/Dockerfile) [cloud-sdk-docker](https://github.com/GoogleCloudPlatform/cloud-sdk-docker/blob/master/alpine/Dockerfile)
* Authenticate with Google Cloud Platform
  * `gcloud auth login`

### Infrastructure development on Google Kubernetes Engine

* Clone and change directory to the deploy repo
  * `git clone https://github.com/datahq/deploy.git`
  * `cd deploy`
* Start a bash shell with all required dependencies and mounted volume to the host `deploy` code
  * `docker run -it --entrypoint bash -v `pwd`:/ops orihoch/sk8s-ops`
* Authenticate with Google Cloud Platform
  * `gcloud auth login`

### Local infrastructure development using Minikube

* Install Minikube according to the instructions in latest [release notes](https://github.com/kubernetes/minikube/releases)
* Create the local minikube cluster
  * `minikube start`
* Verify you are connected to the cluster
  * `kubectl get nodes`
* Install [helm client](https://docs.helm.sh/using_helm/#installing-the-helm-client)
* Initialize helm
  * `helm init --history-max 2 --upgrade --wait`
* Verify helm version on both client and server
  * `helm version`
  * should be v1.8.2 or later
* Clone the deploy repo
  * `git clone https://github.com/datahq/deploy.git`
* Change to the deploy directory
  * `cd deploy`
* Switch to the minikube environment
  * `source switch_environment.sh minikube`

# Common Tasks

All code assumes you are inside a bash shell with required dependencies and connected ot the relevant environment

## Deployment

Deployments are managed using [Helm](https://github.com/kubernetes/helm)

Initialize the Helm server side component

```
kubectl create -f rbac-config.yaml
helm init --service-account tiller --upgrade --force-upgrade --history-max 2
```

Deploy all charts (if dry run succeeds)

```
./helm_upgrade_all.sh --install --debug --dry-run && ./helm_upgrade_all.sh --install
```

You can also upgrade a single chart

```
./helm_upgrade_external_chart.sh  socialmap
```

The helm_upgrade scripts forward all arguments to the underlying `helm upgrade` command, some useful arguments:

* For initial installation you should add `--install`
* Depending on the changes you might need to add `--recreate-pods` or `--force`
* For debugging you can also use `--debug` and `--dry-run`


## Adding an external app

* Duplicate and modify an existing chart under `charts-external` directory
* Setup the external app's continuous deployment
  * Copy the relevant steps from an existing app's [.travis.yml](https://github.com/OriHoch/socialmap-app-main-page/blob/master/.travis.yml)
  * Also, suggested to keep deployment notes in the app's [README.md](https://github.com/OriHoch/socialmap-app-main-page/blob/master/README.md#deployment)
  * Follow the app's README to setup Docker and GitHub credentials on Travis

## Creating a new environment

You can create a new environment by copying an existing environment directory and modifying the values.

See the [sk8s environments documentation](https://github.com/OriHoch/sk8s/blob/master/environments/README.md#environments) for more details about environments, namespaces and clusters.

## Modifying configuration values

The default values are at `values.yaml` - these are used in the chart template files (under `templates`, `charts`  and `charts-external` directories)

Each environment can override these values using `environments/ENVIRONMENT_NAME/values.yaml`

Finally, automation scripts write values to `values.auto-updated.yaml`

## Modifying secrets

Secrets are stored and managed directly in kubernetes and are not managed via Helm.

To update an existing secret, delete it first `kubectl delete secret SECRET_NAME`

After updating a secret you should update the affected deployments, you can use `./force_update.sh` to do that

All secrets should be optional so you can run the environment without any secretes and will use default values similar to dev environments.

Each environment may include a script to create the environment secrets under `environments/ENVIRONMENT_NAME/secrets.sh` - this file is not committed to Git.

You can use the following snippet in the secrets.sh script to check if secret exists before creating it:

```
! kubectl describe secret <SECRET_NAME> &&\
  kubectl create secret generic <SECRET_NAME> <CREATE_SECRET_PARAMS>
```

## Continuous Deployment

* Enable Travis for the repo (run `travis enable` from the repo directory)
* Create a `.travis.yml` file based on existing file and modify according to your requirements

Depending on what you intend to do in your continuous deployment script you may need some of the following:

To connect and run commands on a Google Kubernetes Engine environment:

* Create a Google Compute Cloud service account, download the service account json file
    * set the service account json on the app's travis
* `travis encrypt-file ../deploy/secret-deploy-ops.json deploy-ops-secret.json.enc`
* Copy the `openssl` command output by the above command and modify in the .travis-yml
* The -out param should be `-out k8s-ops-secret.json`

To push changes to GitHub

* Create a GitHub machine user according to [these instructions](https://developer.github.com/v3/guides/managing-deploy-keys/#machine-users).
  * Give this user write permissions to the k8s repo.
* Add the GitHub machine user secret key to travis on the app's repo:
  * `travis env set --private K8S_OPS_GITHUB_REPO_TOKEN "*****"`

To build and push docker images

* `travis env set --private DOCKER_USERNAME "***"`
* `travis env set --private DOCKER_PASSWORD "***"`
 code
  * `docker run -it --entrypoint bash -e OPS_REPO_SLUG=datahq/# The DataHQ Kubernetes Environment


# Credits

TODO: credit Ori ...
