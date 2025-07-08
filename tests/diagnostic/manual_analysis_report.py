#!/usr/bin/env python3
"""
Manual Analysis Report Generator

This script generates comprehensive analysis reports from the diagnostic test data
for manual human assessment, replacing the misleading automated scoring.

Usage: python manual_analysis_report.py [test_results_file]
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))


class ManualAnalysisReport:
    """Generate comprehensive manual analysis reports from diagnostic test data."""
    
    def __init__(self, test_results_file: Optional[str] = None):
        self.test_results_file = test_results_file
        self.test_data = {}
        self.analysis_report = {}
        
    def load_test_data(self) -> bool:
        """Load test data from JSON file."""
        if not self.test_results_file:
            # Find most recent test results file
            results_dir = project_root / "tests" / "diagnostic" / "results"
            if results_dir.exists():
                json_files = list(results_dir.glob("*.json"))
                if json_files:
                    self.test_results_file = str(max(json_files, key=os.path.getctime))
        
        if not self.test_results_file or not os.path.exists(self.test_results_file):
            print(f"❌ Test results file not found: {self.test_results_file}")
            return False
            
        try:
            with open(self.test_results_file, 'r') as f:
                self.test_data = json.load(f)
            print(f"✅ Loaded test data from: {self.test_results_file}")
            return True
        except Exception as e:
            print(f"❌ Error loading test data: {e}")
            return False
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive manual analysis report."""
        if not self.test_data:
            return "❌ No test data loaded. Run load_test_data() first."
        
        report_sections = [
            self._generate_header(),
            self._generate_executive_summary(),
            self._generate_citation_analysis(),
            self._generate_answer_quality_analysis(),
            self._generate_performance_analysis(),
            self._generate_system_health_analysis(),
            self._generate_manual_analysis_guide(),
            self._generate_recommendations(),
            self._generate_footer()
        ]
        
        return "\n".join(report_sections)
    
    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
{'=' * 80}
MANUAL ANALYSIS REPORT - RAG SYSTEM DIAGNOSTIC
{'=' * 80}
Generated: {timestamp}
Test Data: {self.test_results_file}
Analysis Mode: MANUAL (Automated scoring disabled due to misleading results)
{'=' * 80}
"""
    
    def _generate_executive_summary(self) -> str:
        """Generate executive summary."""
        return f"""
📋 EXECUTIVE SUMMARY

⚠️  AUTOMATED SCORING DISABLED
The previous automated scoring system was giving misleading results (e.g., 82% 
STAGING_READY) while the system had fundamental failures. This report provides 
raw data for manual human assessment.

🔍 KEY FINDINGS FOR MANUAL REVIEW:
1. Answer Quality: Data collected - manual assessment required
2. Citation Format: Automated detection flags broken citations
3. Performance: Raw metrics show significant issues
4. System Health: Data collection mode - review required

📊 ASSESSMENT APPROACH:
- Review raw answer samples for citation format issues
- Analyze performance metrics against requirements
- Examine system health data for deployment readiness
- Use provided analysis guidelines for consistent evaluation
"""
    
    def _generate_citation_analysis(self) -> str:
        """Generate citation analysis section."""
        citation_section = f"""
🔗 CITATION FORMAT ANALYSIS

⚠️  AUTOMATED DETECTION RESULTS:
The system has been configured to detect common citation format issues:

"""
        
        # Look for citation analysis in test data
        if 'answer_generation' in self.test_data:
            answer_data = self.test_data['answer_generation']
            if 'quality_tests' in answer_data:
                citation_section += "📝 SAMPLE ANSWER ANALYSIS:\n"
                for query, result in answer_data['quality_tests'].items():
                    if 'raw_answer_data' in result:
                        citation_analysis = result['raw_answer_data'].get('citation_analysis', {})
                        if citation_analysis.get('has_broken_citations', False):
                            citation_section += f"  ❌ {query}: BROKEN CITATIONS DETECTED\n"
                        if citation_analysis.get('repetitive_citation_text', False):
                            citation_section += f"  ⚠️  {query}: REPETITIVE CITATION TEXT\n"
        
        citation_section += f"""
🔍 MANUAL REVIEW REQUIRED:
1. Check for "Page unknown from unknown" in answer text
2. Count occurrences of "the documentation" (>5 = issue)
3. Verify proper citation format: [source.pdf, page X]
4. Assess citation relevance and accuracy

📋 CITATION QUALITY CRITERIA:
- ✅ GOOD: [document.pdf, page 5] format
- ⚠️  ACCEPTABLE: Some missing page numbers
- ❌ POOR: "Page unknown from unknown"
- ❌ BROKEN: Repetitive "the documentation" text
"""
        
        return citation_section
    
    def _generate_answer_quality_analysis(self) -> str:
        """Generate answer quality analysis section."""
        quality_section = f"""
📝 ANSWER QUALITY ANALYSIS

⚠️  SCORING DISABLED - MANUAL ASSESSMENT REQUIRED
Previous automated scoring was giving high scores to answers with:
- Broken citation formats
- Repetitive text patterns
- Template-like structure

"""
        
        # Extract answer samples for manual review
        if 'end_to_end_quality' in self.test_data:
            quality_data = self.test_data['end_to_end_quality']
            if 'good_cases' in quality_data:
                quality_section += "📊 GOOD CASES - MANUAL REVIEW SAMPLES:\n"
                for case in quality_data['good_cases'][:3]:  # Show first 3 samples
                    if 'raw_answer_data' in case:
                        answer_text = case['raw_answer_data'].get('answer_text', '')
                        confidence = case['raw_answer_data'].get('confidence', 0)
                        quality_section += f"  Query: {case['query']}\n"
                        quality_section += f"  Confidence: {confidence:.2f}\n"
                        quality_section += f"  Answer Length: {len(answer_text)} chars\n"
                        quality_section += f"  Sample: {answer_text[:200]}...\n\n"
        
        quality_section += f"""
🔍 MANUAL ASSESSMENT CRITERIA:
1. Citation Format: Check for broken citations
2. Content Quality: Assess technical accuracy
3. Answer Structure: Avoid template-like formatting
4. Confidence Calibration: Should match answer quality
5. Completeness: Adequate length and detail

📋 QUALITY RATING SCALE:
- ✅ EXCELLENT: Professional, well-cited, comprehensive
- ⚠️  GOOD: Minor issues, mostly acceptable
- ❌ POOR: Broken citations, repetitive text, template structure
- ❌ UNACCEPTABLE: Fundamental formatting/quality issues
"""
        
        return quality_section
    
    def _generate_performance_analysis(self) -> str:
        """Generate performance analysis section."""
        performance_section = f"""
⚡ PERFORMANCE ANALYSIS

⚠️  SCORING DISABLED - RAW METRICS PROVIDED
Previous performance scoring was misleading. Raw metrics show:

"""
        
        # Extract performance metrics
        if 'system_health' in self.test_data:
            health_data = self.test_data['system_health']
            performance_section += "📊 MEASURED PERFORMANCE:\n"
            
            # Document processing performance
            if 'system_performance_data' in health_data:
                perf_data = health_data['system_performance_data']
                if 'raw_performance_data' in perf_data:
                    raw_data = perf_data['raw_performance_data']
                    doc_rate = raw_data.get('doc_processing_rate', 0)
                    query_time = raw_data.get('query_response_time', 0)
                    throughput = raw_data.get('query_throughput', 0)
                    
                    performance_section += f"  Document Processing: {doc_rate:.0f} chars/sec\n"
                    performance_section += f"  Query Response Time: {query_time:.3f}s\n"
                    performance_section += f"  System Throughput: {throughput:.2f} queries/sec\n"
            
            # Cache performance
            if 'cache_performance' in health_data:
                cache_data = health_data['cache_performance']
                hit_rate = cache_data.get('cache_hit_rate', 0)
                performance_section += f"  Cache Hit Rate: {hit_rate:.1%}\n"
            
            # Memory usage
            if 'memory_usage_efficiency' in health_data:
                memory_eff = health_data['memory_usage_efficiency']
                performance_section += f"  Memory Efficiency: {memory_eff:.1%}\n"
        
        performance_section += f"""
🎯 PERFORMANCE REQUIREMENTS (for manual assessment):
- Document Processing: >1000 chars/sec (production ready)
- Query Response: <2.0s (acceptable for users)
- System Throughput: >0.5 queries/sec (minimum viable)
- Cache Hit Rate: >70% (performance optimization)
- Memory Efficiency: >80% (resource management)

📋 PERFORMANCE RATING:
- ✅ EXCELLENT: Exceeds all requirements
- ⚠️  ACCEPTABLE: Meets minimum requirements
- ❌ POOR: Below minimum requirements
- ❌ UNACCEPTABLE: Significantly below requirements
"""
        
        return performance_section
    
    def _generate_system_health_analysis(self) -> str:
        """Generate system health analysis section."""
        return f"""
🏥 SYSTEM HEALTH ANALYSIS

⚠️  ASSESSMENT DISABLED - DATA COLLECTION MODE
System health scoring was disabled due to misleading results.

🔍 MANUAL HEALTH ASSESSMENT REQUIRED:
1. Component Initialization: Check all components start correctly
2. Error Handling: Verify graceful failure modes
3. Resource Management: Assess memory and CPU usage
4. Deployment Readiness: Validate production suitability

📋 HEALTH CRITERIA:
- ✅ HEALTHY: All components functional, no critical errors
- ⚠️  DEGRADED: Minor issues, mostly functional
- ❌ UNHEALTHY: Multiple failures, unreliable operation
- ❌ CRITICAL: System non-functional, requires immediate attention
"""
    
    def _generate_manual_analysis_guide(self) -> str:
        """Generate manual analysis guide."""
        return f"""
📚 MANUAL ANALYSIS GUIDE

🔍 STEP-BY-STEP ANALYSIS PROCESS:

1. CITATION FORMAT REVIEW (Critical)
   - Search for "Page unknown from unknown" in answer text
   - Count "the documentation" occurrences (>5 = issue)
   - Verify proper [source.pdf, page X] format
   - Rate: PASS/FAIL for citation quality

2. ANSWER QUALITY ASSESSMENT (High Priority)
   - Read sample answers for coherence
   - Check for template structure (1. Primary definition:, etc.)
   - Assess technical accuracy
   - Rate: EXCELLENT/GOOD/POOR/UNACCEPTABLE

3. PERFORMANCE EVALUATION (Medium Priority)
   - Compare metrics against requirements
   - Identify bottlenecks (slow query time, low throughput)
   - Assess user experience impact
   - Rate: EXCELLENT/ACCEPTABLE/POOR/UNACCEPTABLE

4. SYSTEM HEALTH REVIEW (Medium Priority)
   - Check component initialization success
   - Review error logs and failure modes
   - Assess deployment readiness
   - Rate: HEALTHY/DEGRADED/UNHEALTHY/CRITICAL

📊 OVERALL ASSESSMENT FRAMEWORK:
- Portfolio Ready: All categories EXCELLENT/GOOD
- Staging Ready: Most categories GOOD/ACCEPTABLE
- Development Ready: Some categories POOR but functional
- Not Ready: Multiple UNACCEPTABLE/CRITICAL issues
"""
    
    def _generate_recommendations(self) -> str:
        """Generate recommendations section."""
        return f"""
💡 RECOMMENDATIONS

🎯 IMMEDIATE PRIORITIES:
1. Fix citation format issues (critical for credibility)
2. Improve answer quality consistency
3. Optimize performance bottlenecks
4. Implement proper confidence calibration

🔧 TECHNICAL IMPROVEMENTS:
- Replace broken citation system
- Eliminate repetitive text patterns
- Optimize query response times
- Improve cache effectiveness

📋 QUALITY ASSURANCE:
- Implement proper quality gates
- Add performance monitoring
- Create realistic assessment criteria
- Regular manual quality reviews

🚀 PORTFOLIO READINESS:
- Focus on citation format fixes (highest impact)
- Improve answer professionalism
- Ensure consistent performance
- Document all remaining issues clearly
"""
    
    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""
{'=' * 80}
END OF MANUAL ANALYSIS REPORT
{'=' * 80}

📝 NEXT STEPS:
1. Review this report thoroughly
2. Conduct manual assessment using provided criteria
3. Prioritize fixes based on impact and effort
4. Re-run tests after improvements
5. Generate new manual analysis report

⚠️  IMPORTANT: Do not re-enable automated scoring until fundamental 
issues are resolved and proper quality gates are implemented.

Report generated by: Manual Analysis Report Generator
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 80}
"""
    
    def save_report(self, output_file: Optional[str] = None) -> str:
        """Save the analysis report to file."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"manual_analysis_report_{timestamp}.md"
        
        report_content = self.generate_comprehensive_report()
        
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        return output_file


def main():
    """Main function to generate manual analysis report."""
    test_results_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("🔍 Manual Analysis Report Generator")
    print("=" * 50)
    
    # Generate report
    analyzer = ManualAnalysisReport(test_results_file)
    
    if not analyzer.load_test_data():
        print("❌ Failed to load test data")
        return 1
    
    try:
        report_file = analyzer.save_report()
        print(f"✅ Manual analysis report generated: {report_file}")
        
        # Also print to console
        print("\n" + analyzer.generate_comprehensive_report())
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())