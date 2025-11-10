#!/usr/bin/env python3
"""
Generate Coverage Monitoring Dashboard
Creates an HTML dashboard for monitoring test coverage across the project.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def load_coverage_data(json_file: Path) -> Dict:
    """Load coverage data from JSON file."""
    with open(json_file) as f:
        return json.load(f)

def analyze_coverage_by_module(coverage_data: Dict) -> List[Tuple[str, float, int]]:
    """Analyze coverage data grouped by module."""
    files = coverage_data.get('files', {})
    modules = {}
    
    for file_path, file_data in files.items():
        if file_path.startswith('src/'):
            summary = file_data.get('summary', {})
            percent = summary.get('percent_covered', 0)
            lines = summary.get('num_statements', 0)
            
            # Extract module name
            parts = file_path.replace('src/', '').split('/')
            if len(parts) >= 2:
                module = f'{parts[0]}.{parts[1]}'
            else:
                module = parts[0]
            
            if module not in modules:
                modules[module] = {'total_lines': 0, 'covered_lines': 0, 'files': []}
            
            modules[module]['total_lines'] += lines
            modules[module]['covered_lines'] += int(lines * percent / 100)
            modules[module]['files'].append({
                'path': file_path,
                'coverage': percent,
                'lines': lines
            })
    
    # Calculate module coverage
    result = []
    for module, data in modules.items():
        if data['total_lines'] > 0:
            percent = (data['covered_lines'] / data['total_lines']) * 100
            result.append((module, percent, data['total_lines']))
    
    return sorted(result, key=lambda x: x[1], reverse=True)

def get_coverage_color(percentage: float) -> str:
    """Get color class based on coverage percentage."""
    if percentage >= 90:
        return "coverage-excellent"
    elif percentage >= 75:
        return "coverage-good"
    elif percentage >= 50:
        return "coverage-fair"
    elif percentage >= 25:
        return "coverage-poor"
    else:
        return "coverage-critical"

def generate_html_dashboard(coverage_data: Dict, output_file: Path, 
                          baseline_data: Dict = None) -> None:
    """Generate HTML coverage dashboard."""
    
    # Extract summary data
    summary = coverage_data.get('totals', {})
    total_coverage = summary.get('percent_covered', 0)
    total_lines = summary.get('num_statements', 0)
    covered_lines = summary.get('covered_lines', 0)
    
    # Analyze modules
    module_coverage = analyze_coverage_by_module(coverage_data)
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Portfolio - Coverage Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f7;
            color: #1d1d1f;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .modules-section {{
            padding: 30px;
        }}
        
        .section-title {{
            font-size: 1.5em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1d1d1f;
        }}
        
        .module-list {{
            display: grid;
            gap: 12px;
        }}
        
        .module-item {{
            display: flex;
            align-items: center;
            padding: 15px;
            background: #fafafa;
            border-radius: 8px;
            border-left: 4px solid #ddd;
        }}
        
        .module-name {{
            flex: 1;
            font-weight: 500;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.9em;
        }}
        
        .coverage-bar {{
            width: 120px;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            margin: 0 15px;
            overflow: hidden;
        }}
        
        .coverage-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .coverage-percent {{
            font-weight: 600;
            min-width: 50px;
            text-align: right;
        }}
        
        .coverage-lines {{
            font-size: 0.8em;
            color: #666;
            min-width: 70px;
            text-align: right;
        }}
        
        .coverage-excellent {{ background-color: #28a745; }}
        .coverage-good {{ background-color: #20c997; }}
        .coverage-fair {{ background-color: #ffc107; }}
        .coverage-poor {{ background-color: #fd7e14; }}
        .coverage-critical {{ background-color: #dc3545; }}
        
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
            text-align: center;
        }}
        
        .recommendations {{
            padding: 30px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        
        .rec-item {{
            background: white;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #17a2b8;
        }}
        
        .rec-priority {{
            font-weight: 600;
            color: #17a2b8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Coverage Dashboard</h1>
            <div class="subtitle">RAG Portfolio Project • Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_coverage:.1f}%</div>
                <div class="stat-label">Overall Coverage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_lines:,}</div>
                <div class="stat-label">Total Lines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{covered_lines:,}</div>
                <div class="stat-label">Covered Lines</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(module_coverage)}</div>
                <div class="stat-label">Modules</div>
            </div>
        </div>
        
        <div class="modules-section">
            <h2 class="section-title">Coverage by Module</h2>
            <div class="module-list">
"""
    
    # Add module coverage items
    for module, coverage, lines in module_coverage:
        color_class = get_coverage_color(coverage)
        html_content += f"""
                <div class="module-item">
                    <div class="module-name">{module}</div>
                    <div class="coverage-bar">
                        <div class="coverage-fill {color_class}" style="width: {coverage:.1f}%"></div>
                    </div>
                    <div class="coverage-percent">{coverage:.1f}%</div>
                    <div class="coverage-lines">{lines:,} lines</div>
                </div>
"""
    
    # Add recommendations
    html_content += """
            </div>
        </div>
        
        <div class="recommendations">
            <h2 class="section-title">💡 Coverage Improvement Recommendations</h2>
"""
    
    # Generate recommendations based on coverage data
    recommendations = []
    
    for module, coverage, lines in module_coverage[:5]:  # Top 5 modules by lines
        if coverage < 50 and lines > 100:
            priority = "HIGH" if coverage < 25 else "MEDIUM"
            recommendations.append((priority, f"Add unit tests for {module} ({coverage:.1f}% coverage, {lines:,} lines)"))
    
    if total_coverage < 70:
        recommendations.insert(0, ("CRITICAL", f"Overall coverage ({total_coverage:.1f}%) is below recommended 70% threshold"))
    
    if not recommendations:
        recommendations.append(("LOW", "Coverage levels are good! Consider adding integration tests to improve overall quality."))
    
    for priority, recommendation in recommendations[:6]:  # Show top 6 recommendations
        html_content += f"""
            <div class="rec-item">
                <span class="rec-priority">{priority} PRIORITY:</span> {recommendation}
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • 
            RAG Portfolio Project Coverage Dashboard • 
            <strong>Target: 70%+ Overall Coverage</strong>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    output_file.write_text(html_content)
    print(f"📊 Coverage dashboard generated: {output_file}")

def main():
    """Main function to generate coverage dashboard."""
    parser = argparse.ArgumentParser(description='Generate coverage monitoring dashboard')
    parser.add_argument('coverage_file', help='Path to coverage JSON file')
    parser.add_argument('-o', '--output', default='reports/coverage/dashboard.html', 
                       help='Output HTML file path')
    parser.add_argument('-b', '--baseline', help='Baseline coverage file for comparison')
    
    args = parser.parse_args()
    
    # Load coverage data
    coverage_file = Path(args.coverage_file)
    if not coverage_file.exists():
        print(f"❌ Coverage file not found: {coverage_file}")
        return 1
    
    coverage_data = load_coverage_data(coverage_file)
    
    # Load baseline data if provided
    baseline_data = None
    if args.baseline:
        baseline_file = Path(args.baseline)
        if baseline_file.exists():
            baseline_data = load_coverage_data(baseline_file)
    
    # Generate dashboard
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    generate_html_dashboard(coverage_data, output_file, baseline_data)
    
    return 0

if __name__ == '__main__':
    exit(main())