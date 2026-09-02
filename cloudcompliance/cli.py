#!/usr/bin/env python3
"""
CloudCompliance CLI Entrypoint
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from cloudcompliance.report import load_tfstate, extract_resources, evaluate_controls, print_report

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="CloudCompliance — SOC2 evidence, drift detection, history, AI assistant and auto-remediation"
    )
    parser.add_argument(
        "--tfstate",
        default=str(Path(__file__).parent.parent / "terraform" / "terraform.tfstate"),
        help="Path or S3 URI to terraform.tfstate (e.g. s3://my-bucket/terraform.tfstate)"
    )
    subparsers = parser.add_subparsers(dest="command")

    report_parser = subparsers.add_parser("report", help="Generate compliance evidence report")
    report_parser.add_argument(
        "--framework",
        default="soc2",
        choices=["soc2", "hipaa", "pcidss"],
        help="Compliance framework to evaluate against (default: soc2)"
    )
    report_parser.add_argument(
        "--rego",
        default=None,
        help="Path to a custom OPA Rego policy file to evaluate alongside standard controls"
    )

    drift_parser = subparsers.add_parser("drift", help="Detect infrastructure drift")
    drift_parser.add_argument(
        "--endpoint",
        default="http://localhost:4566",
        help="AWS endpoint URL (default: LocalStack)"
    )

    history_parser = subparsers.add_parser("history", help="Show compliance score history")
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of entries to show (default: 10)"
    )
    history_parser.add_argument(
        "--export",
        action="store_true",
        help="Export history as JSON for auditors"
    )

    ask_parser = subparsers.add_parser("ask", help="Ask AI about your compliance state")
    ask_parser.add_argument("question", help="Your compliance question")
    ask_parser.add_argument(
        "--api-key",
        default=None,
        help="NVIDIA NIM API key (or set NVIDIA_API_KEY env var)"
    )

    remediate_parser = subparsers.add_parser("remediate", help="Auto-remediate drift findings")
    remediate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    remediate_parser.add_argument(
        "--endpoint",
        default=None,
        help="AWS endpoint URL"
    )
    schedule_parser = subparsers.add_parser("schedule", help="Run drift detection on a schedule")
    schedule_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in minutes (default: 60)"
    )
    schedule_parser.add_argument(
        "--endpoint",
        default=None,
        help="AWS endpoint URL"
    )
    
    serve_parser = subparsers.add_parser("serve", help="Start live compliance dashboard")
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run dashboard on (default: 8080)"
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )    

    args = parser.parse_args()

    tfstate_path = args.tfstate

    if args.command == "drift":
        from cloudcompliance.drift.detector import DriftDetector
        detector = DriftDetector(
            tfstate_path=tfstate_path,
            endpoint_url=args.endpoint
        )
        drift_count = detector.run()
        sys.exit(1 if drift_count > 0 else 0)

    elif args.command == "history":
        from cloudcompliance.history import show_history, export_history
        show_history(limit=args.limit)
        if args.export:
            export_history()

    elif args.command == "ask":
        from cloudcompliance.assistant import main as ask_main
        ask_main(args.question, args.api_key)

    elif args.command == "remediate":
        from cloudcompliance.remediation import RemediationEngine
        engine = RemediationEngine(
            endpoint_url=args.endpoint,
            dry_run=args.dry_run
        )
        engine.run()

    elif args.command == "serve":
        from cloudcompliance.dashboard import serve
        serve(host=args.host, port=args.port)
    
    elif args.command == "schedule":
        from cloudcompliance.scheduler import schedule
        schedule(
            interval_minutes=args.interval,
            endpoint_url=args.endpoint
        )    

    else:
        console.print(f"[dim]Reading state from: {tfstate_path}[/dim]")
        tfstate = load_tfstate(tfstate_path)
        resources = extract_resources(tfstate)
        
        from cloudcompliance.report import load_controls
        framework = getattr(args, "framework", "soc2")
        controls = load_controls(framework)
        
        results = evaluate_controls(resources, controls)
        
        if getattr(args, "rego", None):
            from cloudcompliance.opa import evaluate_rego
            console.print(f"[dim]Evaluating custom Rego policy: {args.rego}[/dim]")
            rego_results = evaluate_rego(tfstate_path, args.rego)
            if "violations" in rego_results and rego_results["violations"]:
                console.print(f"\n[red]🔴 Custom OPA Rego Violations Found: {len(rego_results['violations'])}[/red]")
                for v in rego_results["violations"]:
                    console.print(f"  - [red]{v}[/red]")
                console.print()
            elif "violations" in rego_results:
                console.print("[green]✅ Custom OPA Rego Policy: PASS[/green]\n")
                
        print_report(results, resources, framework=framework)


if __name__ == "__main__":
    main()
