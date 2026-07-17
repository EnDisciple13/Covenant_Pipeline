terraform {
  backend "s3" {
    bucket       = "covenant-tfstate-andy-568728209842"
    key          = "env/poc/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
