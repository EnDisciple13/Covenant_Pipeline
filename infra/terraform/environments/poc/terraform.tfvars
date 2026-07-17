aws_region = "us-east-1"

backend_repository_url  = "568728209842.dkr.ecr.us-east-1.amazonaws.com/covenant-pipeline-backend"
frontend_repository_url = "568728209842.dkr.ecr.us-east-1.amazonaws.com/covenant-pipeline-frontend"

# Gate D requires real digests from the hosted build workflow before apply.
backend_image_digest  = "0000000000000000000000000000000000000000000000000000000000000000"
frontend_image_digest = "0000000000000000000000000000000000000000000000000000000000000000"

data_bucket_arn   = "arn:aws:s3:::covenant-pipeline-data-andy-568728209842"
gemini_secret_arn = "arn:aws:secretsmanager:us-east-1:568728209842:secret:covenant-pipeline/gemini-api-key-PLACEHOLDER"

desired_count = 1
