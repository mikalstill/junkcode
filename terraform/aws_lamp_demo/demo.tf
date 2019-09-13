provider "aws" {
  profile    = "default"
  region     = "ap-southeast-1"
  version    = "~> 2.27"
}

resource "aws_ebs_volume" "web_volume" {
  availability_zone = "ap-southeast-1a"
  size              = 1
  type              = "standard"
}

resource "aws_instance" "web_server" {
  # Ubuntu 18.04 LTS HVM, find your AMI ID for Ubuntu at https://cloud-images.ubuntu.com/locator/ec2/
  ami           = "ami-0f8c65cdcc35d0a72"
  instance_type = "t1.micro"
  key_name      = "id_aws"
  user_data     = "${file("initialize_ebs.sh")}"
  root_block_device {
    delete_on_termination = true
  }
}

resource "aws_volume_attachment" "web_volume_attachment" {
  # Note device naming advice at https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html#available-ec2-device-names
  device_name = "/dev/xvdd"
  volume_id   = "${aws_ebs_volume.web_volume.id}"
  instance_id = "${aws_instance.web_server.id}"
}

output "instance_ip_addr" {
  value = aws_instance.web_server.public_ip
}