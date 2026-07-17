output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs (one per operative AZ)."
  value       = aws_subnet.public[*].id
}

output "alb_dns_name" {
  description = "DNS name of the public Application Load Balancer."
  value       = aws_lb.this.dns_name
}

output "alb_sg_id" {
  description = "Security group ID for the ALB."
  value       = aws_security_group.alb.id
}

output "frontend_sg_id" {
  description = "Security group ID for frontend tasks."
  value       = aws_security_group.frontend.id
}

output "backend_sg_id" {
  description = "Security group ID for backend tasks."
  value       = aws_security_group.backend.id
}

output "pipeline_sg_id" {
  description = "Security group ID for pipeline run tasks."
  value       = aws_security_group.pipeline.id
}

output "frontend_tg_arn" {
  description = "ARN of the frontend target group (sole public ALB target)."
  value       = aws_lb_target_group.frontend.arn
}

output "service_connect_namespace_arn" {
  description = "ARN of the Service Connect HTTP namespace (owned by network module)."
  value       = aws_service_discovery_http_namespace.service_connect.arn
}

output "service_connect_namespace_name" {
  description = "Name of the Service Connect HTTP namespace."
  value       = aws_service_discovery_http_namespace.service_connect.name
}
