data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ecs_task_execution_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "s3files_sync_assume" {
  # S3 Files trust principal is elasticfilesystem.amazonaws.com (not s3files.amazonaws.com).
  statement {
    sid     = "AllowS3FilesAssumeRole"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["elasticfilesystem.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:s3files:${var.aws_region}:${data.aws_caller_identity.current.account_id}:file-system/*"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.project_name}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_task_execution_secrets" {
  statement {
    sid    = "GetGeminiSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.gemini_secret_arn]
  }
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name   = "${var.project_name}-execution-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.ecs_task_execution_secrets.json
}

resource "aws_iam_role" "ecs_backend_task" {
  name               = "${var.project_name}-ecs-backend-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

data "aws_iam_policy_document" "ecs_backend_task_s3files" {
  statement {
    sid    = "S3FilesReadOnlyMount"
    effect = "Allow"
    actions = [
      "s3files:ClientMount",
      "s3files:ClientRootAccess",
    ]
    resources = [
      "arn:aws:s3files:${var.aws_region}:${data.aws_caller_identity.current.account_id}:file-system/*",
      "arn:aws:s3files:${var.aws_region}:${data.aws_caller_identity.current.account_id}:access-point/*",
    ]
  }
}

resource "aws_iam_role_policy" "ecs_backend_task_s3files" {
  name   = "${var.project_name}-backend-s3files"
  role   = aws_iam_role.ecs_backend_task.id
  policy = data.aws_iam_policy_document.ecs_backend_task_s3files.json
}

resource "aws_iam_role" "ecs_pipeline_task" {
  name               = "${var.project_name}-ecs-pipeline-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

data "aws_iam_policy_document" "ecs_pipeline_task_s3files" {
  statement {
    sid    = "S3FilesReadWriteMount"
    effect = "Allow"
    actions = [
      "s3files:ClientMount",
      "s3files:ClientWrite",
      "s3files:ClientRootAccess",
    ]
    resources = [
      "arn:aws:s3files:${var.aws_region}:${data.aws_caller_identity.current.account_id}:file-system/*",
      "arn:aws:s3files:${var.aws_region}:${data.aws_caller_identity.current.account_id}:access-point/*",
    ]
  }
}

resource "aws_iam_role_policy" "ecs_pipeline_task_s3files" {
  name   = "${var.project_name}-pipeline-s3files"
  role   = aws_iam_role.ecs_pipeline_task.id
  policy = data.aws_iam_policy_document.ecs_pipeline_task_s3files.json
}

resource "aws_iam_role" "s3files_sync" {
  name               = "${var.project_name}-s3files-sync"
  assume_role_policy = data.aws_iam_policy_document.s3files_sync_assume.json
}

data "aws_iam_policy_document" "s3files_sync_bucket" {
  statement {
    sid    = "SyncDataBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:ListBucketVersions",
      "s3:GetBucketLocation",
      "s3:GetBucketVersioning",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts",
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:GetObjectTagging",
      "s3:GetObjectVersionTagging",
      "s3:PutObject",
      "s3:PutObjectTagging",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
    ]
    resources = [
      var.data_bucket_arn,
      "${var.data_bucket_arn}/*",
    ]
    condition {
      test     = "StringEquals"
      variable = "aws:ResourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }

  statement {
    sid    = "SyncEventBridge"
    effect = "Allow"
    actions = [
      "events:PutRule",
      "events:DeleteRule",
      "events:DescribeRule",
      "events:PutTargets",
      "events:RemoveTargets",
      "events:ListTargetsByRule",
    ]
    resources = [
      "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/DO-NOT-DELETE-S3-Files*",
    ]
  }
}

resource "aws_iam_role_policy" "s3files_sync_bucket" {
  name   = "${var.project_name}-s3files-sync-bucket"
  role   = aws_iam_role.s3files_sync.id
  policy = data.aws_iam_policy_document.s3files_sync_bucket.json
}
