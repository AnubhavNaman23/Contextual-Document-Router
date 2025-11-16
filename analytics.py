"""
Advanced Analytics Module for Multi-Format AI System
Provides comprehensive analytics, reporting, and insights
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import os


class AnalyticsEngine:
    """Main analytics engine for processing insights"""
    
    def __init__(self, memory_file: str = "shared_memory.json"):
        self.memory_file = memory_file
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load data from shared memory"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
                return memory.get('results', [])
        return []
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get overall summary statistics"""
        if not self.data:
            return {}
        
        df = pd.DataFrame(self.data)
        
        stats = {
            'total_documents': len(df),
            'unique_agents': df['agent'].nunique() if 'agent' in df else 0,
            'date_range': {
                'start': df['timestamp'].min() if 'timestamp' in df else None,
                'end': df['timestamp'].max() if 'timestamp' in df else None
            },
            'processing_summary': self._get_processing_summary(df)
        }
        
        return stats
    
    def _get_processing_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get processing summary from dataframe"""
        summary = {
            'by_format': {},
            'by_intent': {},
            'by_agent': {},
            'avg_confidence': 0
        }
        
        # Extract format data
        if 'input_meta' in df:
            formats = [item.get('format', 'Unknown') for item in df['input_meta']]
            summary['by_format'] = dict(Counter(formats))
        
        # Extract intent data
        if 'extracted' in df:
            intents = [item.get('intent', 'Unknown') for item in df['extracted'] if item]
            summary['by_intent'] = dict(Counter(intents))
            
            # Calculate average confidence
            confidences = [item.get('confidence', 0) for item in df['extracted'] if item and item.get('confidence')]
            if confidences:
                summary['avg_confidence'] = np.mean(confidences)
        
        # Count by agent
        if 'agent' in df:
            summary['by_agent'] = dict(Counter(df['agent']))
        
        return summary
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """Get distribution of intents"""
        intents = []
        for item in self.data:
            extracted = item.get('extracted', {})
            if extracted:
                intent = extracted.get('intent', 'Unknown')
                intents.append(intent)
        
        return dict(Counter(intents))
    
    def get_format_distribution(self) -> Dict[str, int]:
        """Get distribution of document formats"""
        formats = []
        for item in self.data:
            input_meta = item.get('input_meta', {})
            fmt = input_meta.get('format', 'Unknown')
            formats.append(fmt)
        
        return dict(Counter(formats))
    
    def get_confidence_statistics(self) -> Dict[str, float]:
        """Get confidence score statistics"""
        confidences = []
        for item in self.data:
            extracted = item.get('extracted', {})
            if extracted and 'confidence' in extracted:
                confidences.append(float(extracted['confidence']))
        
        if not confidences:
            return {}
        
        return {
            'mean': np.mean(confidences),
            'median': np.median(confidences),
            'std': np.std(confidences),
            'min': np.min(confidences),
            'max': np.max(confidences),
            'percentile_25': np.percentile(confidences, 25),
            'percentile_75': np.percentile(confidences, 75)
        }
    
    def get_processing_trend(self, days: int = 7) -> Dict[str, List]:
        """Get processing trend over time"""
        if not self.data:
            return {}
        
        # Parse timestamps
        timestamps = []
        for item in self.data:
            ts = item.get('timestamp')
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                except:
                    continue
        
        if not timestamps:
            return {}
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Count documents per day
        date_counts = defaultdict(int)
        for ts in timestamps:
            if start_date <= ts <= end_date:
                date_key = ts.strftime('%Y-%m-%d')
                date_counts[date_key] += 1
        
        # Fill missing dates
        current_date = start_date
        trend_data = {'dates': [], 'counts': []}
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            trend_data['dates'].append(date_key)
            trend_data['counts'].append(date_counts[date_key])
            current_date += timedelta(days=1)
        
        return trend_data
    
    def get_agent_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by agent"""
        agent_data = defaultdict(lambda: {
            'total_processed': 0,
            'avg_confidence': 0,
            'confidences': [],
            'intents': []
        })
        
        for item in self.data:
            agent = item.get('agent', 'Unknown')
            agent_data[agent]['total_processed'] += 1
            
            extracted = item.get('extracted', {})
            if extracted:
                if 'confidence' in extracted:
                    agent_data[agent]['confidences'].append(float(extracted['confidence']))
                if 'intent' in extracted:
                    agent_data[agent]['intents'].append(extracted['intent'])
        
        # Calculate averages
        for agent, data in agent_data.items():
            if data['confidences']:
                data['avg_confidence'] = np.mean(data['confidences'])
            data['intent_distribution'] = dict(Counter(data['intents']))
            # Clean up temporary lists
            del data['confidences']
            del data['intents']
        
        return dict(agent_data)
    
    def get_top_intents(self, limit: int = 5) -> List[Tuple[str, int]]:
        """Get top N intents by frequency"""
        intent_dist = self.get_intent_distribution()
        return sorted(intent_dist.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_low_confidence_documents(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Get documents with confidence below threshold"""
        low_confidence = []
        
        for item in self.data:
            extracted = item.get('extracted', {})
            if extracted and 'confidence' in extracted:
                confidence = float(extracted['confidence'])
                if confidence < threshold:
                    low_confidence.append({
                        'timestamp': item.get('timestamp'),
                        'agent': item.get('agent'),
                        'intent': extracted.get('intent'),
                        'confidence': confidence,
                        'source': item.get('input_meta', {}).get('source')
                    })
        
        return sorted(low_confidence, key=lambda x: x['confidence'])
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Analyze errors and failures"""
        errors = {
            'total_errors': 0,
            'error_types': {},
            'failed_formats': {},
            'error_timeline': []
        }
        
        for item in self.data:
            actions = item.get('actions', [])
            for action in actions:
                if isinstance(action, str) and ('error' in action.lower() or 'failed' in action.lower()):
                    errors['total_errors'] += 1
                    errors['error_timeline'].append({
                        'timestamp': item.get('timestamp'),
                        'error': action
                    })
        
        return errors
    
    def generate_report(self, output_format: str = 'json') -> str:
        """Generate comprehensive analytics report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_summary_statistics(),
            'intent_distribution': self.get_intent_distribution(),
            'format_distribution': self.get_format_distribution(),
            'confidence_stats': self.get_confidence_statistics(),
            'agent_performance': self.get_agent_performance(),
            'top_intents': self.get_top_intents(),
            'low_confidence_docs': self.get_low_confidence_documents(),
            'error_analysis': self.get_error_analysis()
        }
        
        if output_format == 'json':
            return json.dumps(report, indent=2)
        elif output_format == 'dict':
            return report
        else:
            return str(report)
    
    def export_to_csv(self, output_file: str = "analytics_export.csv"):
        """Export analytics data to CSV"""
        if not self.data:
            return False
        
        # Flatten data for CSV
        rows = []
        for item in self.data:
            row = {
                'timestamp': item.get('timestamp'),
                'agent': item.get('agent'),
                'format': item.get('input_meta', {}).get('format'),
                'intent': item.get('extracted', {}).get('intent'),
                'confidence': item.get('extracted', {}).get('confidence'),
                'source': item.get('input_meta', {}).get('source')
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        return True


class ReportGenerator:
    """Generate formatted reports from analytics"""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.engine = analytics_engine
    
    def generate_text_report(self) -> str:
        """Generate a text-based report"""
        report = []
        report.append("=" * 80)
        report.append("MULTI-FORMAT AI SYSTEM - ANALYTICS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        summary = self.engine.get_summary_statistics()
        report.append("SUMMARY STATISTICS")
        report.append("-" * 80)
        report.append(f"Total Documents Processed: {summary.get('total_documents', 0)}")
        report.append(f"Unique Agents: {summary.get('unique_agents', 0)}")
        report.append("")
        
        # Intent Distribution
        intent_dist = self.engine.get_intent_distribution()
        if intent_dist:
            report.append("INTENT DISTRIBUTION")
            report.append("-" * 80)
            for intent, count in sorted(intent_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary.get('total_documents', 1)) * 100
                report.append(f"{intent:20s}: {count:5d} ({percentage:5.1f}%)")
            report.append("")
        
        # Format Distribution
        format_dist = self.engine.get_format_distribution()
        if format_dist:
            report.append("FORMAT DISTRIBUTION")
            report.append("-" * 80)
            for fmt, count in sorted(format_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary.get('total_documents', 1)) * 100
                report.append(f"{fmt:20s}: {count:5d} ({percentage:5.1f}%)")
            report.append("")
        
        # Confidence Statistics
        conf_stats = self.engine.get_confidence_statistics()
        if conf_stats:
            report.append("CONFIDENCE STATISTICS")
            report.append("-" * 80)
            report.append(f"Mean:       {conf_stats.get('mean', 0):.4f}")
            report.append(f"Median:     {conf_stats.get('median', 0):.4f}")
            report.append(f"Std Dev:    {conf_stats.get('std', 0):.4f}")
            report.append(f"Min:        {conf_stats.get('min', 0):.4f}")
            report.append(f"Max:        {conf_stats.get('max', 0):.4f}")
            report.append("")
        
        # Agent Performance
        agent_perf = self.engine.get_agent_performance()
        if agent_perf:
            report.append("AGENT PERFORMANCE")
            report.append("-" * 80)
            for agent, metrics in agent_perf.items():
                report.append(f"{agent}:")
                report.append(f"  Total Processed: {metrics['total_processed']}")
                report.append(f"  Avg Confidence:  {metrics['avg_confidence']:.4f}")
                report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_html_report(self) -> str:
        """Generate an HTML report"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analytics Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .metric { background-color: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2980b9; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #3498db; color: white; }
                tr:hover { background-color: #f5f5f5; }
                .footer { text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Multi-Format AI System - Analytics Report</h1>
                <p><strong>Generated:</strong> {timestamp}</p>
                
                <h2>Summary Statistics</h2>
                <div class="metric">
                    <div>Total Documents Processed</div>
                    <div class="metric-value">{total_docs}</div>
                </div>
                
                <!-- Additional content would be dynamically generated here -->
                
                <div class="footer">
                    <p>Multi-Format Autonomous AI System v2.0</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        summary = self.engine.get_summary_statistics()
        html = html.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_docs=summary.get('total_documents', 0)
        )
        
        return html


if __name__ == "__main__":
    # Test analytics
    print("=== Testing Analytics Engine ===\n")
    
    engine = AnalyticsEngine()
    print(f"Loaded {len(engine.data)} records")
    
    # Generate report
    report = engine.generate_report(output_format='dict')
    print("\nSummary Statistics:")
    print(json.dumps(report['summary'], indent=2))
    
    # Generate text report
    reporter = ReportGenerator(engine)
    text_report = reporter.generate_text_report()
    print("\n" + text_report)
