variable "aws_region" {
  description = "AWS region for bootstrap resources."
  type        = string
  default     = "us-east-1"
}

variable "data_bucket_name" {
  description = "Name of the persistent versioned/encrypted S3 data bucket (bootstrap-owned)."
  type        = string
  default     = "covenant-pipeline-data-andy-568728209842"
}

variable "github_actions_role_name" {
  description = "Existing unmanaged GitHub OIDC deploy role name (policy attached; role not owned)."
  type        = string
  default     = "github-actions-covenant-deploy"
}

variable "project_name" {
  description = "Project name prefix for ECR repositories."
  type        = string
  default     = "covenant-pipeline"
}
