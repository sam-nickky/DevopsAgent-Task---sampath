
#!/usr/bin/env python3

import time
import logging
import schedule
import json
import os
from datetime import datetime
from monitor import SystemMonitor
from analyzer import LogAnalyzer
from remediation import RemediationEngine
from notifier import NotificationManager

class OpsBotAgent:
    def __init__(self, config_file="config.json"):
        self.config = self.load_config(config_file)
        self.setup_logging()
        
        # Initialize components
        self.monitor = SystemMonitor(
            prometheus_url=self.config.get('prometheus_url', 'http://localhost:9090')
        )
        
        self.analyzer = LogAnalyzer(
            openai_api_key=self.config.get('openai_api_key')
        )
        
        self.remediation = RemediationEngine()
        
        self.notifier = NotificationManager(
            slack_token=self.config.get('slack_token'),
            slack_channel=self.config.get('slack_channel'),
            webhook_url=self.config.get('webhook_url')
        )
        
        self.monitoring_enabled = True
        self.auto_remediation_enabled = self.config.get('auto_remediation', True)
        
        self.logger.info("OpsBot Agent initialized successfully")
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                default_config = {
                    "prometheus_url": "http://localhost:9090",
                    "openai_api_key": None,
                    "slack_token": None,
                    "slack_channel": "#alerts",
                    "webhook_url": None,
                    "auto_remediation": True,
                    "monitoring_interval": 60,
                    "cpu_threshold": 80,
                    "memory_threshold": 85,
                    "disk_threshold": 90
                }
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                print(f"Created default config file: {config_file}")
                print("Please update the config file with your API keys and settings")
                return default_config
                
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('opsbot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def monitor_system(self):
        """Main monitoring loop - called by scheduler"""
        if not self.monitoring_enabled:
            return
        
        try:
            self.logger.info("Running system monitoring check...")
            
            # Get current metrics
            metrics = self.monitor.get_system_metrics()
            
            # Check for anomalies
            alerts = self.monitor.check_anomalies()
            
            if alerts:
                self.logger.warning(f"Found {len(alerts)} alerts")
                
                for alert in alerts:
                    self.handle_alert(alert)
            else:
                self.logger.info("System monitoring check completed - no alerts")
                
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
    
    def handle_alert(self, alert_data):
        """Handle a single alert through the complete pipeline"""
        try:
            alert_type = alert_data.get('type')
            severity = alert_data.get('severity')
            
            self.logger.warning(f"Processing alert: {alert_type} (Severity: {severity})")
            
            # Step 1: Analyze the incident
            self.logger.info("Starting log analysis...")
            analysis_result = self.analyzer.analyze_incident(alert_data)
            
            self.logger.info(f"Analysis completed - Confidence: {analysis_result.get('confidence')}")
            
            # Step 2: Attempt remediation if conditions are met
            remediation_result = None
            if self.auto_remediation_enabled:
                self.logger.info("Attempting automated remediation...")
                remediation_result = self.remediation.execute_remediation(analysis_result)
                
                if remediation_result.get('success'):
                    self.logger.info("Automated remediation successful")
                else:
                    self.logger.warning("Automated remediation failed or skipped")
            
            # Step 3: Send notifications
            self.logger.info("Sending notifications...")
            notification_results = self.notifier.send_notification(
                alert_data, 
                analysis_result, 
                remediation_result
            )
            
            self.logger.info(f"Notifications sent: {notification_results}")
            
            # Step 4: Post-remediation verification
            if remediation_result and remediation_result.get('success'):
                time.sleep(30)  # Wait for system to stabilize
                self.verify_remediation(alert_data)
            
        except Exception as e:
            self.logger.error(f"Error handling alert: {e}")
    
    def verify_remediation(self, original_alert):
        """Verify that remediation was successful"""
        try:
            self.logger.info("Verifying remediation effectiveness...")
            
            # Get fresh metrics
            current_metrics = self.monitor.get_system_metrics()
            new_alerts = self.monitor.check_anomalies()
            
            # Check if the original issue is resolved
            alert_type = original_alert.get('type')
            resolved = True
            
            for alert in new_alerts:
                if alert.get('type') == alert_type:
                    resolved = False
                    break
            
            if resolved:
                self.logger.info("✅ Remediation verification: SUCCESSFUL")
                verification_message = f"✅ System has been successfully remediated. {alert_type} is now within normal thresholds."
            else:
                self.logger.warning("❌ Remediation verification: FAILED")
                verification_message = f"❌ {alert_type} persists after remediation. Manual intervention required."
            
            # Send verification notification
            self.notifier.send_slack_notification(verification_message)
            
        except Exception as e:
            self.logger.error(f"Error during remediation verification: {e}")
    
    def start_monitoring(self):
        """Start the monitoring scheduler"""
        monitoring_interval = self.config.get('monitoring_interval', 60)
        
        self.logger.info(f"Starting OpsBot monitoring (interval: {monitoring_interval}s)")
        
        # Schedule monitoring
        schedule.every(monitoring_interval).seconds.do(self.monitor_system)
        
        # Initial health check
        self.health_check()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
    
    def health_check(self):
        """Perform initial health check"""
        self.logger.info("Performing initial health check...")
        
        try:
            # Test Prometheus connection
            metrics = self.monitor.get_system_metrics()
            if metrics['cpu'] >= 0:
                self.logger.info("✅ Prometheus connection: OK")
            else:
                self.logger.warning("⚠️ Prometheus connection: Issues detected")
            
            # Test Docker connection
            if self.remediation.docker_client:
                containers = self.remediation.docker_client.containers.list()
                self.logger.info(f"✅ Docker connection: OK ({len(containers)} containers running)")
            else:
                self.logger.warning("⚠️ Docker connection: Not available")
            
            self.logger.info("Health check completed")
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_enabled = False
        self.logger.info("Monitoring stopped")

def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════╗
    ║           🤖 OPSBOT AGENT         ║
    ║    AI-Powered DevOps Automation   ║
    ╚═══════════════════════════════════╝
    """)
    
    print("Initializing OpsBot Agent...")
    
    try:
        # Create and start the agent
        agent = OpsBotAgent()
        
        print("\n🚀 OpsBot Agent is now monitoring your system!")
        print("Press Ctrl+C to stop monitoring\n")
        
        # Start monitoring
        agent.start_monitoring()
        
    except Exception as e:
        print(f"Failed to start OpsBot Agent: {e}")
        logging.error(f"Startup error: {e}")

if __name__ == "__main__":
    main()
