# NOTE(mikal): You must set the following environment variables:
#    - GOOGLE_PROJECT
#    - GOOGLE_CLOUD_KEYFILE_JSON

provider "google" {
  region  = "us-central1"
  zone    = "us-central1-c"
}

resource "google_compute_instance" "mikal_test" {
  name         = "mikal-test"
  machine_type = "f1-micro"

  boot_disk {
    initialize_params {
      image = "ubuntu-1804-bionic-v20191211"
    }
  }

  network_interface {
    # A default network is created for all GCP projects
    network       = "default"
    access_config {
    }
  }
}