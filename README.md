#DPR Deploy

Deployement Automation for the DPR.

## Dependencies

We are using [Terraform][T] for deploying the our application to AWS. [Install Terraform][TI].

[T]: https://www.terraform.io/
[TI]: https://www.terraform.io/intro/getting-started/install.html


## Configuration

Create the credentials($HOME/.aws/credentials) file in the user path. See [here][https://www.terraform.io/docs/providers/aws/#shared-credentials-file] for more details.
```
aws_access_key_id = <<AWS ACCESS KEY>>
aws_secret_access_key = <<AWS SECRET ACCESS KEY>>
password = <<Password for RDS DB>>
```

##Build Infrastructure
1. Load Terraform Modules
```
python deploy.py get
```
2. Create the Inra Structure.
```
python deploy.py apply
```


##Optional
1. Pass Variables to the Terraform by adding values in terraform.tfvars. List of variables that we can override are:
 * region = <<AWS Region>>
 * bucket_name = <<Bucket name for S3>>

Also, variables can be overide in corresponding module files.(To replace the defaults) 


2. Destroy the Inra Structure.
```
python deploy.py destroy
```

##Integration with Zappa (Continious Deployment)

Yet to be Done






