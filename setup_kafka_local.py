#!/usr/bin/env python3
"""
Local Kafka Setup Script

This script provides an alternative way to set up Kafka locally
without Docker, using embedded Kafka for testing purposes.
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
import requests
import zipfile
import structlog

# Setup logging
logger = structlog.get_logger(__name__)

class LocalKafkaSetup:
    """Setup Kafka locally for development and testing"""
    
    def __init__(self):
        self.kafka_version = "2.13-3.5.0"
        self.kafka_url = f"https://downloads.apache.org/kafka/3.5.0/kafka_{self.kafka_version}.tgz"
        self.base_dir = Path.cwd() / "kafka_local"
        self.kafka_dir = self.base_dir / f"kafka_{self.kafka_version}"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.base_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.zookeeper_process = None
        self.kafka_process = None
    
    def download_kafka(self):
        """Download and extract Kafka"""
        if self.kafka_dir.exists():
            logger.info("Kafka already downloaded", path=str(self.kafka_dir))
            return True
        
        logger.info("Downloading Kafka", version=self.kafka_version)
        
        try:
            # Download Kafka
            response = requests.get(self.kafka_url, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tgz") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Extract
            logger.info("Extracting Kafka")
            shutil.unpack_archive(tmp_path, self.base_dir)
            
            # Clean up
            os.unlink(tmp_path)
            
            logger.info("Kafka downloaded and extracted successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to download Kafka", error=str(e))
            return False
    
    def create_config_files(self):
        """Create Kafka configuration files"""
        # Zookeeper config
        zk_config = f"""
dataDir={self.data_dir}/zookeeper
clientPort=2181
maxClientCnxns=0
admin.enableServer=false
"""
        
        zk_config_path = self.kafka_dir / "config" / "zookeeper.properties"
        with open(zk_config_path, 'w') as f:
            f.write(zk_config)
        
        # Kafka config
        kafka_config = f"""
broker.id=0
listeners=PLAINTEXT://localhost:9092
log.dirs={self.data_dir}/kafka-logs
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
num.partitions=1
num.recovery.threads.per.data.dir=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1
log.retention.hours=168
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
zookeeper.connect=localhost:2181
zookeeper.connection.timeout.ms=18000
group.initial.rebalance.delay.ms=0
"""
        
        kafka_config_path = self.kafka_dir / "config" / "server.properties"
        with open(kafka_config_path, 'w') as f:
            f.write(kafka_config)
        
        logger.info("Configuration files created")
    
    def start_zookeeper(self):
        """Start Zookeeper"""
        if self.zookeeper_process and self.zookeeper_process.poll() is None:
            logger.info("Zookeeper already running")
            return True
        
        logger.info("Starting Zookeeper")
        
        zk_script = self.kafka_dir / "bin" / "zookeeper-server-start.bat" if os.name == 'nt' else self.kafka_dir / "bin" / "zookeeper-server-start.sh"
        zk_config = self.kafka_dir / "config" / "zookeeper.properties"
        
        try:
            self.zookeeper_process = subprocess.Popen(
                [str(zk_script), str(zk_config)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.kafka_dir)
            )
            
            # Wait for Zookeeper to start
            time.sleep(5)
            
            if self.zookeeper_process.poll() is None:
                logger.info("Zookeeper started successfully")
                return True
            else:
                logger.error("Zookeeper failed to start")
                return False
                
        except Exception as e:
            logger.error("Error starting Zookeeper", error=str(e))
            return False
    
    def start_kafka(self):
        """Start Kafka"""
        if self.kafka_process and self.kafka_process.poll() is None:
            logger.info("Kafka already running")
            return True
        
        logger.info("Starting Kafka")
        
        kafka_script = self.kafka_dir / "bin" / "kafka-server-start.bat" if os.name == 'nt' else self.kafka_dir / "bin" / "kafka-server-start.sh"
        kafka_config = self.kafka_dir / "config" / "server.properties"
        
        try:
            self.kafka_process = subprocess.Popen(
                [str(kafka_script), str(kafka_config)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.kafka_dir)
            )
            
            # Wait for Kafka to start
            time.sleep(10)
            
            if self.kafka_process.poll() is None:
                logger.info("Kafka started successfully")
                return True
            else:
                logger.error("Kafka failed to start")
                return False
                
        except Exception as e:
            logger.error("Error starting Kafka", error=str(e))
            return False
    
    def setup_and_start(self):
        """Complete setup and start process"""
        logger.info("Setting up local Kafka environment")
        
        # Download Kafka if needed
        if not self.download_kafka():
            return False
        
        # Create config files
        self.create_config_files()
        
        # Start Zookeeper
        if not self.start_zookeeper():
            return False
        
        # Start Kafka
        if not self.start_kafka():
            self.stop()
            return False
        
        logger.info("Local Kafka setup completed successfully")
        logger.info("Kafka is running on localhost:9092")
        logger.info("Zookeeper is running on localhost:2181")
        
        return True
    
    def stop(self):
        """Stop Kafka and Zookeeper"""
        logger.info("Stopping local Kafka environment")
        
        if self.kafka_process:
            self.kafka_process.terminate()
            try:
                self.kafka_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.kafka_process.kill()
            logger.info("Kafka stopped")
        
        if self.zookeeper_process:
            self.zookeeper_process.terminate()
            try:
                self.zookeeper_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.zookeeper_process.kill()
            logger.info("Zookeeper stopped")
    
    def is_running(self):
        """Check if Kafka is running"""
        try:
            from confluent_kafka import Producer
            producer = Producer({'bootstrap.servers': 'localhost:9092'})
            # Test connection by getting metadata
            metadata = producer.list_topics(timeout=5)
            return True
        except Exception:
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local Kafka Setup')
    parser.add_argument('action', choices=['start', 'stop', 'status'], help='Action to perform')
    
    args = parser.parse_args()
    
    setup = LocalKafkaSetup()
    
    if args.action == 'start':
        success = setup.setup_and_start()
        if success:
            print("\n" + "="*50)
            print("LOCAL KAFKA ENVIRONMENT STARTED")
            print("="*50)
            print("Kafka: localhost:9092")
            print("Zookeeper: localhost:2181")
            print("\nPress Ctrl+C to stop")
            print("="*50)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                setup.stop()
        else:
            print("Failed to start Kafka environment")
            sys.exit(1)
    
    elif args.action == 'stop':
        setup.stop()
        print("Kafka environment stopped")
    
    elif args.action == 'status':
        if setup.is_running():
            print("Kafka is running")
        else:
            print("Kafka is not running")

if __name__ == '__main__':
    main()