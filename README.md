# DPR Deploy

Deployement Automation for the DPR.

### Requirements:

- We only need docker to be installed. Please follow [this instruction](https://docs.docker.com/engine/installation/) for installation.

### Run instruction:
We need to build docker image locally and run that image.
```bash
$ cd ~
$ git clone https://gitlab.com/atomatic/dpr-deploy
$ cd dpr-deploy
$ docker build -t dpr-deploy .
# After this step docker image will be built
$ docker run -it dpr-deploy -h
  # this will print help
  usage: deploy.py [-h] [-d] {build, destroy}

  argument parser for ansible

  mandetory arguments:
    -a, --action     {build, destroy}  please mention action
    optional arguments:
    -h, --help       show this help message and exit
    -d, --debug      Run in debug mode
```

### Deploy Infrastructure and Application:
After build the docker image plz run this to deploy
```bash
$ docker run -it dpr-deploy -a build -d
```
This will prompt for some System Properties for Infrastructure:
- Please provide auth0 API KEY
- Please provide auth0 Global secret KEY
- Please provide auth0 Domain name
- Plz provide AWS key
- Plz provide AWS secret key
- Plz provide AWS zone name [us-west-2]
- Plz provide route 53 domain name

If these System Properties is not supplied it will throw error.

### Destroy Infrastructure and Application:
If we want to destroy the Infrastructure plz run this command.
```bash
$ docker run -it dpr-deploy -a destroy -d
```
This will prompt for some System Properties for Infrastructure:
- Please provide auth0 API KEY
- Please provide auth0 Global secret KEY
- Please provide auth0 Domain name
- Plz provide AWS key
- Plz provide AWS secret key
- Plz provide AWS zone name [us-west-2]
- Plz provide route 53 domain name

If these System Properties is not supplied it will throw error.
