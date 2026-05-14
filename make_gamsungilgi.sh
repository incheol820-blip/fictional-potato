#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./make_gamsungilgi.sh [emotion-diary directory]
# Example:
#   ./make_gamsungilgi.sh /mnt/c/Users/me/projects/emotion-diary

SOURCE_DIR="${1:-$PWD/emotion-diary}"
SOURCE_INDEX="$SOURCE_DIR/index"

if [[ ! -f "$SOURCE_INDEX" ]]; then
  echo "index 파일을 찾을 수 없습니다: $SOURCE_INDEX"
  echo "emotion-diary 경로를 첫 번째 인자로 전달해 주세요."
  exit 1
fi

get_windows_desktop() {
  # 1) Most accurate in WSL: ask Windows for the Desktop known-folder path.
  if command -v powershell.exe >/dev/null 2>&1; then
    local desktop_win
    desktop_win=$(powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('Desktop')" 2>/dev/null | tr -d '\r' | tail -n 1 || true)
    if [[ -n "$desktop_win" ]] && command -v wslpath >/dev/null 2>&1; then
      local desktop_wsl
      desktop_wsl=$(wslpath "$desktop_win" 2>/dev/null || true)
      if [[ -d "$desktop_wsl" ]]; then
        echo "$desktop_wsl"
        return 0
      fi
    fi
  fi

  # 2) Fallback: classic local Desktop path.
  for desktop in /mnt/c/Users/*/Desktop; do
    [[ -d "$desktop" ]] && { echo "$desktop"; return 0; }
  done

  # 3) Fallback: OneDrive Desktop path.
  for desktop in /mnt/c/Users/*/OneDrive/Desktop; do
    [[ -d "$desktop" ]] && { echo "$desktop"; return 0; }
  done

  return 1
}

WINDOWS_DESKTOP="$(get_windows_desktop || true)"
if [[ -z "$WINDOWS_DESKTOP" ]]; then
  echo "Windows 바탕화면 경로를 찾을 수 없습니다."
  echo "확인 경로: Desktop, OneDrive/Desktop"
  exit 1
fi

TARGET_INDEX="$WINDOWS_DESKTOP/index"
TARGET_RUNNER="$WINDOWS_DESKTOP/감성일기.bat"

cp "$SOURCE_INDEX" "$TARGET_INDEX"

cat > "$TARGET_RUNNER" <<'BAT'
@echo off
setlocal
set INDEX_FILE=%USERPROFILE%\Desktop\index

if not exist "%INDEX_FILE%" (
  if exist "%USERPROFILE%\OneDrive\Desktop\index" (
    set INDEX_FILE=%USERPROFILE%\OneDrive\Desktop\index
  ) else (
    echo index 파일을 찾을 수 없습니다: %USERPROFILE%\Desktop\index
    exit /b 1
  )
)

start "" "%INDEX_FILE%"
BAT

echo "완료:"
echo "- 감성일기 원본: $SOURCE_INDEX"
echo "- index 복사: $TARGET_INDEX"
echo "- 실행 파일 생성: $TARGET_RUNNER"
