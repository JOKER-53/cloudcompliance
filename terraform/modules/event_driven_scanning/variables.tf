variable "tfstate_s3_uri" {
  description = "The S3 URI of the terraform state file (e.g., s3://my-bucket/terraform.tfstate)"
  type        = string
}

variable "auto_remediate" {
  description = "Whether to run auto-remediation inside the Lambda"
  type        = bool
  default     = false
}

variable "lambda_zip_path" {
  description = "Path to the packaged Lambda zip file"
  type        = string
  default     = "cloudcompliance.zip"
}
