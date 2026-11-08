# Latest Ubuntu 24.04 LTS image (x86_64), as published by Canonical.
data "aws_ssm_parameter" "ubuntu" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

data "aws_vpc" "default" {
  default = true
}

# ---------------------------------------------------------------------------
# Firewall: only the API gateway port is open to the internet. There is no
# SSH port; shell access goes through AWS Systems Manager Session Manager.
# ---------------------------------------------------------------------------

resource "aws_security_group" "api" {
  name_prefix = "rummikub-api-"
  description = "Rummikub API gateway"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "api_http" {
  security_group_id = aws_security_group.api.id
  description       = "API gateway and Swagger UI"
  ip_protocol       = "tcp"
  from_port         = 3000
  to_port           = 3000
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "all_outbound" {
  security_group_id = aws_security_group.api.id
  description       = "Pull packages and Docker images"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# ---------------------------------------------------------------------------
# IAM role for the server: lets Session Manager manage it, so no SSH key or
# open SSH port is needed.
# ---------------------------------------------------------------------------

resource "aws_iam_role" "server" {
  name_prefix = "rummikub-server-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.server.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "server" {
  name_prefix = "rummikub-server-"
  role        = aws_iam_role.server.name
}

# ---------------------------------------------------------------------------
# The server
# ---------------------------------------------------------------------------

resource "aws_instance" "server" {
  ami                    = data.aws_ssm_parameter.ubuntu.insecure_value
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.server.name
  vpc_security_group_ids = [aws_security_group.api.id]

  # Installs Docker and starts the stack on first boot (see user_data.sh.tftpl).
  # Windows line endings are stripped, since the script runs on Linux.
  user_data = replace(templatefile("${path.module}/user_data.sh.tftpl", {
    compose_file = file("${path.module}/../docker-compose.prod.yml")
    image_tag    = var.image_tag
  }), "\r", "")
  user_data_replace_on_change = true

  # Require IMDSv2 (session tokens) for the instance metadata service.
  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size_gb
    encrypted   = true
  }

  tags = {
    Name = "rummikub-server"
  }
}
