# Complete Example

Deploys the full SOC2 baseline — all 7 controls — in a single module call.

## Usage

```hcl
module "cloudcompliance" {
  source  = "JOKER-53/cloudcompliance/aws"
  version = "1.0.0"

  project_name = "my-startup"
  environment  = "prod"
  aws_region   = "us-east-1"
}
```

## What gets deployed

- Private VPC with 2 subnets (CC6.1)
- IAM password policy + least-privilege role (CC6.2)
- HTTPS-only S3 policies (CC6.6)
- KMS encryption on all data (CC6.7)
- CloudWatch alarms + Config rules (CC7.1)
- Versioned audit bucket + flow logs (CC7.2)
- IaC-controlled change management (CC8.1)
