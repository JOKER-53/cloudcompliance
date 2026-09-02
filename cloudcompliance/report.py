#!/usr/bin/env python3
"""
CloudCompliance — SOC2 Evidence Report Generator
Reads terraform.tfstate and maps resources to SOC2 Trust Service Criteria
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def load_controls() -> dict:
    controls_path = Path(__file__).parent / "controls.json"
    with open(controls_path) as f:
        return json.load(f)

SOC2_CONTROLS = load_controls()


def load_tfstate(path: str) -> dict:
    tfstate_path = Path(path)
    if not tfstate_path.exists():
        console.print(f"[red]Error: tfstate not found at {path}[/red]")
        sys.exit(1)
    with open(tfstate_path) as f:
        return json.load(f)


def extract_resources(tfstate: dict) -> list:
    resources = []
    for resource in tfstate.get("resources", []):
        resources.append({
            "type": resource.get("type"),
            "name": resource.get("name"),
            "module": resource.get("module", "root"),
            "tags": resource.get("instances", [{}])[0]
                          .get("attributes", {})
                          .get("tags", {}),
        })
    return resources


def evaluate_controls(resources: list) -> dict:
    found_types = set(r["type"] for r in resources)
    results = {}
    for control_id, control in SOC2_CONTROLS.items():
        matched = [t for t in control["resources"] if t in found_types]
        missing = [t for t in control["resources"] if t not in found_types]
        if len(matched) == len(control["resources"]):
            status = "PASS"
        elif len(matched) > 0:
            status = "PARTIAL"
        else:
            status = "FAIL"
        results[control_id] = {
            "title": control["title"],
            "description": control["description"],
            "status": status,
            "matched": matched,
            "missing": missing,
        }
    return results


def save_markdown(results: dict, resources: list, score: int, pass_count: int):
    md_path = Path(__file__).parent.parent / "compliance" / "compliance_report.md"
    with open(md_path, "w") as f:
        f.write("# CloudCompliance — SOC2 Evidence Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total resources provisioned:** {len(resources)}  \n")
        f.write(f"**Compliance score:** {score}% ({pass_count}/{len(results)} controls passing)\n\n")
        f.write("## Control Coverage\n\n")
        f.write("| Control | Title | Status | Matched Resources |\n")
        f.write("|---------|-------|--------|-------------------|\n")
        for control_id, result in results.items():
            if result["status"] == "PASS":
                status_md = "✅ PASS"
            elif result["status"] == "PARTIAL":
                status_md = "⚠️ PARTIAL"
            else:
                status_md = "❌ FAIL"
            matched = ", ".join(result["matched"][:3]) if result["matched"] else "none"
            f.write(f"| {control_id} | {result['title']} | {status_md} | {matched} |\n")
        f.write(f"\n## Summary\n\n")
        f.write(f"SOC2 Compliance Score: **{score}%** ({pass_count}/{len(results)} controls passing)\n\n")
        f.write("## Standards Referenced\n\n")
        f.write("- AICPA SOC2 Trust Services Criteria 2017\n")
        f.write("- CIS AWS Foundations Benchmark v2.0\n")
        f.write("- NIST SP 800-53 Rev 5\n")
    console.print(f"[dim]Markdown report → {md_path}[/dim]")


def print_report(results: dict, resources: list, output_path: Path = None):
    console.print()
    console.print(Panel.fit(
        "[bold cyan]CloudCompliance — SOC2 Evidence Report[/bold cyan]\n"
        f"[dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
        f"[dim]Total resources provisioned: {len(resources)}[/dim]",
        border_style="cyan"
    ))
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("Control", style="cyan", width=8)
    table.add_column("Title", width=35)
    table.add_column("Status", width=10)
    table.add_column("Matched Resources", width=40)

    pass_count = 0
    for control_id, result in results.items():
        status = result["status"]
        if status == "PASS":
            status_str = "[green]✅ PASS[/green]"
            pass_count += 1
        elif status == "PARTIAL":
            status_str = "[yellow]⚠️  PARTIAL[/yellow]"
        else:
            status_str = "[red]❌ FAIL[/red]"
        matched_str = ", ".join(result["matched"]) if result["matched"] else "[dim]none[/dim]"
        table.add_row(control_id, result["title"], status_str, matched_str)

    console.print(table)
    console.print()

    score = int((pass_count / len(results)) * 100)
    color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
    console.print(Panel.fit(
        f"[bold {color}]SOC2 Compliance Score: {score}% ({pass_count}/{len(results)} controls passing)[/bold {color}]",
        border_style=color
    ))

    missing_any = [(cid, r) for cid, r in results.items() if r["missing"]]
    if missing_any:
        console.print()
        console.print("[bold yellow]Resources to add for full compliance:[/bold yellow]")
        for control_id, result in missing_any:
            for m in result["missing"]:
                console.print(f"  [dim]{control_id}[/dim] → [red]{m}[/red]")

    output = {
        "generated_at": datetime.now().isoformat(),
        "total_resources": len(resources),
        "compliance_score": score,
        "controls": results,
    }

    if output_path is None:
        output_path = Path(__file__).parent.parent / "compliance" / "compliance_report.json"

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    console.print()
    console.print(f"[dim]Evidence saved → {output_path}[/dim]")

    save_markdown(results, resources, score, pass_count)

    from cloudcompliance.history import save_score
    save_score(output_path)
    # Slack notification
    from cloudcompliance.notifications import notify_compliance_score
    notify_compliance_score(score, pass_count, len(results), len(resources))

def run(tfstate_path: str = None, output_path: str = None):
    if tfstate_path is None:
        tfstate_path = Path(__file__).parent.parent / "terraform" / "terraform.tfstate"
    console.print(f"[dim]Reading state from: {tfstate_path}[/dim]")
    tfstate = load_tfstate(str(tfstate_path))
    resources = extract_resources(tfstate)
