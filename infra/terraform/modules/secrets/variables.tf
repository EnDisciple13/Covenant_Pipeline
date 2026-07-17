variable "secret_name" {
  description = "Secrets Manager secret name for GEMINI_API_KEY metadata."
  type        = string
  default     = "covenant-pipeline/gemini-api-key"
}
