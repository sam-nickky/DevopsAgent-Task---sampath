
# 🤖 OpsBot - AI-Powered DevOps Agent

OpsBot is an intelligent DevOps automation agent that monitors your infrastructure, detects anomalies, performs root cause analysis using AI, and executes automated remediation actions.

## 🏗️ Architecture

```
DevOpsAgent/
├── agent/
│   ├── monitor.py          # System monitoring & anomaly detection
│   ├── analyzer.py         # AI-powered log analysis
│   ├── remediation.py      # Automated remediation actions
│   ├── notifier.py         # Multi-channel notifications
│   └── opsbot_agent.py     # Main orchestration agent
├── requirements.txt        # Python dependencies
├── config.json            # Configuration file (auto-generated)
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Server Setup (AWS EC2 Free Tier)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Python and pip
sudo apt install python3 python3-pip -y
sudo apt install python3-venv -y
python3 -m venv venv
source venv/bin/activate

# Install Docker Compose
sudo apt install docker-compose -y
```

### 2. Monitoring Stack Setup

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

volumes:
  grafana-data:
```

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

Start the monitoring stack:

```bash
docker-compose up -d
```

### 3. Install OpsBot Agent

```bash
# Clone or download the agent
git clone <your-repo-url>
cd DevOpsAgent

# Install dependencies
pip install -r requirements.txt

# Run the agent
python3 agent/opsbot_agent.py
```

## ⚙️ Configuration

On first run, OpsBot creates a `config.json` file with default settings:

```json
{
  "prometheus_url": "http://localhost:9090",
  "openai_api_key": null,
  "slack_token": null,
  "slack_channel": "#alerts",
  "webhook_url": null,
  "auto_remediation": true,
  "monitoring_interval": 60,
  "cpu_threshold": 80,
  "memory_threshold": 85,
  "disk_threshold": 90
}
```

### Required Configurations:

1. **OpenAI API Key**: For AI-powered log analysis
   ```bash
   # Get your API key from https://platform.openai.com/api-keys
   # Update config.json with your key
   ```

2. **Slack Integration** (Optional):
   ```bash
   # Create a Slack app at https://api.slack.com/apps
   # Get Bot User OAuth Token
   # Update config.json with token and channel
   ```

## 🎯 Features

### 1. **Multi-Metric Monitoring**
- CPU usage monitoring
- Memory utilization tracking
- Disk space monitoring
- Network traffic analysis

### 2. **AI-Powered Analysis**
- Intelligent log analysis using OpenAI
- Root cause identification
- Confidence scoring
- Evidence collection

### 3. **Automated Remediation**
- Docker container restarts
- System service management
- Process termination for high CPU usage
- Disk cleanup operations

### 4. **Multi-Channel Notifications**
- Slack notifications
- Webhook integrations
- File logging
- Console output

## 🧪 Testing

### Test CPU Spike:

```bash
# Create CPU load
stress --cpu 4 --timeout 300s

# Or use Python:
python3 -c "
import threading
import time

def cpu_load():
    while True:
        pass

for i in range(4):
    thread = threading.Thread(target=cpu_load)
    thread.daemon = True
    thread.start()

time.sleep(300)
"
```

### Test Memory Spike:

```bash
# Create memory load
stress --vm 1 --vm-bytes 1G --timeout 300s
```

### Test Disk Usage:

```bash
# Create large file
dd if=/dev/zero of=/tmp/large_file bs=1M count=1000
```

## 📊 Monitoring Dashboards

### Grafana Dashboard
- URL: http://your-server:3000
- Username: admin
- Password: admin

### Prometheus Metrics
- URL: http://your-server:9090

## 🔧 Advanced Usage

### Custom Remediation Actions

Modify `remediation.py` to add custom remediation logic:

```python
def custom_remediation_action(self, alert_data):
    # Your custom logic here
    pass
```

### Custom Notification Channels

Extend `notifier.py` to add new notification methods:

```python
def send_custom_notification(self, message):
    # Your custom notification logic
    pass
```

## 📝 Logs

OpsBot generates several log files:

- `opsbot.log` - Main application log
- `incidents.log` - Incident records in JSON format

## 🚨 Troubleshooting

### Common Issues:

1. **Prometheus Connection Failed**
   ```bash
   # Check if Prometheus is running
   docker ps | grep prometheus
   
   # Check Prometheus logs
   docker logs prometheus
   ```

2. **Docker Permission Denied**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **OpenAI API Errors**
   - Verify API key is correct
   - Check API rate limits
   - Ensure sufficient credits

## 🔒 Security Considerations

- Store API keys securely
- Use environment variables for sensitive data
- Implement proper access controls
- Monitor remediation actions carefully

## 📈 Performance Optimization

- Adjust monitoring intervals based on needs
- Implement metric caching for high-frequency checks
- Use log rotation for large log files
- Monitor OpsBot's own resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the logs (`opsbot.log`)
2. Verify configuration (`config.json`)
3. Test individual components
4. Create an issue with logs and configuration

---

**OpsBot** - Your AI-powered DevOps companion for 99.99% uptime! 🚀
