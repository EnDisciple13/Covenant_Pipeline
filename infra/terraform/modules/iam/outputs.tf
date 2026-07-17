output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role."
  value       = aws_iam_role.ecs_task_execution.arn
}

output "backend_task_role_arn" {
  description = "ARN of the backend ECS task role (S3 Files read-only mount)."
  value       = aws_iam_role.ecs_backend_task.arn
}

output "pipeline_task_role_arn" {
  description = "ARN of the pipeline ECS task role (S3 Files read-write mount)."
  value       = aws_iam_role.ecs_pipeline_task.arn
}

output "s3files_sync_role_arn" {
  description = "ARN of the S3 Files synchronization role trusted by s3files.amazonaws.com."
  value       = aws_iam_role.s3files_sync.arn
}
