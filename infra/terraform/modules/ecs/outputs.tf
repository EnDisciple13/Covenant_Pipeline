output "cluster_arn" {
  description = "ARN of the ECS cluster."
  value       = aws_ecs_cluster.this.arn
}

output "backend_service_name" {
  description = "Name of the backend ECS service."
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service."
  value       = aws_ecs_service.frontend.name
}

output "pipeline_task_definition_arn" {
  description = "ARN of the pipeline task definition (run-task only; no service)."
  value       = aws_ecs_task_definition.pipeline.arn
}

output "alb_dns_name" {
  description = "ALB DNS name (passed through from network module)."
  value       = var.alb_dns_name
}

output "backend_task_definition_arn" {
  description = "ARN of the backend task definition."
  value       = aws_ecs_task_definition.backend.arn
}

output "frontend_task_definition_arn" {
  description = "ARN of the frontend task definition."
  value       = aws_ecs_task_definition.frontend.arn
}
