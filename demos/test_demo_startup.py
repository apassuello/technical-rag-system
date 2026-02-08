"""
Demo Startup Test

Quick test to verify demo components can be initialized.
Run this before launching the full Streamlit app.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        import streamlit
        print("✅ Streamlit imported")
    except ImportError as e:
        print(f"❌ Failed to import Streamlit: {e}")
        return False

    try:
        import plotly
        print("✅ Plotly imported")
    except ImportError as e:
        print(f"❌ Failed to import Plotly: {e}")
        return False

    try:
        from demos.components_epic2.rag_engine import RAGEngine
        print("✅ RAGEngine imported")
    except ImportError as e:
        print(f"❌ Failed to import RAGEngine: {e}")
        return False

    try:
        from demos.components_epic2.metrics_collector import MetricsCollector
        print("✅ MetricsCollector imported")
    except ImportError as e:
        print(f"❌ Failed to import MetricsCollector: {e}")
        return False

    return True


def test_config_loading():
    """Test that demo config can be loaded."""
    print("\nTesting config loading...")

    try:
        from demos.components_epic2.rag_engine import RAGEngine

        engine = RAGEngine()
        print("✅ RAGEngine instantiated")

        config = engine.config
        print(f"✅ Config loaded: {len(config)} top-level keys")

        return True

    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False


def test_component_initialization():
    """Test that components can be initialized."""
    print("\nTesting component initialization...")

    try:
        from demos.components_epic2.rag_engine import RAGEngine

        engine = RAGEngine()
        print("✅ RAGEngine created")

        success = engine.initialize()

        if success:
            print("✅ RAG Engine initialized successfully")

            # Check health
            health = engine.get_component_health()
            print(f"\nComponent Health:")
            for component, is_healthy in health.items():
                status = "✅" if is_healthy else "❌"
                print(f"  {status} {component}")

            # Get stats
            stats = engine.get_statistics()
            print(f"\nStatistics:")
            print(f"  Total Documents: {stats.get('total_documents', 0)}")
            print(f"  Available Strategies: {stats.get('available_strategies', 0)}")
            print(f"  Indices Loaded: {stats.get('indices_loaded', False)}")

            return True
        else:
            print("❌ RAG Engine initialization failed")
            print("    This is expected if models/indices are not downloaded")
            print("    Run: python scripts/download_models.py && python scripts/build_indices.py")
            return False

    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all startup tests."""
    print("=" * 60)
    print("RAG Demo Startup Test")
    print("=" * 60)

    all_passed = True

    # Test 1: Imports
    if not test_imports():
        all_passed = False
        print("\n⚠️  Some imports failed. Install dependencies:")
        print("    pip install -r requirements.txt")

    # Test 2: Config
    if not test_config_loading():
        all_passed = False

    # Test 3: Initialization
    if not test_component_initialization():
        all_passed = False
        print("\n⚠️  Component initialization failed (expected if data pipeline not run)")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Demo is ready to launch.")
        print("    Run: streamlit run app.py")
    else:
        print("⚠️  Some tests failed. See messages above.")
        print("    The demo may still work with limited functionality.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
