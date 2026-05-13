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
        subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return True
    except Exception:
        return False


def notify_darwin(title: str, message: str) -> bool:
    if not shutil.which("osascript"):
        return False

    script = (
        "display notification "
        f"{message!r} "
        "with title "
        f"{title!r}"
    )
    return run(["osascript", "-e", script])


def notify_linux(title: str, message: str) -> bool:
    if not shutil.which("notify-send"):
        return False
    return run(["notify-send", title, message])


def notify_windows(title: str, message: str) -> bool:
    if not shutil.which("powershell"):
        return False

    ps = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        f"[System.Windows.Forms.MessageBox]::Show({message!r},{title!r})"
    )
    return run(["powershell", "-Command", ps])


def main() -> int:
    message = " ".join(sys.argv[1:]).strip() or "✅ Codex CLI 응답이 완료되었습니다."
    title = "Codex Notify"

    # Always print to console as a fallback.
    print(f"{title}: {message}")

    system = platform.system().lower()

    if system == "darwin":
        notify_darwin(title, message)
    elif system == "linux":
        notify_linux(title, message)
    elif system == "windows":
        notify_windows(title, message)

    # Terminal bell as an extra, cross-platform nudge.
    print("\a", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
