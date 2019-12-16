provider "aws" {
  profile    = "default"
  region     = "ap-southeast-1"
  version    = "~> 2.27"
}

resource "aws_instance" "mikal_test" {
  # Ubuntu 18.04 LTS HVM, find your AMI ID for Ubuntu at https://cloud-images.ubuntu.com/locator/ec2/
  ami           = "ami-0f8c65cdcc35d0a72"
  instance_type = "t1.micro"
  key_name      = "id_aws"
  root_block_device {
    delete_on_termination = true
  }
}