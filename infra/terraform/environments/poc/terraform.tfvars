aws_region = "us-east-1"

backend_repository_url  = "568728209842.dkr.ecr.us-east-1.amazonaws.com/covenant-pipeline-backend"
frontend_repository_url = "568728209842.dkr.ecr.us-east-1.amazonaws.com/covenant-pipeline-frontend"

# Digests from build-push-poc run 29601806177 @ commit 5e58ecbff6e57f95bbf336445d95131c8e41b1b2
backend_image_digest  = "13c0b73aca47492eb66ed556dc530fec7f769b55b43ca879e3e38fb5e7fdf346"
frontend_image_digest = "e5391be0651a7d2952c7bdb9b3a7fea530ebadd0893547a39fdfccf7313c761f"

data_bucket_arn   = "arn:aws:s3:::covenant-pipeline-data-andy-568728209842"
gemini_secret_arn = "arn:aws:secretsmanager:us-east-1:568728209842:secret:covenant-pipeline/gemini-api-key-umd9IP"

desired_count = 1