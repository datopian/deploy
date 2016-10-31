variable "aws_access_key_id" {
	description = "AWS ACCESS KEY"
}
variable "aws_secret_access_key" {
	description = "AWS SECRET KEY"
}
variable "password" {
  description = "password, provide through your ENV variables"
}
variable "aws_region" {
  default = "us-east-1"
}

variable "bucket_name" {
description = "Bucket name for S3"	
}