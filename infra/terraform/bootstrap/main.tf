data "aws_caller_identity" "current" {}

data "aws_iam_role" "github_actions_deploy" {
  name = var.github_actions_role_name
}

module "ecr" {
  source = "../modules/ecr"

  project_name = var.project_name
}

module "secrets" {
  source = "../modules/secrets"
}

resource "aws_s3_bucket" "data" {
  bucket = var.data_bucket_name

  tags = {
    Name    = var.data_bucket_name
    Purpose = "covenant-pipeline-persistent-data"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role_policy" "github_actions_ecr_push" {
  name = "covenant-pipeline-ecr-push"
  role = data.aws_iam_role.github_actions_deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrAuthToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "EcrPushPull"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeRepositories",
          "ecr:DescribeImages",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
        ]
        Resource = [
          module.ecr.backend_repository_arn,
          module.ecr.frontend_repository_arn,
        ]
      },
    ]
  })
}
