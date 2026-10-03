import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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
