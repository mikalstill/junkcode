# NOTE(mikal): You must set the following environment variables:
#    - GOOGLE_PROJECT
#    - GOOGLE_CLOUD_KEYFILE_JSON

variable "gce_ssh_user" {
  type = string
}

variable "gce_ssh_pub_key_file" {
  type = string
}

provider "google" {
  region  = "us-central1"
  zone    = "us-central1-b"
}

resource "google_compute_instance" "sf_worker" {
  name         = "sf-worker"
  machine_type = "n1-standard-1"
  min_cpu_platform = "Intel Haswell"

  boot_disk {
    initialize_params {
      image = "nested-vm-image"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network       = "default"
    access_config {
    }
  }

  metadata = {
    ssh-keys = "${var.gce_ssh_user}:${file(var.gce_ssh_pub_key_file)}"
  }
}

output "instance_ip_addr" {
  value = google_compute_instance.sf_worker.network_interface.0.access_config.0.nat_ip
}