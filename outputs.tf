output "vpc_id" {
  description = "ID of the provisioned SOC2 VPC (CC6.1)"
  value       = module.compliance_baseline.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets with default deny-all security groups (CC6.1)"
  value       = module.compliance_baseline.private_subnet_ids
}

output "audit_bucket_id" {
  description = "ID of the versioned, tamper-evident SOC2 audit logging S3 bucket (CC7.2)"
  value       = module.compliance_baseline.audit_bucket_id
}

output "kms_key_id" {
  description = "ID of the KMS customer managed encryption key (CC6.7)"
  value       = module.compliance_baseline.kms_key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS customer managed key (CC6.7)"
  value       = module.compliance_baseline.kms_key_arn
}

output "app_role_arn" {
  description = "ARN of the least-privilege IAM application role (CC6.2)"
  value       = module.compliance_baseline.app_role_arn
}

output "compliance_score" {
  description = "SOC2 controls implemented by baseline"
  value       = module.compliance_baseline.compliance_score
}
