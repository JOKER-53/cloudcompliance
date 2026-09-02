import pytest
from cloudcompliance.report import evaluate_controls, load_controls

def test_load_controls():
    controls = load_controls()
    assert "CC6.1" in controls
    assert "CC6.2" in controls
    assert len(controls) == 10

def test_evaluate_controls_all_pass():
    # Mock resources that satisfy all controls
    controls = load_controls()
    mock_resources = []
    
    # Collect all required resource types
    for ctrl in controls.values():
        for res_type in ctrl["resources"]:
            mock_resources.append({"type": res_type, "name": f"mock_{res_type}"})
            
    results = evaluate_controls(mock_resources)
    
    for control_id, result in results.items():
        assert result["status"] == "PASS"

def test_evaluate_controls_partial_fail():
    # Provide only one required resource for CC6.1
    mock_resources = [{"type": "aws_vpc", "name": "mock_vpc"}]
    results = evaluate_controls(mock_resources)
    
    assert results["CC6.1"]["status"] == "PARTIAL"
    assert results["CC6.2"]["status"] == "FAIL"
