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


## Internal Working deploy:
- Creates s3 bucket [ignore if exists]
- Creates RDS instance [ignore if exists]
- Auth0
  - Create new Client
  - Create user pool [ignore if exists]
  - Grant the client created to the user pool
  - Grant Client to use management API
- Zappa
  - Clone repo from github
  - Run management to populate initial data
  - Certify the domain name
    - In the process of certify we need a pre-generated key
    - The document can be found [here](https://github.com/Miserlou/Zappa/blob/master/docs/domain_with_free_ssl_dns.md)
    - In this process zappa create a hosted zone of type CNAME that resolves to a cloudfont domain
  - Try to deploy the application
    - If already deployed it will fail and continue
  - If deploy fail application will be updated
  - Get the status of the lambda [It is properly running or not]
- Spit out a json of the deployed application

## Internal Working destroy:
- Delete s3 bucket
- Delete RDS instance
- Delete auth0 client and user pool
- Undeploy zappa application


# DPR - Deployment esp API Gateway

## 10 Dec 2016

So i think the way to go is zerossl as per:

https://www.pandastrike.com/posts/20160613-ssl-cert-aws-api-gateway-zerossl-letsencrypt

**NOTE**: Rufus can do DNS based domain ownership very easily ..

## 8 Dec 2016

We want to link a custom domain to API-Gateway generated endpoint.

We therefore need to create custom domain in API-gateway.

**Option 1:**

https://github.com/Miserlou/Zappa/blob/master/docs/domain_with_free_ssl_dns.md

- Create DNS in route53 [Need to buy this from route53 console] - TODO: cost summary. $12 for domain + $0.50 a month plus more ...  [Route 53 pricing][53-pricing]
- Zappa can automatically link to this TODO: link to docs

[53-pricing]: https://aws.amazon.com/route53/pricing/

**Option 2:**

https://github.com/Miserlou/Zappa/blob/master/docs/domain_with_free_ssl_http.md

Amazon doc: http://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-custom-domains.html

- Have a domain registered [DONE]
- Get a PEM-encoded SSL certificate for your custom domain name from a certificate authority. This can be done by ```letsencrypt```
  1. Certificate private key
  2. Certificate body
  3. Certificate chain
- Manually or [programatically][boto-apig] create custom domain in API Gateway
- Map custom domain to cloudfront distribution point
  - Requires cloudfront distribution point

[boto-apig]: http://boto3.readthedocs.io/en/latest/reference/services/apigateway.html#APIGateway.Client.create_domain_name

**NOTE: all this info should be included in documentation for this function in our dpr-deploy code ;-)**

Once these are created we can link custom domain in API Gateway.




## **Modified play-books and the deployment process:**
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
