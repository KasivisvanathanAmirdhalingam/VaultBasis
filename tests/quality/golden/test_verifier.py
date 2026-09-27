import json
from pathlib import Path
import pytest
from edge.receipts.verifier import ReceiptVerifier

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GOLDEN_DIR = WORKSPACE_ROOT / "tests" / "quality" / "golden" / "layer-d-verifier"

def get_verifier_fixtures():
    fixtures = []
    if not GOLDEN_DIR.exists():
        return fixtures
    for fixture_dir in GOLDEN_DIR.iterdir():
        if not fixture_dir.is_dir():
            continue
        
        manifest_path = fixture_dir / "manifest.json"
        expected_path = fixture_dir / "expected.json"
        receipt_path = fixture_dir / "receipt.json"
        
        if not manifest_path.exists() or not expected_path.exists() or not receipt_path.exists():
            continue
            
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        receipt_str = receipt_path.read_text(encoding="utf-8")
        
        fixtures.append({
            "id": manifest["fixture_id"],
            "receipt_str": receipt_str,
            "expected": expected
        })
    return fixtures

@pytest.mark.parametrize("fixture", get_verifier_fixtures(), ids=lambda f: f["id"])
def test_verifier_fixture(fixture):
    receipt_str = fixture["receipt_str"]
    expected = fixture["expected"]
    
    receipt_dict = json.loads(receipt_str)
    result = ReceiptVerifier.verify(receipt_dict)
    
    assert result["overall_status"] == expected["overall_status"], (
        f"Expected {expected['overall_status']} but got {result['overall_status']}"
    )
