variable "tfstate_s3_uri" {
  description = "The S3 URI of the terraform state file (e.g., s3://my-bucket/terraform.tfstate)"
  type        = string
}

variable "auto_remediate" {
  description = "Whether to run auto-remediation inside the Lambda"
  type        = bool
  default     = false
}

resource "aws_iam_role" "lambda_exec" {
  name = "cloudcompliance-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess" # Note: would need Write access for remediation
}

resource "aws_lambda_function" "drift_detector" {
  filename         = "cloudcompliance.zip" # Assumes code is packaged
  function_name    = "cloudcompliance-drift-detector"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "cloudcompliance.lambda_handler.handler"
  runtime          = "python3.9"
  timeout          = 300

  environment {
    variables = {
      TFSTATE_URL    = var.tfstate_s3_uri
      AUTO_REMEDIATE = tostring(var.auto_remediate)
    }
  }
}

# EventBridge Rule to trigger Lambda on any AWS API call that modifies infrastructure
resource "aws_cloudwatch_event_rule" "infra_changes" {
  name        = "cloudcompliance-infra-changes"
  description = "Triggers CloudCompliance drift detection on infra changes"
  event_pattern = jsonencode({
    "source" : ["aws.ec2", "aws.s3", "aws.iam", "aws.kms"],
    "detail-type" : ["AWS API Call via CloudTrail"],
    "detail" : {
      "eventName" : [
        "CreateBucket", "DeleteBucket",
        "CreateRole", "DeleteRole",
        "RunInstances", "TerminateInstances",
        "ScheduleKeyDeletion"
      ]
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.infra_changes.name
  target_id = "TriggerCloudComplianceLambda"
  arn       = aws_lambda_function.drift_detector.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.drift_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.infra_changes.arn
}
