output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer."
  value       = module.network.alb_dns_name
}

output "cluster_arn" {
  description = "ARN of the covenant-pipeline ECS cluster."
  value       = module.ecs.cluster_arn
}

output "backend_service_name" {
  description = "Name of the backend ECS service."
  value       = module.ecs.backend_service_name
}

output "frontend_service_name" {
  description = "Name of the frontend ECS service."
  value       = module.ecs.frontend_service_name
}

output "pipeline_task_definition_arn" {
  description = "ARN of the on-demand pipeline task definition (run-task only)."
  value       = module.ecs.pipeline_task_definition_arn
}

output "service_connect_namespace_arn" {
  description = "Cloud Map HTTP namespace ARN used by ECS Service Connect (dns_name=backend)."
  value       = module.network.service_connect_namespace_arn
}

output "service_connect_namespace_name" {
  description = "Cloud Map HTTP namespace name used by ECS Service Connect."
  value       = module.network.service_connect_namespace_name
}

output "s3files_file_system_arn" {
  description = "ARN of the session-scoped S3 Files file system."
  value       = module.storage.file_system_arn
}

output "s3files_access_point_arn" {
  description = "ARN of the S3 Files access point mounted at /app/data."
  value       = module.storage.access_point_arn
}

output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role."
  value       = module.iam.task_execution_role_arn
}

output "backend_task_role_arn" {
  description = "ARN of the backend ECS task role."
  value       = module.iam.backend_task_role_arn
}

output "pipeline_task_role_arn" {
  description = "ARN of the pipeline ECS task role."
  value       = module.iam.pipeline_task_role_arn
}

output "s3files_sync_role_arn" {
  description = "ARN of the S3 Files synchronization role."
  value       = module.iam.s3files_sync_role_arn
}
