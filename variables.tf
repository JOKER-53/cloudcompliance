variable "environment" {
  type        = string
  description = "Deployment environment (local, dev, staging, prod)"
  default     = "local"

  validation {
    condition     = contains(["local", "dev", "staging", "prod"], var.environment)
    error_message = "Environment must be local, dev, staging, or prod."
  }
}

variable "project_name" {
  type        = string
  description = "Project name used for resource naming and SOC2 tagging"
  default     = "cloudcompliance"
}

variable "aws_region" {
  type        = string
  description = "AWS region for infrastructure deployment"
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  type        = string
  description = "LocalStack endpoint URL — set to empty string for real AWS"
  default     = ""
}
