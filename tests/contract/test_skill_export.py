from pathlib import Path

from scripts.export_timely_skill import export_skill


def test_export_contains_required_sections_and_version_hash(tmp_path: Path):
    output = tmp_path / "skill.txt"
    digest = export_skill(output)
    text = output.read_text(encoding="utf-8")

    assert "OWNDRAFT_SKILL_VERSION:" in text
    assert digest in text
    assert "GENERATED_FROM_REPOSITORY: true" in text
    assert "# 사실 보존 절대 규칙" in text
    assert "# 맥락 질문 규칙" in text
    assert "# 사용자 출력 형식" in text
    assert "워터마크 제거" in text
    assert "보장하지 않는다" in text


def test_export_is_deterministic(tmp_path: Path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"

    digest_first = export_skill(first)
    digest_second = export_skill(second)

    assert digest_first == digest_second
    assert first.read_bytes() == second.read_bytes()


def test_export_includes_pattern_catalog_codes(tmp_path: Path):
    output = tmp_path / "skill.txt"
    export_skill(output)
    text = output.read_text(encoding="utf-8")

    assert "era_background_intro" in text
    assert "chatbot_greeting_closing" in text


def test_verify_script_accepts_fresh_export(tmp_path: Path, capsys):
    import os
    import subprocess
    import sys

    output = tmp_path / "skill.txt"
    export_skill(output)

    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["OWNDRAFT_REPO_ROOT"] = str(repo_root)
    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "verify_timely_export.py"),
            str(output),
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
