/* Variables used by Terraform Code */

variable "publicly_accessible" {
default     = "true"
  description = "DB Accessablity"

}
variable "identifier" {
  default     = "dpr-rds"
  description = "Identifier for your DB"
}

variable "storage" {
  default     = "10"
  description = "Storage size in GB"
}

variable "engine" {
  default     = "mysql"
  description = "Engine type (Example:mysql, postgres)"
}

variable "engine_version" {
  description = "Engine version"

  default = {
    mysql    = "5.6.22"
    postgres = "9.4.1"
  }
}

variable "instance_class" {
  default     = "db.t2.micro"
  description = "Instance class"
}

variable "db_name" {
  default     = "dprdb"
  description = "DB Name"
}

variable "username" {
  default     = "dprroot"
  description = "User name"
}

variable "password" {
  description = "password, provide through your ENV variables"
}
