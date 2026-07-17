variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "backend_repository_url" {
  description = "ECR repository URL for the backend image (no tag or digest suffix)."
  type        = string
}

variable "frontend_repository_url" {
  description = "ECR repository URL for the frontend image (no tag or digest suffix)."
  type        = string
}

variable "backend_image_digest" {
  description = "Immutable backend image digest (64 hex chars, optional sha256: prefix)."
  type        = string

  validation {
    condition     = can(regex("^(sha256:)?[0-9a-fA-F]{64}$", var.backend_image_digest))
    error_message = "backend_image_digest must be a 64-character hex SHA256 digest, optionally prefixed with sha256:."
  }
}

variable "frontend_image_digest" {
  description = "Immutable frontend image digest (64 hex chars, optional sha256: prefix)."
  type        = string

  validation {
    condition     = can(regex("^(sha256:)?[0-9a-fA-F]{64}$", var.frontend_image_digest))
    error_message = "frontend_image_digest must be a 64-character hex SHA256 digest, optionally prefixed with sha256:."
  }
}

variable "data_bucket_arn" {
  description = "ARN of the persistent general-purpose S3 data bucket (bootstrap-owned)."
  type        = string
}

variable "gemini_secret_arn" {
  description = "ARN of the Secrets Manager secret for GEMINI_API_KEY (bootstrap-owned metadata)."
  type        = string
}

variable "desired_count" {
  description = "Desired task count for long-running backend and frontend ECS services."
  type        = number
  default     = 1
}
