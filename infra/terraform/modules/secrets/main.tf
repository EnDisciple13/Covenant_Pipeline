resource "aws_secretsmanager_secret" "gemini_api_key" {
  name        = var.secret_name
  description = "Gemini API key for covenant-pipeline LLM stages (value set outside Terraform)."
}
