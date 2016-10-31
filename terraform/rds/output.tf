output "address" {
  value = "${aws_db_instance.default.address}"
}

output "port" {
  value = "${aws_db_instance.default.port}"
}

output "engine" {
value = "${aws_db_instance.default.engine}"	
}