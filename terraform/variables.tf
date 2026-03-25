variable "yc_token" {
  description = "Yandex Cloud IAM token (from `yc iam create-token`)"
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for VM access"
  default     = "~/.ssh/id_ed25519.pub"
}
