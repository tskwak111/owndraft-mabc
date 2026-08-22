"""Export the OwnDraft Timely skill as a single deterministic text artifact.

Order is fixed:
1. SKILL.md
2. pattern_catalog_ko.yaml
3. output_contract.md
4. safety_policy.md
5. SHA-256 digest of the concatenated normalized content

The first 12 characters of the digest become OWNDRAFT_SKILL_VERSION.
"""

import hashlib
import sys
from pathlib import Path

from owndraft.patterns.catalog import find_repo_root

SKILL_RELPATHS = (
    Path("skills/owndraft/SKILL.md"),
    Path("skills/owndraft/references/pattern_catalog_ko.yaml"),
    Path("skills/owndraft/references/output_contract.md"),
    Path("skills/owndraft/references/safety_policy.md"),
)

SECTION_SEPARATOR = "\n\n" + "#" * 78 + "\n\n"


def normalize_content(text: str) -> str:
    """Normalize line endings and trailing whitespace for stable hashing."""

    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def build_export_text(repo_root: Path) -> tuple[str, str]:
    """Return (full export text, normalized-content sha256 hex digest)."""

    sections: list[str] = []
    for relpath in SKILL_RELPATHS:
        path = repo_root / relpath
        if not path.is_file():
            raise FileNotFoundError(f"스킬 원본 파일이 없습니다: {path}")
        sections.append(f"# SOURCE: {relpath.as_posix()}\n\n{normalize_content(path.read_text(encoding='utf-8'))}")

    normalized_concat = SECTION_SEPARATOR.join(sections).strip()
    digest = hashlib.sha256(normalized_concat.encode("utf-8")).hexdigest()
    version = digest[:12]

    header = (
        "OWNDRAFT_SKILL_VERSION: " + version + "\n"
        "GENERATED_FROM_REPOSITORY: true\n"
        "CONTENT_SHA256: " + digest + "\n"
        + "#" * 78
    )
    full_text = header + "\n\n" + normalized_concat + "\n\n" + f"CONTENT_SHA256_EOF: {digest}\n"
    return full_text, digest


def export_skill(output_path: Path, repo_root: Path | None = None) -> str:
    """Write the export artifact and return its content digest."""

    root = repo_root or find_repo_root()
    text, digest = build_export_text(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return digest


def main() -> int:
    root = find_repo_root()
    default_output = root / "artifacts" / "stage1" / "owndraft-timely-skill.txt"
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    digest = export_skill(output, repo_root=root)
    print(f"exported: {output}")
    print(f"content_sha256: {digest}")
    print(f"skill_version: {digest[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
