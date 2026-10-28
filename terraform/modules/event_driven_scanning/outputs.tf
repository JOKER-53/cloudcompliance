output "lambda_arn" {
  description = "The ARN of the drift detection Lambda function"
  value       = aws_lambda_function.drift_detector.arn
}

output "lambda_role_arn" {
  description = "The ARN of the IAM role used by the Lambda function"
  value       = aws_iam_role.lambda_exec.arn
}

output "eventbridge_rule_arn" {
  description = "The ARN of the EventBridge rule monitoring infra changes"
  value       = aws_cloudwatch_event_rule.infra_changes.arn
}
