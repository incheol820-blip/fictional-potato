#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_INDEX="$SRC_DIR/.git/index"
DESKTOP_DIR="$HOME/Desktop"
TARGET_INDEX="$DESKTOP_DIR/index"
TARGET_RUNNER="$DESKTOP_DIR/감성일기"

mkdir -p "$DESKTOP_DIR"
cp "$SRC_INDEX" "$TARGET_INDEX"

cat > "$TARGET_RUNNER" <<'RUNNER'
#!/usr/bin/env bash
set -euo pipefail
INDEX_FILE="$HOME/Desktop/index"

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "index 파일을 찾을 수 없습니다: $INDEX_FILE"
  exit 1
fi

echo "감성일기 실행: $INDEX_FILE"
wc -c "$INDEX_FILE"
RUNNER

chmod +x "$TARGET_RUNNER"

echo "완료: $TARGET_INDEX 복사 및 $TARGET_RUNNER 실행 파일 생성"
