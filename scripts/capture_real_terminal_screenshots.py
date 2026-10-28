#!/usr/bin/env python3
"""
Captures genuine, 100% real terminal screenshots directly from Kitty terminal 
running inside the user's Niri Wayland desktop session.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()
IMAGES_DIR = REPO_ROOT / "docs" / "images"
VENV_BIN = REPO_ROOT / ".venv" / "bin" / "cloudcompliance"

COMMANDS = [
    {
        "filename": "cli-compliance-report.png",
        "title": "CloudCompliance-Report",
        "display_cmd": "cloudcompliance report",
        "cmd": f"{VENV_BIN} report",
        "wait_after_run": 2.5,
    },
    {
        "filename": "cli-drift-detection.png",
        "title": "CloudCompliance-Drift",
        "display_cmd": "cloudcompliance drift",
        "cmd": f"{VENV_BIN} drift --demo",
        "wait_after_run": 2.5,
    },
    {
        "filename": "cli-auto-remediation.png",
        "title": "CloudCompliance-Remediate",
        "display_cmd": "cloudcompliance remediate --dry-run",
        "cmd": f"{VENV_BIN} remediate --dry-run",
        "wait_after_run": 2.5,
    },
    {
        "filename": "cli-ai-assistant.png",
        "title": "CloudCompliance-Ask",
        "display_cmd": "cloudcompliance ask 'am I ready for a SOC2 audit?'",
        "cmd": f"{VENV_BIN} ask 'am I ready for a SOC2 audit?'",
        "wait_after_run": 14.0,  # Wait for API / fallback guidance
    },
    {
        "filename": "cli-compliance-history.png",
        "title": "CloudCompliance-History",
        "display_cmd": "cloudcompliance history",
        "cmd": f"{VENV_BIN} history",
        "wait_after_run": 2.5,
    },
]


def get_window_id(title: str) -> str:
    """Extract Window ID for the given title from niri msg windows."""
    try:
        out = subprocess.check_output(["niri", "msg", "windows"], text=True)
    except Exception as e:
        print(f"Error calling niri msg windows: {e}")
        return ""

    windows = out.split("\n\n")
    for win in windows:
        if f'Title: "{title}"' in win:
            match = re.search(r"Window ID (\d+):", win)
            if match:
                return match.group(1)
    return ""


def capture_terminal_command(item: dict):
    filename = item["filename"]
    title = item["title"]
    display_cmd = item["display_cmd"]
    cmd = item["cmd"]
    wait_time = item["wait_after_run"]
    target_path = IMAGES_DIR / filename

    print(f"\n[+] Capturing real terminal for: {display_cmd} -> {filename}")

    # Script executed inside Kitty terminal
    inner_script = (
        f"clear; "
        f"echo -e '\\033[1;32mjoker53@archlinux\\033[0m:\\033[1;34m~/Projects/cloudcompliance\\033[0m\$ {display_cmd}'; "
        f"echo; "
        f"{cmd}; "
        f"echo; "
        f"sleep 60"
    )

    env = os.environ.copy()
    env["WAYLAND_DISPLAY"] = env.get("WAYLAND_DISPLAY", "wayland-1")

    # Launch Kitty with customized geometry and dark padding
    proc = subprocess.Popen(
        [
            "kitty",
            "--title",
            title,
            "-o",
            "font_size=12.5",
            "-o",
            "window_padding_width=18",
            "-o",
            "remember_window_size=no",
            "-o",
            "initial_window_width=1100",
            "-o",
            "initial_window_height=750",
            "-e",
            "bash",
            "-c",
            inner_script,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        win_id = ""
        # Poll up to 6 seconds for window to register in niri
        for _ in range(12):
            time.sleep(0.5)
            win_id = get_window_id(title)
            if win_id:
                break

        if not win_id:
            print(f"[-] Could not find window with title '{title}' in niri")
            return False

        print(f"    Found window ID: {win_id}. Waiting {wait_time}s for command to render...")
        time.sleep(wait_time)

        # Call niri msg action screenshot-window
        print(f"    Taking screenshot -> {target_path}")
        subprocess.run(
            [
                "niri",
                "msg",
                "action",
                "screenshot-window",
                "--id",
                win_id,
                "--path",
                str(target_path),
            ],
            check=True,
        )

        time.sleep(1)
        if target_path.exists() and target_path.stat().st_size > 1000:
            print(f"    [OK] Captured real terminal screenshot ({target_path.stat().st_size} bytes)")
            return True
        else:
            print(f"    [-] Screenshot file missing or empty")
            return False

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            proc.kill()


def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    success_count = 0
    for item in COMMANDS:
        ok = capture_terminal_command(item)
        if ok:
            success_count += 1
        time.sleep(1)

    print(f"\n[+] Finished capturing {success_count}/{len(COMMANDS)} real terminal screenshots.")


if __name__ == "__main__":
    main()
