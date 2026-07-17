variable "data_bucket_arn" {
  description = "ARN of the persistent general-purpose S3 data bucket."
  type        = string
}

variable "s3files_sync_role_arn" {
  description = "IAM role ARN trusted by S3 Files for bucket synchronization."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for mount-target security group."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs (one mount target per subnet/AZ)."
  type        = list(string)
}

variable "backend_security_group_id" {
  description = "Backend task security group allowed to mount read-only."
  type        = string
}

variable "pipeline_security_group_id" {
  description = "Pipeline task security group allowed to mount read-write."
  type        = string
}

variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "covenant-pipeline"
}
