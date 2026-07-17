output "gemini_secret_arn" {
  description = "ARN of the GEMINI_API_KEY secret (metadata only; no secret version)."
  value       = aws_secretsmanager_secret.gemini_api_key.arn
}

output "gemini_secret_name" {
  description = "Name of the GEMINI_API_KEY secret."
  value       = aws_secretsmanager_secret.gemini_api_key.name
}
