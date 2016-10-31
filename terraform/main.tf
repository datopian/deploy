/* Teraform Code for RDS Cluster */

provider "aws" {
  access_key = "${var.aws_access_key_id}"
  secret_key = "${var.aws_secret_access_key}"
  region     = "${var.aws_region}"
}


module "dpr_rds" {
source = "./rds"
password = "${var.password}"
}

module "dpr_s3" {
source = "./s3"
bucket_name = "${var.bucket_name}"
}
