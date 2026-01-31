#!/bin/bash
# docs 폴더에 .md 파일이 생성/수정될 때 CLAUDE.md의 문서 목록을 자동 업데이트
# 마커(DOCS_LIST_START/END) 사이의 내용만 교체하여 안전하게 업데이트

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# docs 폴더의 .md 파일인지 확인
if [[ ! "$FILE_PATH" =~ /docs/.*\.md$ ]]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_MD="$PROJECT_DIR/CLAUDE.md"
DOCS_DIR="$PROJECT_DIR/docs"

# CLAUDE.md가 없거나 마커가 없으면 종료
if [ ! -f "$CLAUDE_MD" ]; then
  exit 0
fi

if ! grep -q "DOCS_LIST_START" "$CLAUDE_MD"; then
  echo "DOCS_LIST_START 마커가 없습니다." >&2
  exit 0
fi

# 새로운 문서 목록 생성
generate_section() {
  echo "### 문서 목록"
  echo ""

  # direction
  if [ -d "$DOCS_DIR/direction" ]; then
    echo "#### direction (기획)"
    for f in "$DOCS_DIR/direction"/*.md; do
      [ -f "$f" ] && echo "- \`docs/direction/$(basename "$f")\`"
    done
    echo ""
  fi

  # plan
  if [ -d "$DOCS_DIR/plan" ]; then
    echo "#### plan (계획안)"
    for f in "$DOCS_DIR/plan"/*.md; do
      [ -f "$f" ] && echo "- \`docs/plan/$(basename "$f")\`"
    done
    echo ""
  fi

  # report
  if [ -d "$DOCS_DIR/report" ]; then
    echo "#### report (리포트)"
    for f in "$DOCS_DIR/report"/*.md; do
      [ -f "$f" ] && echo "- \`docs/report/$(basename "$f")\`"
    done
  fi
}

# 새 섹션 내용 생성
NEW_SECTION=$(generate_section)

# Python으로 마커 사이 내용 교체 (더 안전함)
python3 << EOF
import re

with open("$CLAUDE_MD", "r") as f:
    content = f.read()

new_section = """$NEW_SECTION"""

# 마커 사이 내용 교체
pattern = r'(<!-- DOCS_LIST_START -->).*?(<!-- DOCS_LIST_END -->)'
replacement = r'\1\n' + new_section + r'\n\2'
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open("$CLAUDE_MD", "w") as f:
    f.write(new_content)
EOF

echo "CLAUDE.md 문서 목록 업데이트 완료" >&2
exit 0
