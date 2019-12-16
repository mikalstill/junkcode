provider "openstack" {
}

resource "openstack_networking_network_v2" "mikal_test_net" {
  name = "mikal_test_net"
}

resource "openstack_networking_subnet_v2" "mikal_test_subnet" {
  name = "mikal_test_subnet"
  network_id = "${openstack_networking_network_v2.mikal_test_net.id}"
  cidr = "10.1.0.0/24"
}

resource "openstack_compute_instance_v2" "mikal_test" {
  depends_on  = ["openstack_networking_subnet_v2.mikal_test_subnet"]
  name        = "mikal_test"
  flavor_name = "v2-highcpu-1"
  network {
    uuid = "${openstack_networking_network_v2.mikal_test_net.id}"
    fixed_ip_v4 = "10.1.0.40"
  }
  block_device {
    uuid                  = "83d33538-b366-4590-bb0a-a5cd9dbcce6e"
    source_type           = "image"
    volume_size           = 5
    boot_index            = 0
    destination_type      = "volume"
    delete_on_termination = true
  }
}