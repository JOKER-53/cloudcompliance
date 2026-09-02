import os
import json
from cloudcompliance.drift.detector import DriftDetector

def handler(event, context):
    """
    AWS Lambda Handler for real-time drift detection triggered by EventBridge/CloudTrail.
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Optional: check if the event is a relevant modification (e.g., RunInstances, CreateBucket)
    # and skip if not relevant to avoid running drift detection on every single read event.
    
    tfstate_url = os.environ.get("TFSTATE_URL")
    if not tfstate_url:
        print("Error: TFSTATE_URL environment variable is required (e.g., s3://my-bucket/terraform.tfstate)")
        return {"statusCode": 500, "body": "TFSTATE_URL not configured"}
        
    print(f"Running drift detection against {tfstate_url}")
    
    detector = DriftDetector(tfstate_path=tfstate_url)
    drift_count = detector.run()
    
    if drift_count > 0:
        print(f"🚨 {drift_count} drift findings detected!")
        # If auto-remediation is enabled via env var, we can trigger it here
        if os.environ.get("AUTO_REMEDIATE", "false").lower() == "true":
            from cloudcompliance.remediation import RemediationEngine
            print("Running auto-remediation...")
            engine = RemediationEngine()
            engine.run()
            
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "DRIFT_DETECTED",
                "drift_count": drift_count,
                "findings": detector.drift_findings
            })
        }
        
    print("✅ No drift detected")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "COMPLIANT",
            "drift_count": 0
        })
    }
