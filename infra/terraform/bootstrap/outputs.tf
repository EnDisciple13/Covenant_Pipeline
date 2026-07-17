output "backend_repository_url" {
  description = "ECR repository URL for the backend image."
  value       = module.ecr.backend_repository_url
}

output "frontend_repository_url" {
  description = "ECR repository URL for the frontend image."
  value       = module.ecr.frontend_repository_url
}

output "backend_repository_arn" {
  description = "ARN of the backend ECR repository."
  value       = module.ecr.backend_repository_arn
}

output "frontend_repository_arn" {
  description = "ARN of the frontend ECR repository."
  value       = module.ecr.frontend_repository_arn
}

output "data_bucket_name" {
  description = "Persistent data bucket name."
  value       = aws_s3_bucket.data.id
}

output "data_bucket_arn" {
  description = "Persistent data bucket ARN (input to main root)."
  value       = aws_s3_bucket.data.arn
}

output "gemini_secret_arn" {
  description = "Secrets Manager secret ARN (metadata only; value set OOB after Gate D)."
  value       = module.secrets.gemini_secret_arn
  sensitive   = true
}

output "github_actions_ecr_push_policy_name" {
  description = "Inline ECR push policy name attached to the unmanaged OIDC role."
  value       = aws_iam_role_policy.github_actions_ecr_push.name
}

output "aws_account_id" {
  description = "Account ID used for this bootstrap plan."
  value       = data.aws_caller_identity.current.account_id
}
