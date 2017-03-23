Deployment automation for the DPR.

## Installation

Make sure you have `npm` and `python` installed.

```bash
cd ~
git clone https://gitlab.com/atomatic/dpr-deploy
cd dpr-deploy
pip install -r requirements.txt

# setup configuration
cp external_config.json.template external_config.json

# external_config.json remove `run_env` key
```

We need to have `aws_credentials` in `~/.aws/credentials` file.

```bash
ansible-playbook app.yml dpr-deploy --extra-vars "@external_config.json"
```



# OLD //////////

----

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


# Docker-based option

### Requirements:

- We only need docker to be installed. Please follow [this instruction](https://docs.docker.com/engine/installation/) for installation.

### Run instruction:
We need to build docker image locally and run that image.
```bash
$ cd ~
$ git clone https://gitlab.com/atomatic/dpr-deploy
$ cd dpr-deploy

$ cp external_config.json.template external_config.json
# please update the configurations in external_config.json
$ docker build -t dpr-deploy .
# After this step docker image will be built
$ docker run -it dpr-deploy -h
  # this will print ansible commands
  # please run the docker build -t dpr-deploy . command when ever we update some configurations
```

### For running the deployment:

```bash
$ docker run -it dpr-deploy --extra-vars "@external_config.json"
```


## Configurations Options are:

```project``` [Projetc name ]

## Tags
There are separate tags to run components individually:
To run the tags we want to run run command:
```bash
$ docker run -it dpr-deploy --extra-vars "@external_config.json" --tags "s3,rds"
# this will only run s3 and rds part of deployment
```


```s3``` This tag will only create/delete s3 buckets
```rds``` This tag will only create/delete rds instance.
```auth0``` This tag will only create/delete auth0 environment.
```zappa_facts``` This tag will gather facts about s3, rds and auth0
```zappa_manager``` This tag will run ```zappa_facts``` and run manager.py
```zappa``` This tag will only create/create flask app and run zappa_facts,zappa_manager
