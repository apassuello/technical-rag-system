"""
Basic smoke tests for system health checks.
"""

def test_python_environment():
    """Test that Python environment is working."""
    import sys
    assert sys.version_info.major >= 3
    assert sys.version_info.minor >= 8

def test_basic_imports():
    """Test that basic dependencies can be imported."""
    try:
        import pytest
        import pathlib
        import yaml
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"

def test_project_structure():
    """Test that project structure exists."""
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    assert (project_root / "src").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "config").exists()