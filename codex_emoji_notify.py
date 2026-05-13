#!/usr/bin/env python3
"""Codex CLI 응답 완료 알림 스크립트.

Usage:
  python codex_emoji_notify.py
  python codex_emoji_notify.py "배포 끝!"
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> bool:
    """외부 명령 실행. 실패해도 예외를 올리지 않고 False 반환."""
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def build_emoji_message(message: str, emoji: str = "🎉") -> str:
    """눈에 잘 띄도록 이모티콘이 포함된 알림 메시지를 생성한다."""
    clean = message.strip()
    if not clean:
        clean = "Codex 응답이 완료되었습니다"

    # 이미 이모지가 포함된 메시지는 중복 장식을 피한다.
    if emoji in clean:
        return clean
    return f"{emoji} {clean} {emoji}"


def send_custom_notification(message: str, title: str = "Codex Notify") -> None:
    """운영체제별 알림을 전송하고, 항상 콘솔/벨 폴백을 수행한다."""
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

    # 어디서든 최소한의 주의를 끌 수 있도록 터미널 벨을 울린다.
    print("\a", end="")


def main() -> int:
    raw_message = sys.argv[1] if len(sys.argv) > 1 else "Codex CLI 응답이 완료되었습니다."
    final_message = build_emoji_message(raw_message, emoji="🚀")
    send_custom_notification(final_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
