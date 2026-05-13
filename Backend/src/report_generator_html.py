"""
report_generator/html_reporter.py - Generate comprehensive HTML test reports
Includes test results, screenshots, charts, and analytics
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
from jinja2 import Template
from loguru import logger


@dataclass
class TestResult:
    """Test result data class"""
    test_id: str
    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float  # seconds
    message: str = ""
    screenshot_path: Optional[Path] = None
    error_details: Optional[str] = None
    timestamp: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()


class HTMLReporter:
    """Generate comprehensive HTML test reports"""
    
    # HTML Template
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Report - {{ report_title }}</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            header {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            
            header h1 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            
            header p {
                color: #666;
                font-size: 0.95em;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
                border-left: 4px solid #667eea;
            }
            
            .stat-card.passed {
                border-left-color: #28a745;
            }
            
            .stat-card.failed {
                border-left-color: #dc3545;
            }
            
            .stat-card.skipped {
                border-left-color: #ffc107;
            }
            
            .stat-card h3 {
                color: #667eea;
                font-size: 2em;
                margin: 10px 0;
            }
            
            .stat-card.passed h3 {
                color: #28a745;
            }
            
            .stat-card.failed h3 {
                color: #dc3545;
            }
            
            .stat-card p {
                color: #666;
                font-size: 0.9em;
            }
            
            .charts-section {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            
            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
            }
            
            .chart-container {
                text-align: center;
            }
            
            .chart-container img {
                max-width: 100%;
                height: auto;
                border-radius: 4px;
            }
            
            .tests-section {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            
            .tests-section h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            thead {
                background: #f8f9fa;
                border-bottom: 2px solid #667eea;
            }
            
            th {
                padding: 15px;
                text-align: left;
                color: #333;
                font-weight: 600;
            }
            
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e9ecef;
            }
            
            tr:hover {
                background: #f8f9fa;
            }
            
            .badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.85em;
                font-weight: 600;
            }
            
            .badge.passed {
                background: #d4edda;
                color: #155724;
            }
            
            .badge.failed {
                background: #f8d7da;
                color: #721c24;
            }
            
            .badge.skipped {
                background: #fff3cd;
                color: #856404;
            }
            
            .badge.error {
                background: #f8d7da;
                color: #721c24;
            }
            
            .screenshot {
                max-width: 100%;
                height: auto;
                border-radius: 4px;
                margin: 10px 0;
            }
            
            .test-row-details {
                display: none;
            }
            
            .test-row-details.show {
                display: table-row;
                background: #f8f9fa;
            }
            
            .test-row-details td {
                padding: 20px;
            }
            
            .error-message {
                background: #fff3cd;
                padding: 15px;
                border-left: 4px solid #ffc107;
                border-radius: 4px;
                margin: 10px 0;
                color: #856404;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                max-height: 200px;
                overflow-y: auto;
            }
            
            footer {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                color: #666;
                margin-top: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .expandable-row {
                cursor: pointer;
            }
            
            .expandable-row:hover {
                background: #e9ecef;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .charts-grid {
                    grid-template-columns: 1fr;
                }
                
                header h1 {
                    font-size: 1.5em;
                }
                
                table {
                    font-size: 0.9em;
                }
                
                th, td {
                    padding: 8px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🧪 Test Report</h1>
                <p><strong>{{ report_title }}</strong></p>
                <p>Generated: {{ generated_at }}</p>
            </header>
            
            <div class="stats-grid">
                <div class="stat-card passed">
                    <p>✅ Passed</p>
                    <h3>{{ stats.passed }}</h3>
                    <p>{{ stats.passed_percent }}%</p>
                </div>
                <div class="stat-card failed">
                    <p>❌ Failed</p>
                    <h3>{{ stats.failed }}</h3>
                    <p>{{ stats.failed_percent }}%</p>
                </div>
                <div class="stat-card skipped">
                    <p>⏭️ Skipped</p>
                    <h3>{{ stats.skipped }}</h3>
                    <p>{{ stats.skipped_percent }}%</p>
                </div>
                <div class="stat-card">
                    <p>⏱️ Duration</p>
                    <h3>{{ stats.total_duration }}s</h3>
                    <p>Total execution time</p>
                </div>
            </div>
            
            {% if charts %}
            <div class="charts-section">
                <h2>📊 Charts & Analytics</h2>
                <div class="charts-grid">
                    {% for chart in charts %}
                    <div class="chart-container">
                        <img src="{{ chart }}" alt="Chart">
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
            
            <div class="tests-section">
                <h2>📋 Test Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Test ID</th>
                            <th>Test Name</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Tags</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for test in tests %}
                        <tr class="expandable-row" onclick="toggleDetails(this)">
                            <td>{{ test.test_id }}</td>
                            <td>{{ test.test_name }}</td>
                            <td><span class="badge {{ test.status }}">{{ test.status|upper }}</span></td>
                            <td>{{ test.duration }}s</td>
                            <td>
                                {% for tag in test.tags %}
                                <span class="badge">{{ tag }}</span>
                                {% endfor %}
                            </td>
                        </tr>
                        {% if test.screenshot_path or test.error_details %}
                        <tr class="test-row-details">
                            <td colspan="5">
                                {% if test.screenshot_path %}
                                <div>
                                    <p><strong>Screenshot:</strong></p>
                                    <img src="{{ test.screenshot_path }}" alt="Test Screenshot" class="screenshot">
                                </div>
                                {% endif %}
                                {% if test.error_details %}
                                <div class="error-message">
                                    <strong>Error Details:</strong><br>
                                    {{ test.error_details }}
                                </div>
                                {% endif %}
                            </td>
                        </tr>
                        {% endif %}
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <footer>
                <p>Generated by AI Testing System | Version 1.0.0</p>
                <p><small>Total Tests: {{ stats.total }} | Pass Rate: {{ stats.passed_percent }}%</small></p>
            </footer>
        </div>
        
        <script>
            function toggleDetails(row) {
                const nextRow = row.nextElementSibling;
                if (nextRow && nextRow.classList.contains('test-row-details')) {
                    nextRow.classList.toggle('show');
                }
            }
        </script>
    </body>
    </html>
    """
    
    def __init__(self, output_path: Path = Path("reports/html")):
        """
        Initialize HTML reporter
        
        Args:
            output_path: Path to save HTML reports
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized HTMLReporter at {output_path}")
    
    def generate(
        self,
        test_results: List[TestResult],
        report_title: str = "Test Execution Report",
        include_charts: bool = True
    ) -> Path:
        """
        Generate HTML report
        
        Args:
            test_results: List of TestResult objects
            report_title: Title for the report
            include_charts: Generate and include charts
            
        Returns:
            Path to generated report
        """
        logger.info(f"Generating HTML report with {len(test_results)} tests")
        
        # Calculate statistics
        stats = self._calculate_stats(test_results)
        
        # Generate charts
        charts = []
        if include_charts:
            charts = self._generate_charts(test_results)
        
        # Prepare template data
        template_data = {
            "report_title": report_title,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stats": stats,
            "tests": [self._prepare_test_data(test) for test in test_results],
            "charts": charts
        }
        
        # Render template
        template = Template(self.HTML_TEMPLATE)
        html_content = template.render(template_data)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_path / f"test_report_{timestamp}.html"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to {report_path}")
        return report_path
    
    def _calculate_stats(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Calculate test statistics"""
        
        total = len(test_results)
        passed = sum(1 for t in test_results if t.status == "passed")
        failed = sum(1 for t in test_results if t.status == "failed")
        skipped = sum(1 for t in test_results if t.status == "skipped")
        
        total_duration = sum(t.duration for t in test_results)
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "passed_percent": round((passed / total * 100) if total > 0 else 0, 2),
            "failed_percent": round((failed / total * 100) if total > 0 else 0, 2),
            "skipped_percent": round((skipped / total * 100) if total > 0 else 0, 2),
            "total_duration": round(total_duration, 2)
        }
    
    def _generate_charts(self, test_results: List[TestResult]) -> List[str]:
        """Generate and save charts"""
        
        charts = []
        
        # Chart 1: Test Results Distribution
        status_counts = {
            "passed": sum(1 for t in test_results if t.status == "passed"),
            "failed": sum(1 for t in test_results if t.status == "failed"),
            "skipped": sum(1 for t in test_results if t.status == "skipped")
        }
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#28a745', '#dc3545', '#ffc107']
        ax.pie(
            status_counts.values(),
            labels=status_counts.keys(),
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        ax.set_title('Test Results Distribution', fontsize=16, fontweight='bold')
        
        chart_path = self.output_path / f"chart_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        charts.append(str(chart_path))
        
        # Chart 2: Test Duration Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        durations = [t.duration for t in test_results]
        test_names = [t.test_name[:20] + "..." if len(t.test_name) > 20 else t.test_name for t in test_results]
        
        bars = ax.barh(test_names, durations, color=['#28a745' if test_results[i].status == 'passed' else '#dc3545' for i in range(len(test_results))])
        ax.set_xlabel('Duration (seconds)', fontweight='bold')
        ax.set_title('Test Duration by Test', fontsize=16, fontweight='bold')
        ax.invert_yaxis()
        
        chart_path = self.output_path / f"chart_duration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_path, dpi=100, bbox_inches='tight')
        plt.close()
        charts.append(str(chart_path))
        
        return charts
    
    def _prepare_test_data(self, test: TestResult) -> Dict[str, Any]:
        """Prepare test data for template"""
        
        return {
            "test_id": test.test_id,
            "test_name": test.test_name,
            "status": test.status,
            "duration": round(test.duration, 3),
            "message": test.message,
            "screenshot_path": str(test.screenshot_path) if test.screenshot_path else None,
            "error_details": test.error_details,
            "tags": test.tags
        }


# Example usage
if __name__ == "__main__":
    # Create sample test results
    results = [
        TestResult(
            test_id="TC_001",
            test_name="Login with valid credentials",
            status="passed",
            duration=2.5,
            tags=["login", "functional"]
        ),
        TestResult(
            test_id="TC_002",
            test_name="Login with invalid credentials",
            status="failed",
            duration=3.2,
            error_details="Expected: 'Invalid credentials' message\nActual: No error message shown",
            tags=["login", "negative"]
        ),
    ]
    
    # Generate report
    reporter = HTMLReporter()
    report_path = reporter.generate(results, "Sample Test Report")
    print(f"Report generated: {report_path}")
