"""Release workflow input normalization is checked using its actual Bash step."""
import os
from pathlib import Path
import subprocess
import textwrap

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"


def _normalizer():
    content = WORKFLOW.read_text()
    first = content.split("      - name: Normalize and validate release tag input\n", 1)[1]
    section = first.split("      - name: Check out exactly the published release tag\n", 1)[0]
    assert "id: release_tag" in section
    return textwrap.dedent(section.split("        run: |\n", 1)[1])


def _check_tag(raw, tmp_path):
    output = tmp_path / "github_output.txt"
    env = dict(os.environ, RAW_RELEASE_TAG=raw, GITHUB_OUTPUT=str(output))
    result = subprocess.run(["bash", "-e", "-c", _normalizer()],
                            env=env, capture_output=True, text=True, timeout=5)
    value = output.read_text() if output.exists() else ""
    return result, value


def test_manual_release_tag_trailing_whitespace_is_removed(tmp_path):
    result, value = _check_tag("  v0.2.1  \n", tmp_path)
    assert result.returncode == 0, result.stderr
    assert value == "value=v0.2.1\n"


def test_valid_future_release_tags_are_supported(tmp_path):
    result, value = _check_tag("v12.34.567", tmp_path)
    assert result.returncode == 0
    assert value == "value=v12.34.567\n"


def test_invalid_and_injected_tags_fail_closed(tmp_path):
    for bad in ("main", "v0.2.1;echo dangerous", "v0.2", "v0.2.1-rc1", "", "v0.2.1 evil"):
        result, value = _check_tag(bad, tmp_path)
        assert result.returncode != 0, bad
        assert not value, bad


def test_all_release_actions_use_normalized_tag():
    content = WORKFLOW.read_text()
    normalized = "${{ steps.release_tag.outputs.value }}"
    assert content.count(normalized) == 3
    assert "ref: " + normalized in content
    assert content.index("Normalize and validate release tag input") < content.index("Check out exactly the published release tag")
