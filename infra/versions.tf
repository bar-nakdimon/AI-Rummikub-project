terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  # Tag everything this project creates, so it is easy to find in the console.
  default_tags {
    tags = {
      Project   = "rummikub"
      ManagedBy = "terraform"
    }
  }
}
