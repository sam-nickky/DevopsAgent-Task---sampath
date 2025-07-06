
import docker
import subprocess
import logging
import time
from datetime import datetime

class RemediationEngine:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logging.error(f"Could not connect to Docker: {e}")
            self.docker_client = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def restart_docker_container(self, container_name):
        """Restart a specific Docker container"""
        try:
            if not self.docker_client:
                return {"success": False, "message": "Docker client not available"}
            
            container = self.docker_client.containers.get(container_name)
            
            self.logger.info(f"Restarting container: {container_name}")
            container.restart()
            
            # Wait a bit and check if container is running
            time.sleep(5)
            container.reload()
            
            if container.status == 'running':
                return {
                    "success": True,
                    "message": f"Container {container_name} restarted successfully",
                    "action": "CONTAINER_RESTART",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"Container {container_name} failed to start after restart",
                    "action": "CONTAINER_RESTART_FAILED"
                }
                
        except docker.errors.NotFound:
            return {"success": False, "message": f"Container {container_name} not found"}
        except Exception as e:
            self.logger.error(f"Error restarting container {container_name}: {e}")
            return {"success": False, "message": f"Error restarting container: {str(e)}"}
    
    def restart_system_service(self, service_name):
        """Restart a system service using systemctl"""
        try:
            self.logger.info(f"Restarting service: {service_name}")
            
            # Stop the service
            result_stop = subprocess.run(
                ["sudo", "systemctl", "stop", service_name],
                capture_output=True, text=True
            )
            
            # Start the service
            result_start = subprocess.run(
                ["sudo", "systemctl", "start", service_name],
                capture_output=True, text=True
            )
            
            # Check status
            result_status = subprocess.run(
                ["sudo", "systemctl", "is-active", service_name],
                capture_output=True, text=True
            )
            
            if result_status.stdout.strip() == "active":
                return {
                    "success": True,
                    "message": f"Service {service_name} restarted successfully",
                    "action": "SERVICE_RESTART",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": f"Service {service_name} failed to start",
                    "action": "SERVICE_RESTART_FAILED"
                }
                
        except Exception as e:
            self.logger.error(f"Error restarting service {service_name}: {e}")
            return {"success": False, "message": f"Error restarting service: {str(e)}"}
    
    def kill_high_cpu_processes(self, cpu_threshold=90):
        """Kill processes consuming too much CPU"""
        try:
            # Get processes sorted by CPU usage
            cmd = f"ps aux --sort=-%cpu | awk 'NR>1 && $3>={cpu_threshold} {{print $2,$11}}' | head -5"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if not result.stdout.strip():
                return {"success": False, "message": "No high CPU processes found"}
            
            killed_processes = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    pid = parts[0]
                    process_name = parts[1]
                    
                    # Avoid killing critical system processes
                    if any(critical in process_name.lower() for critical in ['systemd', 'kernel', 'init']):
                        continue
                    
                    try:
                        subprocess.run(["kill", "-9", pid], check=True)
                        killed_processes.append(f"{process_name} (PID: {pid})")
                        self.logger.info(f"Killed high CPU process: {process_name} (PID: {pid})")
                    except subprocess.CalledProcessError:
                        self.logger.error(f"Failed to kill process {pid}")
            
            return {
                "success": True,
                "message": f"Killed {len(killed_processes)} high CPU processes",
                "killed_processes": killed_processes,
                "action": "PROCESS_KILL",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error killing high CPU processes: {e}")
            return {"success": False, "message": f"Error killing processes: {str(e)}"}
    
    def clear_disk_space(self):
        """Clear temporary files and Docker unused resources"""
        try:
            actions_taken = []
            
            # Clear Docker unused resources
            if self.docker_client:
                try:
                    self.docker_client.containers.prune()
                    self.docker_client.images.prune()
                    self.docker_client.volumes.prune()
                    actions_taken.append("Docker cleanup completed")
                except Exception as e:
                    self.logger.error(f"Docker cleanup failed: {e}")
            
            # Clear system temp files
            temp_commands = [
                "sudo rm -rf /tmp/*",
                "sudo journalctl --vacuum-time=3d",
                "sudo apt-get autoremove -y",
                "sudo apt-get autoclean"
            ]
            
            for cmd in temp_commands:
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    actions_taken.append(f"Executed: {cmd}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Failed to execute {cmd}: {e}")
            
            return {
                "success": True,
                "message": "Disk cleanup completed",
                "actions_taken": actions_taken,
                "action": "DISK_CLEANUP",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error during disk cleanup: {e}")
            return {"success": False, "message": f"Disk cleanup failed: {str(e)}"}
    
    def execute_remediation(self, analysis_result):
        """Execute remediation based on analysis results"""
        alert_type = analysis_result.get('alert_data', {}).get('type', 'UNKNOWN')
        confidence = analysis_result.get('confidence', 'LOW')
        requires_human = analysis_result.get('requires_human_intervention', True)
        
        if requires_human or confidence == 'LOW':
            return {
                "success": False,
                "message": "Remediation requires human intervention",
                "reason": "Low confidence or human intervention required"
            }
        
        remediation_results = []
        
        if alert_type == 'CPU_SPIKE':
            # Try container restart first, then process killing
            if self.docker_client:
                containers = self.docker_client.containers.list()
                for container in containers[:3]:  # Restart first 3 containers
                    result = self.restart_docker_container(container.name)
                    remediation_results.append(result)
            
            # If still high CPU, kill processes
            kill_result = self.kill_high_cpu_processes()
            remediation_results.append(kill_result)
        
        elif alert_type == 'MEMORY_SPIKE':
            # Restart containers and clear cache
            if self.docker_client:
                containers = self.docker_client.containers.list()
                for container in containers[:2]:
                    result = self.restart_docker_container(container.name)
                    remediation_results.append(result)
        
        elif alert_type == 'DISK_SPIKE':
            # Clear disk space
            cleanup_result = self.clear_disk_space()
            remediation_results.append(cleanup_result)
        
        return {
            "success": any(r.get('success', False) for r in remediation_results),
            "remediation_results": remediation_results,
            "timestamp": datetime.now().isoformat()
        }
