resource "yandex_vpc_network" "proofly" {
  name = "proofly-net"
}

resource "yandex_vpc_subnet" "proofly" {
  name           = "proofly-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.proofly.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}
