terraform {
  backend "http" {
    address = "http://localhost:5001/terraform_state/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    lock_address = "http://localhost:5001/terraform_lock/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    lock_method = "PUT"
    unlock_address = "http://localhost:5001/terraform_lock/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    unlock_method = "DELETE"
  }
}

provider "aws" {
  profile    = "default"
  region     = "ap-southeast-1"
  version    = "~> 2.27"
}

resource "aws_instance" "web_server" {
  # Ubuntu 18.04 LTS HVM, find your AMI ID for Ubuntu at https://cloud-images.ubuntu.com/locator/ec2/
  ami           = "ami-0f8c65cdcc35d0a72"
  instance_type = "t1.micro"
  key_name      = "id_aws"
  root_block_device {
    delete_on_termination = true
  }
}
