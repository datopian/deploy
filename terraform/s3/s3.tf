
resource "aws_s3_bucket" "dpr_bucket" {
    bucket = "${var.bucket_name}"
    
    tags {
        Name = "DPR bucket"
        Environment = "Dev"
    }
}
