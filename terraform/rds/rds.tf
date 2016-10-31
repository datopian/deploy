/* Teraform Code for RDS Cluster */

resource "aws_db_instance" "default" {
  identifier             = "${var.identifier}"
  allocated_storage      = "${var.storage}"
  engine                 = "${var.engine}"
  engine_version         = "${lookup(var.engine_version, var.engine)}"
  instance_class         = "${var.instance_class}"
  name                   = "${var.db_name}"
  username               = "${var.username}"
  password               = "${var.password}"
  publicly_accessible    = "${var.publicly_accessible}"
  vpc_security_group_ids = ["${aws_security_group.dpr_sg.id}"]
}

