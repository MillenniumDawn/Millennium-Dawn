import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/analysis/targeted_operations_audit.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("targeted_operations_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_audit_creates_pytest_basetemp_parent_on_a_fresh_checkout(monkeypatch):
    audit = load_audit_module()
    test_cache = ROOT / ".pytest_cache"
    test_cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="audit-test-", dir=test_cache) as temporary:
        root = Path(temporary) / "fresh-checkout"
        (root / "tools/tests").mkdir(parents=True)
        calls = []
        monkeypatch.setattr(audit, "ROOT", root)
        monkeypatch.setattr(audit, "run", lambda command: calls.append(command) or 0)

        assert audit.main() == 0
        assert (root / ".pytest_cache").is_dir()
        basetemp = (root / ".pytest_cache/targeted-operations-audit").resolve()
        assert str(basetemp) in calls[1]


def test_audit_passes_root_and_content_suites_to_pytest(monkeypatch):
    audit = load_audit_module()
    test_cache = ROOT / ".pytest_cache"
    test_cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="audit-test-", dir=test_cache) as temporary:
        root = Path(temporary) / "checkout"
        (root / "tools/tests/content").mkdir(parents=True)
        (root / "tools/tests/targeted_operations_model_test.py").touch()
        (root / "tools/tests/content/targeted_operations_core_test.py").touch()
        calls = []
        monkeypatch.setattr(audit, "ROOT", root)
        monkeypatch.setattr(audit, "run", lambda command: calls.append(command) or 0)

        assert audit.main() == 0
        assert "tools/tests/targeted_operations_model_test.py" in calls[1]
        assert "tools/tests/content/targeted_operations_core_test.py" in calls[1]
