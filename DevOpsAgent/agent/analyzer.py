
import openai
import logging
import subprocess
import json
from datetime import datetime, timedelta

class LogAnalyzer:
    def __init__(self, openai_api_key=None):
        if openai_api_key:
            openai.api_key = openai_api_key
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_system_logs(self, minutes_back=10):
        """Retrieve system logs from the last N minutes"""
        try:
            # Get system logs using journalctl
            cmd = f"journalctl --since '{minutes_back} minutes ago' --no-pager --output=json-pretty"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.error(f"Error getting system logs: {result.stderr}")
                return ""
        except Exception as e:
            self.logger.error(f"Error retrieving logs: {e}")
            return ""
    
    def get_docker_logs(self, container_name=None, minutes_back=10):
        """Get Docker container logs"""
        try:
            if container_name:
                cmd = f"docker logs --since {minutes_back}m {container_name}"
            else:
                # Get logs from all running containers
                cmd = f"docker ps --format '{{{{.Names}}}}' | xargs -I {{}} docker logs --since {minutes_back}m {{}}"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout
            else:
                self.logger.error(f"Error getting Docker logs: {result.stderr}")
                return ""
        except Exception as e:
            self.logger.error(f"Error retrieving Docker logs: {e}")
            return ""
    
    def analyze_logs_with_llm(self, logs, alert_type):
        """Analyze logs using OpenAI API to identify root causes"""
        try:
            prompt = f"""
            You are OpsBot, an AI DevOps assistant. Analyze the following logs to identify the possible cause of a {alert_type}.
            
            Instructions:
            1. Look for patterns that could cause high resource usage
            2. Identify specific error messages or warnings
            3. Provide a clear, actionable root cause analysis
            4. Suggest remediation steps
            5. Rate your confidence level (HIGH/MEDIUM/LOW)
            
            Logs to analyze:
            {logs[:4000]}  # Limit to avoid token limits
            
            Respond in JSON format:
            {{
                "root_cause": "Brief description of the identified cause",
                "confidence": "HIGH/MEDIUM/LOW",
                "evidence": ["List of specific log entries that support your analysis"],
                "recommended_actions": ["List of suggested remediation steps"],
                "requires_human_intervention": true/false
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are OpsBot, a reliable AI DevOps assistant focused on system stability and root cause analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing logs with LLM: {e}")
            return {
                "root_cause": "Unable to analyze logs automatically",
                "confidence": "LOW",
                "evidence": [],
                "recommended_actions": ["Manual investigation required"],
                "requires_human_intervention": True
            }
    
    def get_process_info(self):
        """Get information about running processes"""
        try:
            cmd = "ps aux --sort=-%cpu | head -20"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            self.logger.error(f"Error getting process info: {e}")
            return ""
    
    def analyze_incident(self, alert_data):
        """Main method to analyze an incident"""
        alert_type = alert_data.get('type', 'UNKNOWN')
        
        # Collect relevant logs
        system_logs = self.get_system_logs()
        docker_logs = self.get_docker_logs()
        process_info = self.get_process_info()
        
        # Combine all log sources
        combined_logs = f"""
        SYSTEM LOGS:
        {system_logs}
        
        DOCKER LOGS:
        {docker_logs}
        
        PROCESS INFO:
        {process_info}
        """
        
        # Analyze with LLM
        analysis = self.analyze_logs_with_llm(combined_logs, alert_type)
        
        # Add metadata
        analysis['alert_data'] = alert_data
        analysis['analysis_timestamp'] = datetime.now().isoformat()
        
        return analysis
