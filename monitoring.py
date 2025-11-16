"""
Monitoring and Metrics System for Contextual Document Router
Tracks system performance, health, and usage metrics
"""
import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any, List
from collections import deque
import threading
import json


class SystemMetrics:
    """Collect system-level metrics"""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage statistics"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),  # GB
            'available': memory.available / (1024**3),  # GB
            'used': memory.used / (1024**3),  # GB
            'percent': memory.percent
        }
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage statistics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total / (1024**3),  # GB
            'used': disk.used / (1024**3),  # GB
            'free': disk.free / (1024**3),  # GB
            'percent': disk.percent
        }
    
    @staticmethod
    def get_network_stats() -> Dict[str, int]:
        """Get network I/O statistics"""
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }
    
    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """Get current process information"""
        process = psutil.Process(os.getpid())
        return {
            'pid': process.pid,
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / (1024**2),
            'threads': process.num_threads(),
            'status': process.status()
        }


class ApplicationMetrics:
    """Track application-specific metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.request_times = deque(maxlen=max_history)
        self.error_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.requests_by_format = {}
        self.requests_by_intent = {}
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def record_request(self, duration: float, format: str = None, intent: str = None, success: bool = True):
        """Record a request metric"""
        with self._lock:
            self.request_times.append(duration)
            self.total_requests += 1
            
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
            
            if format:
                self.requests_by_format[format] = self.requests_by_format.get(format, 0) + 1
            
            if intent:
                self.requests_by_intent[intent] = self.requests_by_intent.get(intent, 0) + 1
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.request_times:
            return 0.0
        return sum(self.request_times) / len(self.request_times)
    
    def get_percentile(self, percentile: int) -> float:
        """Get response time percentile"""
        if not self.request_times:
            return 0.0
        sorted_times = sorted(self.request_times)
        index = int(len(sorted_times) * (percentile / 100))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.error_count / self.total_requests) * 100
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100
    
    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time
    
    def get_requests_per_minute(self) -> float:
        """Get average requests per minute"""
        uptime_minutes = self.get_uptime() / 60
        if uptime_minutes == 0:
            return 0.0
        return self.total_requests / uptime_minutes
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        return {
            'total_requests': self.total_requests,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': f"{self.get_success_rate():.2f}%",
            'error_rate': f"{self.get_error_rate():.2f}%",
            'avg_response_time': f"{self.get_average_response_time():.3f}s",
            'p50_response_time': f"{self.get_percentile(50):.3f}s",
            'p95_response_time': f"{self.get_percentile(95):.3f}s",
            'p99_response_time': f"{self.get_percentile(99):.3f}s",
            'uptime_seconds': self.get_uptime(),
            'requests_per_minute': f"{self.get_requests_per_minute():.2f}",
            'requests_by_format': self.requests_by_format,
            'requests_by_intent': self.requests_by_intent
        }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.request_times.clear()
            self.error_count = 0
            self.success_count = 0
            self.total_requests = 0
            self.requests_by_format.clear()
            self.requests_by_intent.clear()
            self.start_time = time.time()


class HealthChecker:
    """Monitor system health"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
    
    def add_check(self, name: str, check_func, threshold: Dict[str, Any] = None):
        """Add a health check"""
        self.checks[name] = {
            'function': check_func,
            'threshold': threshold or {},
            'last_status': None,
            'last_value': None
        }
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        self.last_check_time = datetime.now()
        results = {
            'timestamp': self.last_check_time.isoformat(),
            'checks': {},
            'overall_status': 'healthy'
        }
        
        for name, check in self.checks.items():
            try:
                value = check['function']()
                status = self._evaluate_status(value, check['threshold'])
                
                results['checks'][name] = {
                    'status': status,
                    'value': value
                }
                
                check['last_status'] = status
                check['last_value'] = value
                
                if status == 'unhealthy':
                    results['overall_status'] = 'unhealthy'
                elif status == 'degraded' and results['overall_status'] != 'unhealthy':
                    results['overall_status'] = 'degraded'
                    
            except Exception as e:
                results['checks'][name] = {
                    'status': 'error',
                    'error': str(e)
                }
                results['overall_status'] = 'unhealthy'
        
        return results
    
    def _evaluate_status(self, value: Any, threshold: Dict[str, Any]) -> str:
        """Evaluate health status based on threshold"""
        if not threshold:
            return 'healthy'
        
        if isinstance(value, dict):
            # For complex values, check 'percent' key if available
            value = value.get('percent', 0)
        
        if 'max' in threshold and value > threshold['max']:
            return 'unhealthy'
        elif 'warning' in threshold and value > threshold['warning']:
            return 'degraded'
        
        return 'healthy'
    
    def get_health_status(self) -> str:
        """Get overall health status"""
        results = self.run_checks()
        return results['overall_status']


class MetricsCollector:
    """Centralized metrics collection and reporting"""
    
    def __init__(self):
        self.system_metrics = SystemMetrics()
        self.app_metrics = ApplicationMetrics()
        self.health_checker = HealthChecker()
        self._setup_health_checks()
    
    def _setup_health_checks(self):
        """Setup default health checks"""
        self.health_checker.add_check(
            'cpu_usage',
            self.system_metrics.get_cpu_usage,
            {'warning': 70, 'max': 90}
        )
        self.health_checker.add_check(
            'memory_usage',
            self.system_metrics.get_memory_usage,
            {'warning': 80, 'max': 95}
        )
        self.health_checker.add_check(
            'disk_usage',
            self.system_metrics.get_disk_usage,
            {'warning': 80, 'max': 95}
        )
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu': self.system_metrics.get_cpu_usage(),
                'memory': self.system_metrics.get_memory_usage(),
                'disk': self.system_metrics.get_disk_usage(),
                'network': self.system_metrics.get_network_stats(),
                'process': self.system_metrics.get_process_info()
            },
            'application': self.app_metrics.get_summary(),
            'health': self.health_checker.run_checks()
        }
    
    def export_metrics(self, filepath: str = "metrics.json"):
        """Export metrics to file"""
        metrics = self.collect_all_metrics()
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        return filepath
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = []
        app_summary = self.app_metrics.get_summary()
        
        metrics.append(f"# HELP requests_total Total number of requests")
        metrics.append(f"# TYPE requests_total counter")
        metrics.append(f"requests_total {app_summary['total_requests']}")
        
        metrics.append(f"# HELP requests_success Total number of successful requests")
        metrics.append(f"# TYPE requests_success counter")
        metrics.append(f"requests_success {app_summary['success_count']}")
        
        metrics.append(f"# HELP requests_error Total number of failed requests")
        metrics.append(f"# TYPE requests_error counter")
        metrics.append(f"requests_error {app_summary['error_count']}")
        
        metrics.append(f"# HELP response_time_avg Average response time in seconds")
        metrics.append(f"# TYPE response_time_avg gauge")
        metrics.append(f"response_time_avg {self.app_metrics.get_average_response_time():.6f}")
        
        cpu_usage = self.system_metrics.get_cpu_usage()
        metrics.append(f"# HELP cpu_usage_percent CPU usage percentage")
        metrics.append(f"# TYPE cpu_usage_percent gauge")
        metrics.append(f"cpu_usage_percent {cpu_usage}")
        
        memory = self.system_metrics.get_memory_usage()
        metrics.append(f"# HELP memory_usage_percent Memory usage percentage")
        metrics.append(f"# TYPE memory_usage_percent gauge")
        metrics.append(f"memory_usage_percent {memory['percent']}")
        
        return "\n".join(metrics)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector


if __name__ == "__main__":
    # Test metrics collection
    print("=== Testing Metrics System ===\n")
    
    collector = MetricsCollector()
    
    # Simulate some requests
    for i in range(10):
        duration = 0.1 + (i * 0.05)
        format = ['Email', 'JSON', 'PDF'][i % 3]
        intent = ['Complaint', 'Invoice', 'RFQ'][i % 3]
        success = i % 8 != 0  # 1 failure
        
        collector.app_metrics.record_request(duration, format, intent, success)
    
    # Collect and display metrics
    metrics = collector.collect_all_metrics()
    print(json.dumps(metrics, indent=2))
    
    # Export metrics
    collector.export_metrics("test_metrics.json")
    print("\nMetrics exported to test_metrics.json")
    
    # Show Prometheus format
    print("\n=== Prometheus Format ===")
    print(collector.get_prometheus_format())
