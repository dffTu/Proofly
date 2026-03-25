data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}

resource "yandex_compute_instance" "proofly" {
  name        = "proofly"
  platform_id = "standard-v3"

  resources {
    cores         = 2
    memory        = 2
    core_fraction = 20
  }

  scheduling_policy {
    preemptible = true
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 15
    }
  }

  network_interface {
    subnet_id      = yandex_vpc_subnet.proofly.id
    nat            = true
    nat_ip_address = "158.160.106.142"
  }

  metadata = {
    ssh-keys  = "ubuntu:${file(pathexpand(var.ssh_public_key_path))}"
    user-data = file("${path.module}/cloud-init.yml")
  }
}
