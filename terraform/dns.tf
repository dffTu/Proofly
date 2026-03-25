data "yandex_dns_zone" "ganvas" {
  dns_zone_id = "dns08o7kbutupb771q9k"
}

resource "yandex_dns_recordset" "proofly" {
  zone_id = data.yandex_dns_zone.ganvas.id
  name    = "proofly"
  type    = "A"
  ttl     = 300
  data    = ["158.160.106.142"]
}
