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
  flavor_name = "1C4R16D"
  image_id    = "733bce10-271f-46ed-acfd-aa45cd4a284b"
  network {
    uuid = "${openstack_networking_network_v2.mikal_test_net.id}"
    fixed_ip_v4 = "10.1.0.40"
  }
}