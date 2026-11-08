variable "region" {
  description = "AWS Region to deploy into."
  type        = string
  default     = "eu-north-1"
}

variable "instance_type" {
  description = "EC2 instance type. Needs about 4 GB of RAM for the PyTorch vision models, and must be x86_64 because the images are built for amd64."
  type        = string
  default     = "c7i-flex.large"
}

variable "image_tag" {
  description = "Tag of the ghcr.io images to run: \"latest\", or \"sha-<commit>\" to pin a version."
  type        = string
  default     = "latest"
}

variable "root_volume_size_gb" {
  description = "Size of the server's disk. The Docker images take a few GB."
  type        = number
  default     = 30
}
