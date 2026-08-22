"""Loading and validation of the Korean pattern catalog."""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from owndraft.core.errors import ContractError

CATALOG_RELPATH = Path("skills/owndraft/references/pattern_catalog_ko.yaml")
EXPECTED_RULE_COUNT = 40


class PatternRule(BaseModel):
    code: str
    category: str
    description_ko: str
    severity: str = Field(pattern="^(low|medium|high)$")
    default_action: str = Field(pattern="^(keep|rewrite|delete|ask)$")
    regexes: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    exemptions: list[str] = Field(default_factory=list)


def find_repo_root() -> Path:
    """Walk up from CWD (or env override) to locate the repository root."""
    override = os.getenv("OWNDRAFT_REPO_ROOT")
    if override:
        return Path(override).resolve()
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "apps" / "api").is_dir() and (candidate / "skills").is_dir():
            return candidate
    raise ContractError(
        "owndraft_repo_root_not_found",
        detail="저장소 루트를 찾지 못했습니다. OWNDRAFT_REPO_ROOT 환경변수로 지정하세요.",
    )


def catalog_path() -> Path:
    return find_repo_root() / CATALOG_RELPATH


def load_pattern_catalog() -> list[PatternRule]:
    """Load and validate all 40 pattern rules from the YAML catalog."""
    path = catalog_path()
    if not path.is_file():
        raise ContractError(
            "pattern_catalog_missing",
            detail=f"패턴 카탈로그 파일이 없습니다: {path}",
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ContractError("pattern_catalog_invalid", detail="카탈로그는 리스트여야 합니다.")
    rules = [PatternRule.model_validate(entry) for entry in raw]
    if len(rules) != EXPECTED_RULE_COUNT:
        raise ContractError(
            "pattern_catalog_wrong_size",
            detail=f"패턴 규칙은 정확히 {EXPECTED_RULE_COUNT}개여야 합니다: {len(rules)}",
        )
    codes = [rule.code for rule in rules]
    if len(set(codes)) != len(codes):
        raise ContractError("pattern_catalog_duplicate_code", detail="중복된 패턴 코드가 있습니다.")
    return rules
