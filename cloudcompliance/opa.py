import json
import subprocess
import tempfile
from pathlib import Path
from rich.console import Console

console = Console()

def evaluate_rego(tfstate_path: str, rego_path: str) -> dict:
    """Evaluates terraform state against a custom Rego policy using the OPA CLI."""
    if not Path(rego_path).exists():
        console.print(f"[red]Error: Rego file not found at {rego_path}[/red]")
        return {}

    try:
        # Check if opa is installed
        subprocess.run(["opa", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[yellow]Warning: 'opa' executable not found in PATH. Skipping custom Rego checks.[/yellow]")
        return {}

    try:
        # Evaluate opa with data (tfstate) and policy (rego)
        # Assuming the rego file defines a rule `deny` or `violations` in package `compliance`
        result = subprocess.run(
            ["opa", "eval", "-i", tfstate_path, "-d", rego_path, "data.compliance.violations"],
            capture_output=True,
            text=True,
            check=True
        )
        output = json.loads(result.stdout)
        
        # Parse results
        violations = []
        if output.get("result") and len(output["result"]) > 0:
            violations = output["result"][0].get("expressions", [{}])[0].get("value", [])
        
        return {"violations": violations}
        
    except Exception as e:
        console.print(f"[red]Error running OPA: {e}[/red]")
        return {}
