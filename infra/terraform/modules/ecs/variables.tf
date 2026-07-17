variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "desired_count" {
  description = "Desired count for backend and frontend services."
  type        = number
}

variable "backend_repository_url" {
  description = "Backend ECR repository URL."
  type        = string
}

variable "frontend_repository_url" {
  description = "Frontend ECR repository URL."
  type        = string
}

variable "backend_image_digest" {
  description = "Backend image digest (64 hex, optional sha256: prefix)."
  type        = string
}

variable "frontend_image_digest" {
  description = "Frontend image digest (64 hex, optional sha256: prefix)."
  type        = string
}

variable "gemini_secret_arn" {
  description = "Secrets Manager ARN for GEMINI_API_KEY injection."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID (reserved for future use)."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for Fargate tasks."
  type        = list(string)
}

variable "alb_sg_id" {
  description = "ALB security group ID (reserved for future use)."
  type        = string
}

variable "frontend_sg_id" {
  description = "Frontend task security group ID."
  type        = string
}

variable "backend_sg_id" {
  description = "Backend task security group ID."
  type        = string
}

variable "pipeline_sg_id" {
  description = "Pipeline run-task security group ID."
  type        = string
}

variable "frontend_tg_arn" {
  description = "Frontend target group ARN for the ALB."
  type        = string
}

variable "alb_dns_name" {
  description = "ALB DNS name passed through for convenience outputs."
  type        = string
}

variable "service_connect_namespace_arn" {
  description = "Service Connect namespace ARN."
  type        = string
}

variable "service_connect_namespace_name" {
  description = "Service Connect namespace name."
  type        = string
}

variable "task_execution_role_arn" {
  description = "ECS task execution role ARN."
  type        = string
}

variable "backend_task_role_arn" {
  description = "Backend task role ARN."
  type        = string
}

variable "pipeline_task_role_arn" {
  description = "Pipeline task role ARN."
  type        = string
}

variable "s3files_file_system_arn" {
  description = "S3 Files file system ARN for task volumes."
  type        = string
}

variable "s3files_access_point_arn" {
  description = "S3 Files access point ARN for task volumes."
  type        = string
}

variable "project_name" {
  description = "Project name prefix."
  type        = string
  default     = "covenant-pipeline"
}
