"""Verify a Timely skill export against the current repository sources.

Checks that the artifact's embedded version and digest match a fresh
deterministic rebuild, and that required section markers are present.
Exit code 0 means the export is reproducible and complete.
"""

import sys
from pathlib import Path

REPO_ROOT_CANDIDATES = 6


def _find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for _ in range(REPO_ROOT_CANDIDATES):
        if (current / "apps" / "api").is_dir() and (current / "skills").is_dir():
            return current
        current = current.parent
    raise SystemExit("저장소 루트를 찾지 못했습니다.")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: verify_timely_export.py <exported-skill.txt>")
        return 2

    repo_root = _find_repo_root(Path(__file__))
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "apps" / "api" / "src"))

    from scripts.export_timely_skill import SKILL_RELPATHS, build_export_text

    exported_path = Path(argv[1])
    if not exported_path.is_file():
        print(f"FAIL: 내보내기 파일이 없습니다: {exported_path}")
        return 1

    expected_text, expected_digest = build_export_text(repo_root)
    actual_text = exported_path.read_text(encoding="utf-8")

    failures: list[str] = []
    if actual_text != expected_text:
        failures.append("내보내기 내용이 현재 저장소 소스와 일치하지 않습니다.")
    if f"OWNDRAFT_SKILL_VERSION: {expected_digest[:12]}" not in actual_text:
        failures.append("버전 헤더가 일치하지 않습니다.")
    for marker in ("# 사실 보존 절대 규칙", "# 맥락 질문 규칙", "# 사용자 출력 형식"):
        if marker not in actual_text:
            failures.append(f"필수 섹션이 없습니다: {marker}")
    missing_sources = [
        relpath.as_posix()
        for relpath in SKILL_RELPATHS
        if f"# SOURCE: {relpath.as_posix()}" not in actual_text
    ]
    failures.extend(f"소스 섹션 누락: {source}" for source in missing_sources)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"OK: 내보내기가 저장소 소스와 일치합니다 (sha256={expected_digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
