variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "environment" {
  description = "Name prefix for shared delivery resources"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in the format owner/repo"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to track for changes"
  type        = string
  default     = "main"
}

variable "approval_notification_arn" {
  description = "SNS topic ARN for manual approval notifications"
  type        = string
  default     = ""
}

variable "hubble_repository_name" {
  description = "ECR repository name for cds-hubble"
  type        = string
  default     = "cds-hubble"
}

variable "production_cluster_name" {
  description = "ECS cluster name for production"
  type        = string
}

variable "production_hubble_service_name" {
  description = "CDS Hubble ECS service name in production"
  type        = string
}
