#!/usr/bin/env python3
"""Basic custom notification script for Codex CLI completion hooks.

Usage examples:
  python codex_emoji_notify.py
  python codex_emoji_notify.py "작업이 끝났어요!"

You can wire this script into your Codex CLI post-response hook.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> bool:
    """Run a command safely; return True on success."""
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def main() -> int:
    message = sys.argv[1] if len(sys.argv) > 1 else "✅ Codex CLI 응답이 완료되었습니다."
    title = "Codex Notify"

    # Always print to console as a fallback.
    print(f"{title}: {message}")

    system = platform.system().lower()

    if system == "darwin" and shutil.which("osascript"):
        run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
    elif system == "linux" and shutil.which("notify-send"):
        run(["notify-send", title, message])
    elif system == "windows" and shutil.which("powershell"):
        run(
            [
                "powershell",
                "-Command",
                (
                    "Add-Type -AssemblyName System.Windows.Forms;"
                    f"[System.Windows.Forms.MessageBox]::Show('{message}','{title}')"
                ),
            ]
        )

    # Terminal bell as an extra, cross-platform nudge.
    print("\a", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
