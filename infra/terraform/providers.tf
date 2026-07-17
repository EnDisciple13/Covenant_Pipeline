provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "covenant-pipeline"
      Environment = "poc"
      ManagedBy   = "terraform"
    }
  }
}
