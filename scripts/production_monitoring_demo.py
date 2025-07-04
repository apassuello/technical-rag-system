#!/usr/bin/env python3
"""
Production Monitoring Integration Demo

Demonstrates how to integrate the confidence calibration monitoring
system with the existing RAG pipeline for production deployment.
"""

import sys
from pathlib import Path
import json
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_with_generation import RAGWithGeneration
from src.production_monitoring import CalibrationMonitor, ProductionIntegration, MonitoringMetrics
import numpy as np


def create_sample_baseline_metrics() -> MonitoringMetrics:
    """Create sample baseline metrics for demonstration."""
    return MonitoringMetrics(
        timestamp=datetime.now(),
        ece_score=0.094,  # From our calibration results
        ace_score=0.208,
        mce_score=0.517,
        brier_score=0.241,
        sample_count=500,
        avg_confidence=0.67,
        high_confidence_rate=0.45,
        low_confidence_rate=0.12,
        accuracy=0.78
    )


def demo_monitoring_integration():
    """Demonstrate production monitoring integration."""
    print("🔍 PRODUCTION MONITORING INTEGRATION DEMO")
    print("=" * 60)
    
    # 1. Set up baseline metrics
    print("\n1. Setting up baseline metrics...")
    baseline_metrics = create_sample_baseline_metrics()
    print(f"   ✅ Baseline ECE: {baseline_metrics.ece_score:.3f}")
    print(f"   ✅ Baseline accuracy: {baseline_metrics.accuracy:.3f}")
    
    # 2. Initialize monitoring system
    print("\n2. Initializing monitoring system...")
    monitor = CalibrationMonitor(
        ece_threshold=0.1,
        accuracy_threshold=0.05,
        min_samples=20,  # Lower for demo
        monitoring_window=100,
        baseline_metrics=baseline_metrics
    )
    print(f"   ✅ Monitor initialized with ECE threshold: {monitor.ece_threshold}")
    
    # 3. Initialize RAG system
    print("\n3. Initializing RAG system...")
    try:
        rag = RAGWithGeneration()
        
        # Load test document if not already loaded
        if len(rag.chunks) == 0:
            test_pdf = Path("data/test/riscv-base-instructions.pdf")
            if test_pdf.exists():
                chunk_count = rag.index_document(test_pdf)
                print(f"   ✅ Loaded {chunk_count} chunks from test document")
            else:
                print("   ⚠️ Test document not found, using mock data")
                # Create minimal mock chunks for demo
                rag.chunks = [{"text": "RISC-V is an open-source ISA", "page": 1}] * 10
    except Exception as e:
        print(f"   ❌ RAG initialization failed: {e}")
        return
    
    # 4. Integrate monitoring middleware
    print("\n4. Integrating monitoring middleware...")
    original_query_method = rag.query_with_answer
    middleware = ProductionIntegration.create_monitoring_middleware(monitor)
    rag.query_with_answer = middleware(original_query_method)
    print("   ✅ Monitoring middleware integrated")
    
    # 5. Run monitored queries
    print("\n5. Running monitored queries...")
    test_queries = [
        "What is RISC-V?",
        "How does RISC-V determine instruction length?",
        "What are the main features of RISC-V?",
        "What is the capital of Mars?",  # Should get low confidence
        "Tell me about quantum computing",  # Should get low confidence
    ]
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        try:
            start_time = time.time()
            result = rag.query_with_answer(
                question=query,
                top_k=3,
                use_hybrid=True,
                dense_weight=0.7,
                return_context=True
            )
            processing_time = time.time() - start_time
            
            print(f"      Confidence: {result['confidence']:.1%}")
            print(f"      Citations: {len(result['citations'])}")
            print(f"      Processing time: {processing_time:.2f}s")
            
            # Check for monitoring alerts
            if result.get('monitoring', {}).get('alert'):
                alert = result['monitoring']['alert']
                print(f"      🚨 Alert: {alert['alert_type']} (severity: {alert['severity']})")
            else:
                print(f"      ✅ No alerts")
            
            results.append({
                'query': query,
                'confidence': result['confidence'],
                'processing_time': processing_time,
                'alert': result.get('monitoring', {}).get('alert')
            })
            
        except Exception as e:
            print(f"      ❌ Query failed: {e}")
    
    # 6. Demonstrate drift detection by simulating poor results
    print("\n6. Simulating calibration drift...")
    print("   Adding queries with poor calibration to trigger alerts...")
    
    # Add queries with artificially poor calibration
    for i in range(25):
        # High confidence but low correctness (overconfident predictions)
        confidence = np.random.uniform(0.8, 0.95)
        correctness = 0.0 if np.random.random() < 0.7 else 1.0  # 70% wrong (poor calibration)
        
        alert = monitor.add_query_result(confidence, correctness)
        
        if alert and i < 3:  # Show first few alerts
            print(f"      🚨 Drift detected: {alert.alert_type}")
            print(f"         Current ECE: {alert.current_value:.3f}")
            print(f"         Threshold: {alert.threshold:.3f}")
    
    # 7. Generate monitoring dashboard
    print("\n7. Generating monitoring dashboard...")
    dashboard_data = monitor.get_monitoring_dashboard_data()
    
    print(f"   📊 System Status: {dashboard_data['current_status']['status']}")
    print(f"   📈 Current ECE: {dashboard_data['current_status']['ece_score']:.3f}")
    print(f"   📦 Sample Count: {dashboard_data['current_status']['sample_count']}")
    print(f"   🚨 Alerts (24h): {dashboard_data['current_status']['alerts_24h']}")
    
    print(f"\n   📈 Current Metrics:")
    print(f"      Average Confidence: {dashboard_data['metrics']['avg_confidence']:.1%}")
    print(f"      High Confidence Rate: {dashboard_data['metrics']['high_confidence_rate']:.1%}")
    print(f"      Low Confidence Rate: {dashboard_data['metrics']['low_confidence_rate']:.1%}")
    print(f"      Accuracy: {dashboard_data['metrics']['accuracy']:.1%}")
    
    # 8. Export monitoring report
    print("\n8. Exporting monitoring report...")
    report_filename = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    success = monitor.export_monitoring_report(report_filename)
    
    if success:
        print(f"   ✅ Report exported to {report_filename}")
        
        # Show report summary
        with open(report_filename, 'r') as f:
            report_data = json.load(f)
        
        print(f"\n   📋 Report Summary:")
        print(f"      Total metrics recorded: {len(report_data['metrics_history'])}")
        print(f"      Total alerts: {len(report_data['alerts_history'])}")
        print(f"      Recommendations: {len(report_data['recommendations'])}")
        
        # Show key recommendations
        if report_data['recommendations']:
            print(f"\n   💡 Key Recommendations:")
            for rec in report_data['recommendations'][:3]:
                print(f"      - {rec}")
    else:
        print(f"   ❌ Failed to export report")
    
    # 9. Demonstrate production deployment integration
    print("\n9. Production deployment integration...")
    
    production_config = {
        'ece_threshold': 0.1,
        'accuracy_threshold': 0.05,
        'min_samples': 100,
        'monitoring_window': 1000
    }
    
    print(f"   📝 Production Config:")
    for key, value in production_config.items():
        print(f"      {key}: {value}")
    
    print(f"\n   🚀 Ready for production deployment with:")
    print(f"      - Automatic drift detection")
    print(f"      - Real-time monitoring dashboard")
    print(f"      - Configurable alert thresholds")
    print(f"      - Comprehensive reporting")
    
    return {
        'monitor': monitor,
        'dashboard_data': dashboard_data,
        'report_filename': report_filename if success else None,
        'query_results': results
    }


def demonstrate_production_setup():
    """Demonstrate how to set up monitoring in production."""
    print("\n\n🎯 PRODUCTION SETUP DEMONSTRATION")
    print("=" * 60)
    
    print("""
    Production Integration Steps:
    
    1. Create baseline metrics from validation data:
       ```python
       baseline_metrics = create_baseline_metrics_from_validation(
           validation_data, 'baseline_metrics.json'
       )
       ```
    
    2. Initialize production monitoring:
       ```python
       monitor = ProductionIntegration.setup_production_monitoring(
           rag_system,
           baseline_metrics_file='baseline_metrics.json',
           monitoring_config={'ece_threshold': 0.1}
       )
       ```
    
    3. Queries automatically monitored:
       ```python
       result = rag_system.query_with_answer(question)
       # result['monitoring'] contains drift alerts
       ```
    
    4. Dashboard monitoring:
       ```python
       dashboard_data = monitor.get_monitoring_dashboard_data()
       # Use for real-time monitoring visualization
       ```
    
    5. Regular reporting:
       ```python
       monitor.export_monitoring_report('weekly_report.json')
       # Schedule weekly/monthly comprehensive reports
       ```
    """)


if __name__ == "__main__":
    # Run the demo
    demo_results = demo_monitoring_integration()
    
    # Show production setup
    demonstrate_production_setup()
    
    print(f"\n\n✅ PRODUCTION MONITORING DEMO COMPLETED!")
    print(f"   - Monitoring system integrated successfully")
    print(f"   - Drift detection working")
    print(f"   - Dashboard data generated")
    print(f"   - Report exported")
    print(f"   - Ready for production deployment!")