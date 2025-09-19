#!/bin/bash

# EKS Node User Data Script
# Swiss Engineering Standards: Secure, Monitored, Optimized

set -o xtrace

# Update system packages
yum update -y

# Install additional packages for monitoring and security
yum install -y \
    amazon-cloudwatch-agent \
    awscli \
    jq \
    htop \
    iotop \
    tcpdump

# Configure CloudWatch agent for enhanced monitoring
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "metrics": {
        "namespace": "EKS/Epic8",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": true
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/messages",
                        "log_group_name": "/aws/eks/${cluster_name}/node/system",
                        "log_stream_name": "{instance_id}/system"
                    },
                    {
                        "file_path": "/var/log/cloud-init.log",
                        "log_group_name": "/aws/eks/${cluster_name}/node/cloud-init",
                        "log_stream_name": "{instance_id}/cloud-init"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Configure Docker daemon for optimal performance
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "live-restore": true,
    "max-concurrent-downloads": 10,
    "max-concurrent-uploads": 5,
    "default-ulimits": {
        "memlock": {
            "Name": "memlock",
            "Hard": -1,
            "Soft": -1
        },
        "nofile": {
            "Name": "nofile",
            "Hard": 65536,
            "Soft": 65536
        }
    }
}
EOF

# Optimize kernel parameters for containerized workloads
cat >> /etc/sysctl.conf << 'EOF'

# Epic 8 RAG Platform Optimizations
# Network optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# File system optimizations
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 8192

# Memory optimizations
vm.max_map_count = 262144
vm.swappiness = 1
kernel.pid_max = 4194304
EOF

sysctl -p

# Set up disk optimization
echo 'mq-deadline' > /sys/block/nvme0n1/queue/scheduler
echo '2' > /sys/block/nvme0n1/queue/rq_affinity

# Bootstrap the EKS node
/etc/eks/bootstrap.sh ${cluster_name} ${bootstrap_arguments}

# Install Epic 8 specific tools
curl -L https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz | tar xz
mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
chmod +x /usr/local/bin/node_exporter

# Create node_exporter service
cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=nobody
Group=nobody
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --collector.diskstats.ignored-devices="^(ram|loop|fd|(h|s|v|xv)d[a-z]|nvme\\d+n\\d+p)\\d+$"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter

# Configure log rotation for containers
cat > /etc/logrotate.d/docker-containers << 'EOF'
/var/lib/docker/containers/*/*.log {
    rotate 5
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
EOF

# Set up node readiness probe
cat > /usr/local/bin/node-readiness-check.sh << 'EOF'
#!/bin/bash

# Epic 8 Node Readiness Check
# Ensures node is ready for Epic 8 workloads

set -e

# Check if kubelet is running
if ! systemctl is-active --quiet kubelet; then
    echo "Kubelet is not active"
    exit 1
fi

# Check if node is ready in Kubernetes
if ! kubectl get nodes $(hostname) -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' | grep -q "True"; then
    echo "Node is not ready in Kubernetes"
    exit 1
fi

# Check Docker daemon
if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is not running"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "Disk usage is too high: $DISK_USAGE%"
    exit 1
fi

# Check memory
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", ($3/$2)*100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "Memory usage is too high: $MEM_USAGE%"
    exit 1
fi

echo "Node is ready for Epic 8 workloads"
exit 0
EOF

chmod +x /usr/local/bin/node-readiness-check.sh

# Set up cron job for readiness check
echo "*/5 * * * * root /usr/local/bin/node-readiness-check.sh >> /var/log/node-readiness.log 2>&1" >> /etc/crontab

# Signal completion
/opt/aws/bin/cfn-signal -e $? --stack ${AWS::StackName} --resource AutoScalingGroup --region ${AWS::Region}

echo "Epic 8 EKS node initialization completed successfully"