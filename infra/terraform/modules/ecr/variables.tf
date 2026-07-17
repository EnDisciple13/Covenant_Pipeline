variable "project_name" {
  description = "Project name prefix for ECR repository names."
  type        = string
  default     = "covenant-pipeline"
}

variable "repository_policy_json" {
  description = "Optional JSON repository policy applied to both repositories when non-empty."
  type        = string
  default     = ""
}
