#!/usr/bin/env python3
"""
CloudCompliance — AI Compliance Assistant
Powered by NVIDIA NIM
Answers questions about your actual compliance state
"""
import json
import os
import sys
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

console = Console()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"


def load_context() -> dict:
    """Load compliance report, drift report and tfstate as context."""
    base = Path(__file__).parent.parent
    context = {}

    report_path = base / "compliance" / "compliance_report.json"
    if report_path.exists():
        with open(report_path) as f:
            context["compliance_report"] = json.load(f)

    drift_path = base / "compliance" / "drift_report.json"
    if drift_path.exists():
        with open(drift_path) as f:
            context["drift_report"] = json.load(f)

    history_path = base / "compliance" / "history_export.json"
    if history_path.exists():
        with open(history_path) as f:
            context["history"] = json.load(f)

    tfstate_path = base / "terraform" / "terraform.tfstate"
    if tfstate_path.exists():
        with open(tfstate_path) as f:
            state = json.load(f)
            context["resource_count"] = len(state.get("resources", []))
            context["resource_types"] = list(
                set(r.get("type") for r in state.get("resources", []) if r.get("type"))
            )

    return context


def _truncate(obj, max_chars: int = 12000) -> str:
    """Serialize JSON, truncating if it is very large."""
    text = json.dumps(obj, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def build_system_prompt(context: dict) -> str:
    report = context.get("compliance_report") or {}
    drift = context.get("drift_report") or {}

    return f"""You are CloudCompliance AI — an expert SOC2 compliance assistant.
You have access to the user's actual AWS infrastructure compliance data.

COMPLIANCE REPORT:
{_truncate(report)}

DRIFT REPORT:
{_truncate(drift)}

INFRASTRUCTURE SUMMARY:
- Total resources: {context.get("resource_count", "unknown")}
- Resource types present: {", ".join(context.get("resource_types") or []) or "unknown"}

INSTRUCTIONS:
- Answer questions about the user's actual compliance state
- Be specific — reference actual controls, scores, and resources from their data
- Give actionable recommendations
- If drift was detected, explain the risk and how to fix it
- Keep answers concise and practical
- Format with markdown for clarity
- Never make up data — only reference what's in the reports above
"""


def ask(question: str, api_key: str):
    context = load_context()
    if not context:
        console.print(
            "[red]Error: No compliance data found. Run 'cloudcompliance report' first.[/red]"
        )
        sys.exit(1)

    system_prompt = build_system_prompt(context)

    console.print()
    console.print(
        Panel.fit(
            f"[bold cyan]CloudCompliance AI[/bold cyan]\n"
            f"[dim]Powered by NVIDIA NIM — {MODEL}[/dim]",
            border_style="cyan",
        )
    )
    console.print()
    console.print(f"[dim]Question:[/dim] {question}")
    console.print()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": 2048,
        "temperature": 0.3,
        "stream": False,
    }

    try:
        t0 = time.perf_counter()
        with console.status(
            f"[cyan]Thinking with {MODEL}…[/cyan]",
            spinner="dots",
        ):
            response = requests.post(
                NVIDIA_API_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )
        elapsed = time.perf_counter() - t0

        response.raise_for_status()
        data = response.json()

        msg = data["choices"][0]["message"]
        # gpt-oss may put the answer in content or only in reasoning_content
        answer = msg.get("content") or msg.get("reasoning_content") or ""

        if not answer.strip():
            console.print("[red]Error: Empty model response.[/red]")
            console.print(f"[dim]{json.dumps(msg, indent=2)[:800]}[/dim]")
            sys.exit(1)

        console.print(
            Panel(
                Markdown(answer),
                title="[bold green]AI Response[/bold green]",
                border_style="green",
            )
        )
        console.print(f"[dim]Answered in {elapsed:.1f}s[/dim]")

    except requests.exceptions.Timeout:
        console.print(
            "[red]Error: Request timed out after 180s. "
            "The model may be under load — try again.[/red]"
        )
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]Error: API request failed — {e}[/red]")
        try:
            console.print(f"[dim]Status: {response.status_code}[/dim]")
            console.print(f"[dim]Body: {response.text[:500]}[/dim]")
        except Exception:
            pass
        sys.exit(1)
    except requests.exceptions.JSONDecodeError:
        console.print("[red]Error: API returned non-JSON response.[/red]")
        try:
            console.print(f"[dim]Status: {response.status_code}[/dim]")
            console.print(f"[dim]Body: {response.text[:500]}[/dim]")
        except Exception:
            pass
        sys.exit(1)
    except (KeyError, IndexError, TypeError) as e:
        console.print(f"[red]Error: Unexpected API response format — {e}[/red]")
        try:
            console.print(f"[dim]Body: {response.text[:500]}[/dim]")
        except Exception:
            pass
        sys.exit(1)


def main(question: str, api_key: str = None):
    if api_key is None:
        api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        console.print("[red]Error: NVIDIA_API_KEY not set.[/red]")
        console.print("[dim]Export it: export NVIDIA_API_KEY='your-key'[/dim]")
        sys.exit(1)
    ask(question, api_key)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print('[red]Usage: python assistant.py "your question"[/red]')
        sys.exit(1)
    main(sys.argv[1])
