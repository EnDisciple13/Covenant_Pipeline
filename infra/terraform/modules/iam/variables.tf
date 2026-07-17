variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "data_bucket_arn" {
  description = "ARN of the persistent data bucket."
  type        = string
}

variable "gemini_secret_arn" {
  description = "ARN of the GEMINI_API_KEY secret."
  type        = string
}

variable "project_name" {
  description = "Project name prefix for IAM role names."
  type        = string
  default     = "covenant-pipeline"
}
