terraform {
  backend "s3" {
    key          = "demo/terraform.tfstate"
    bucket       = "cosmicds-terraform-state"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
