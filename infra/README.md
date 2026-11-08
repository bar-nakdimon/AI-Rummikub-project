# Infrastructure (Terraform)

Creates a single EC2 server on AWS that runs the production stack (`docker-compose.prod.yml`) from the prebuilt ghcr.io images.

| Resource | Purpose |
|---|---|
| EC2 instance (`c7i-flex.large`, Ubuntu 24.04, 30 GB encrypted disk) | Runs the API gateway, the Python service and MongoDB in Docker |
| Security group | Opens only port 3000 (API + Swagger). No SSH port |
| IAM role + instance profile | Shell access through AWS Session Manager instead of SSH keys |

On first boot the server installs Docker, generates a random `JWT_SECRET` locally (it never leaves the server), and starts the stack.

## Usage

Requires [Terraform](https://developer.hashicorp.com/terraform/install) and AWS CLI credentials.

```bash
cd infra
terraform init
terraform apply     # create the server (~5 minutes until the API responds)
terraform destroy   # delete everything, back to zero cost
```

`terraform apply` prints the URLs:

```
swagger_url = "http://<public-ip>:3000/api/docs"
api_url     = "http://<public-ip>:3000/api"   # set as EXPO_PUBLIC_API_URL in mobile/.env
```

The server is meant to be created on demand (e.g. for a demo) and destroyed afterwards. The public IP changes every time it is recreated.

To run a specific version: `terraform apply -var image_tag=sha-<commit>`.

## Troubleshooting

Open a shell on the server with the `shell_command` output (requires the [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)), then:

```bash
sudo cat /var/log/rummikub-setup.log            # first-boot setup log
sudo docker compose -f /opt/rummikub/docker-compose.yml ps
```

Terraform state (`terraform.tfstate`) is kept locally and is git-ignored.
