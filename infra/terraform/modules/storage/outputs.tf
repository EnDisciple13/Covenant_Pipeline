output "file_system_arn" {
  description = "ARN of the S3 Files file system linked to the persistent data bucket."
  value       = aws_s3files_file_system.this.arn
}

output "access_point_arn" {
  description = "ARN of the S3 Files access point (POSIX uid/gid 0)."
  value       = aws_s3files_access_point.this.arn
}

output "mount_target_ids" {
  description = "IDs of per-AZ S3 Files mount targets."
  value       = [for mt in aws_s3files_mount_target.this : mt.id]
}

output "mount_sg_id" {
  description = "Security group ID for S3 Files mount targets (TCP 2049)."
  value       = aws_security_group.mount_target.id
}
