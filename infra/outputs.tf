output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.server.id
}

output "public_ip" {
  description = "Public IP address of the server (changes every time it is recreated)."
  value       = aws_instance.server.public_ip
}

output "api_url" {
  description = "API base URL. Use it as EXPO_PUBLIC_API_URL in mobile/.env."
  value       = "http://${aws_instance.server.public_ip}:3000/api"
}

output "swagger_url" {
  description = "Swagger UI."
  value       = "http://${aws_instance.server.public_ip}:3000/api/docs"
}

output "shell_command" {
  description = "Open a shell on the server through Session Manager (needs the Session Manager plugin for the AWS CLI)."
  value       = "aws ssm start-session --region ${var.region} --target ${aws_instance.server.id}"
}
