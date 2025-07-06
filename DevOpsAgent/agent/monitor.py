
import time
import logging
from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import json

class SystemMonitor:
    def __init__(self, prometheus_url="http://localhost:9090"):
        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0
        self.network_threshold = 1000000  # 1MB/s
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage"""
        try:
            query = 'round((1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100, 2)'
            result = self.prom.custom_query(query=query)
            if result:
                return float(result[0]['value'][1])
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    def get_memory_usage(self):
        """Get current memory usage percentage"""
        try:
            query = 'round((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100, 2)'
            result = self.prom.custom_query(query=query)
            if result:
                return float(result[0]['value'][1])
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return 0.0
    
    def get_disk_usage(self):
        """Get current disk usage percentage"""
        try:
            query = 'round((1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100, 2)'
            result = self.prom.custom_query(query=query)
            if result:
                return max([float(r['value'][1]) for r in result])
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting disk usage: {e}")
            return 0.0
    
    def get_network_usage(self):
        """Get network usage in bytes per second"""
        try:
            query = 'rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])'
            result = self.prom.custom_query(query=query)
            if result:
                return sum([float(r['value'][1]) for r in result])
            return 0.0
        except Exception as e:
            self.logger.error(f"Error getting network usage: {e}")
            return 0.0
    
    def check_anomalies(self):
        """Check for system anomalies and return alert data"""
        alerts = []
        
        cpu_usage = self.get_cpu_usage()
        memory_usage = self.get_memory_usage()
        disk_usage = self.get_disk_usage()
        network_usage = self.get_network_usage()
        
        current_time = datetime.now().isoformat()
        
        if cpu_usage > self.cpu_threshold:
            alerts.append({
                'type': 'CPU_SPIKE',
                'value': cpu_usage,
                'threshold': self.cpu_threshold,
                'timestamp': current_time,
                'severity': 'HIGH' if cpu_usage > 90 else 'MEDIUM'
            })
        
        if memory_usage > self.memory_threshold:
            alerts.append({
                'type': 'MEMORY_SPIKE',
                'value': memory_usage,
                'threshold': self.memory_threshold,
                'timestamp': current_time,
                'severity': 'HIGH' if memory_usage > 95 else 'MEDIUM'
            })
        
        if disk_usage > self.disk_threshold:
            alerts.append({
                'type': 'DISK_SPIKE',
                'value': disk_usage,
                'threshold': self.disk_threshold,
                'timestamp': current_time,
                'severity': 'HIGH'
            })
        
        if network_usage > self.network_threshold:
            alerts.append({
                'type': 'NETWORK_SPIKE',
                'value': network_usage,
                'threshold': self.network_threshold,
                'timestamp': current_time,
                'severity': 'MEDIUM'
            })
        
        return alerts
    
    def get_system_metrics(self):
        """Get all current system metrics"""
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_usage(),
            'timestamp': datetime.now().isoformat()
        }
