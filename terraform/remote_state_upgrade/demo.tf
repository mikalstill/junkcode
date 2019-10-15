terraform {
  backend "http" {
    address = "http://localhost:5000/terraform_state/471ab834-d82f-11e9-ad51-efd94c880179"
    lock_address = "http://localhost:5000/terraform_lock/471ab834-d82f-11e9-ad51-efd94c880179"
    lock_method = "PUT"
    unlock_address = "http://localhost:5000/terraform_lock/471ab834-d82f-11e9-ad51-efd94c880179"
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