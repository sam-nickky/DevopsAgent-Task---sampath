
import logging
import json
import requests
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class NotificationManager:
    def __init__(self, slack_token=None, slack_channel=None, webhook_url=None):
        self.slack_token = slack_token
        self.slack_channel = slack_channel or "#alerts"
        self.webhook_url = webhook_url
        
        if self.slack_token:
            self.slack_client = WebClient(token=self.slack_token)
        else:
            self.slack_client = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def format_alert_message(self, alert_data, analysis_result=None, remediation_result=None):
        """Format alert message for notifications"""
        alert_type = alert_data.get('type', 'UNKNOWN')
        value = alert_data.get('value', 0)
        threshold = alert_data.get('threshold', 0)
        severity = alert_data.get('severity', 'MEDIUM')
        timestamp = alert_data.get('timestamp', datetime.now().isoformat())
        
        # Create severity emoji
        severity_emoji = {
            'HIGH': '🚨',
            'MEDIUM': '⚠️',
            'LOW': '🔸'
        }.get(severity, '⚠️')
        
        # Base message
        message = f"""
{severity_emoji} **SYSTEM ALERT - {alert_type}**

📊 **Metrics:**
• Current Value: {value}%
• Threshold: {threshold}%
• Severity: {severity}
• Time: {timestamp}

"""
        
        # Add analysis if available
        if analysis_result:
            root_cause = analysis_result.get('root_cause', 'Unknown')
            confidence = analysis_result.get('confidence', 'LOW')
            
            message += f"""
🔍 **Root Cause Analysis:**
• Identified Cause: {root_cause}
• Confidence: {confidence}
• Evidence: {', '.join(analysis_result.get('evidence', [])[:3])}

"""
        
        # Add remediation results if available
        if remediation_result:
            if remediation_result.get('success'):
                message += f"""
✅ **Automated Remediation:**
• Action: Successful
• Details: {remediation_result.get('message', 'Remediation completed')}

"""
                for result in remediation_result.get('remediation_results', []):
                    if result.get('success'):
                        message += f"• ✓ {result.get('message', 'Action completed')}\n"
            else:
                message += f"""
❌ **Remediation Failed:**
• Reason: {remediation_result.get('message', 'Unknown error')}
• **HUMAN INTERVENTION REQUIRED**

"""
        
        message += f"""
🔗 **Actions:**
• Check Grafana Dashboard: http://localhost:3000
• View Prometheus Metrics: http://localhost:9090
• System Status: OK

---
*OpsBot - Automated DevOps Monitoring*
        """
        
        return message.strip()
    
    def send_slack_notification(self, message, channel=None):
        """Send notification to Slack"""
        if not self.slack_client:
            self.logger.warning("Slack client not configured")
            return False
        
        try:
            channel = channel or self.slack_channel
            response = self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                username="OpsBot",
                icon_emoji=":robot_face:"
            )
            
            self.logger.info(f"Slack notification sent successfully to {channel}")
            return True
            
        except SlackApiError as e:
            self.logger.error(f"Error sending Slack notification: {e.response['error']}")
            return False
    
    def send_webhook_notification(self, alert_data, analysis_result=None, remediation_result=None):
        """Send notification via webhook"""
        if not self.webhook_url:
            self.logger.warning("Webhook URL not configured")
            return False
        
        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "alert": alert_data,
                "analysis": analysis_result,
                "remediation": remediation_result,
                "source": "OpsBot"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Webhook notification sent successfully")
                return True
            else:
                self.logger.error(f"Webhook notification failed: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def log_incident(self, alert_data, analysis_result=None, remediation_result=None):
        """Log incident to file"""
        try:
            incident_data = {
                "timestamp": datetime.now().isoformat(),
                "alert": alert_data,
                "analysis": analysis_result,
                "remediation": remediation_result
            }
            
            with open("incidents.log", "a") as f:
                f.write(json.dumps(incident_data) + "\n")
            
            self.logger.info("Incident logged to file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging incident: {e}")
            return False
    
    def send_notification(self, alert_data, analysis_result=None, remediation_result=None):
        """Send notification through all configured channels"""
        message = self.format_alert_message(alert_data, analysis_result, remediation_result)
        
        results = {
            "slack": False,
            "webhook": False,
            "log": False
        }
        
        # Send Slack notification
        if self.slack_client:
            results["slack"] = self.send_slack_notification(message)
        
        # Send webhook notification
        if self.webhook_url:
            results["webhook"] = self.send_webhook_notification(alert_data, analysis_result, remediation_result)
        
        # Always log to file
        results["log"] = self.log_incident(alert_data, analysis_result, remediation_result)
        
        # Print to console as fallback
        print("\n" + "="*50)
        print("OPSBOT ALERT NOTIFICATION")
        print("="*50)
        print(message)
        print("="*50 + "\n")
        
        return results
