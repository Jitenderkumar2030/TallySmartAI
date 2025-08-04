import psutil
import sqlite3
import os
import redis
import requests
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List
import asyncio

class AdvancedHealthMonitor:
    def __init__(self):
        self.setup_logging()
        self.redis_client = None
        self.health_history = []
        self.alert_thresholds = {
            'cpu_usage': 80,
            'memory_usage': 85,
            'disk_usage': 90,
            'response_time': 5000,  # milliseconds
            'error_rate': 0.05  # 5%
        }
        
    def setup_logging(self):
        """Setup health monitoring logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/health_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def comprehensive_health_check(self):
        """Perform comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'metrics': {},
            'alerts': []
        }
        
        # System resource checks
        health_status['components']['system'] = await self._check_system_resources()
        health_status['components']['database'] = await self._check_database_health()
        health_status['components']['cache'] = await self._check_cache_health()
        health_status['components']['external_apis'] = await self._check_external_apis()
        health_status['components']['application'] = await self._check_application_health()
        
        # Calculate overall status
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if 'critical' in component_statuses:
            health_status['overall_status'] = 'critical'
        elif 'warning' in component_statuses:
            health_status['overall_status'] = 'warning'
        
        # Store health history
        self.health_history.append(health_status)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history.pop(0)
        
        # Generate alerts if needed
        await self._generate_health_alerts(health_status)
        
        return health_status
    
    async def _check_system_resources(self):
        """Check system CPU, memory, and disk usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = 'healthy'
            issues = []
            
            if cpu_percent > self.alert_thresholds['cpu_usage']:
                status = 'critical' if cpu_percent > 95 else 'warning'
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > self.alert_thresholds['memory_usage']:
                status = 'critical' if memory.percent > 95 else 'warning'
                issues.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > self.alert_thresholds['disk_usage']:
                status = 'critical'
                issues.append(f"Low disk space: {disk.percent}% used")
            
            return {
                'status': status,
                'metrics': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'available_memory': f"{memory.available / (1024**3):.1f}GB"
                },
                'issues': issues
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['System resource check failed']
            }
    
    async def _check_database_health(self):
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            
            # Test database connection
            conn = sqlite3.connect('users.db', timeout=5.0)
            cursor = conn.cursor()
            
            # Test query performance
            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            
            # Check database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            conn.close()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            status = 'healthy'
            issues = []
            
            if response_time > 1000:  # 1 second
                status = 'warning'
                issues.append(f"Slow database response: {response_time:.0f}ms")
            
            return {
                'status': status,
                'metrics': {
                    'response_time_ms': response_time,
                    'user_count': user_count,
                    'database_size_mb': db_size / (1024 * 1024)
                },
                'issues': issues
            }
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'issues': ['Database connection failed']
            }
    
    async def _check_cache_health(self):
        """Check Redis cache health"""
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis(host='localhost', port=6379, socket_timeout=5)
            
            start_time = datetime.now()
            
            # Test cache connectivity
            self.redis_client.ping()
            
            # Get cache info
            info = self.redis_client.info()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            status = 'healthy'
            issues = []
            
            if response_time > 100:  # 100ms
                status = 'warning'
                issues.append(f"Slow cache response: {response_time:.0f}ms")
            
            return {
                'status': status,
                'metrics': {
                    'response_time_ms': response_time,
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_mb': info.get('used_memory', 0) / (1024 * 1024),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                },
                'issues': issues
            }
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'issues': ['Cache connection failed - running without cache']
            }
    
    async def _check_external_apis(self):
        """Check external API connectivity"""
        api_checks = {
            'openai': 'https://api.openai.com/v1/models',
            'cashfree': 'https://api.cashfree.com/pg/orders',
            'telegram': f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN', 'test')}/getMe"
        }
        
        results = {}
        overall_status = 'healthy'
        
        for api_name, url in api_checks.items():
            try:
                start_time = datetime.now()
                response = requests.get(url, timeout=10)
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    results[api_name] = {
                        'status': 'healthy',
                        'response_time_ms': response_time
                    }
                else:
                    results[api_name] = {
                        'status': 'warning',
                        'response_time_ms': response_time,
                        'status_code': response.status_code
                    }
                    overall_status = 'warning'
            except Exception as e:
                results[api_name] = {
                    'status': 'critical',
                    'error': str(e)
                }
                overall_status = 'warning'  # Don't mark as critical for external APIs
        
        return {
            'status': overall_status,
            'apis': results,
            'issues': [f"{api}: {result.get('error', 'API unavailable')}" 
                      for api, result in results.items() 
                      if result['status'] != 'healthy']
        }
    
    async def _check_application_health(self):
        """Check application-specific health metrics"""
        try:
            # Check log files for recent errors
            error_count = 0
            if os.path.exists('logs/app_errors.log'):
                with open('logs/app_errors.log', 'r') as f:
                    lines = f.readlines()
                    # Count errors in last hour
                    recent_errors = [line for line in lines[-1000:] 
                                   if 'ERROR' in line and 
                                   (datetime.now() - datetime.fromisoformat(line.split(' - ')[0])).total_seconds() < 3600]
                    error_count = len(recent_errors)
            
            # Check application metrics
            status = 'healthy'
            issues = []
            
            if error_count > 10:  # More than 10 errors per hour
                status = 'warning'
                issues.append(f"High error rate: {error_count} errors in last hour")
            
            return {
                'status': status,
                'metrics': {
                    'recent_errors': error_count,
                    'uptime_hours': self._get_uptime_hours()
                },
                'issues': issues
            }
        except Exception as e:
            return {
                'status': 'warning',
                'error': str(e),
                'issues': ['Application health check failed']
            }
    
    def _get_uptime_hours(self):
        """Get application uptime in hours"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return uptime.total_seconds() / 3600
        except:
            return 0
    
    async def _generate_health_alerts(self, health_status):
        """Generate alerts based on health status"""
        if health_status['overall_status'] in ['warning', 'critical']:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'severity': health_status['overall_status'],
                'message': f"System health check failed: {health_status['overall_status']}",
                'details': health_status
            }
            
            # Log alert
            self.logger.warning(f"Health Alert: {alert['message']}")
            
            # Send notification (implement based on your notification system)
            await self._send_health_alert(alert)
    
    async def _send_health_alert(self, alert):
        """Send health alert notification"""
        try:
            # Implement notification logic here
            # Could send email, Slack message, etc.
            pass
        except Exception as e:
            self.logger.error(f"Failed to send health alert: {e}")
    
    def get_health_trends(self, hours=24):
        """Get health trends over specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_checks = [
            check for check in self.health_history 
            if datetime.fromisoformat(check['timestamp']) > cutoff_time
        ]
        
        if not recent_checks:
            return {}
        
        # Calculate trends
        cpu_values = [check['components']['system']['metrics']['cpu_usage'] 
                     for check in recent_checks 
                     if 'system' in check['components']]
        
        memory_values = [check['components']['system']['metrics']['memory_usage'] 
                        for check in recent_checks 
                        if 'system' in check['components']]
        
        return {
            'period_hours': hours,
            'total_checks': len(recent_checks),
            'avg_cpu_usage': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'avg_memory_usage': sum(memory_values) / len(memory_values) if memory_values else 0,
            'health_score': len([c for c in recent_checks if c['overall_status'] == 'healthy']) / len(recent_checks)
        }

# Global health monitor instance
health_monitor = AdvancedHealthMonitor()
