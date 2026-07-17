resource "aws_s3files_file_system" "this" {
  bucket   = var.data_bucket_arn
  role_arn = var.s3files_sync_role_arn
}

resource "aws_s3files_access_point" "this" {
  file_system_id = aws_s3files_file_system.this.id

  posix_user {
    uid = 0
    gid = 0
  }
}

resource "aws_security_group" "mount_target" {
  name        = "${var.project_name}-s3files-mt"
  description = "S3 Files mount target: NFS 2049 from backend and pipeline tasks only."
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project_name}-s3files-mt-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "mount_from_backend" {
  security_group_id            = aws_security_group.mount_target.id
  referenced_security_group_id = var.backend_security_group_id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
  description                  = "NFS from backend tasks"
}

resource "aws_vpc_security_group_ingress_rule" "mount_from_pipeline" {
  security_group_id            = aws_security_group.mount_target.id
  referenced_security_group_id = var.pipeline_security_group_id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
  description                  = "NFS from pipeline tasks"
}

resource "aws_s3files_mount_target" "this" {
  for_each = toset(var.public_subnet_ids)

  file_system_id  = aws_s3files_file_system.this.id
  subnet_id       = each.value
  security_groups = [aws_security_group.mount_target.id]
}
