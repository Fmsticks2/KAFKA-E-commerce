#!/usr/bin/env python3
"""
Embedded Kafka Adapter

This module provides compatibility between the embedded Kafka REST API
and the kafka-python client interface used by the services.
"""

import json
import time
import threading
import requests
from typing import Dict, List, Any, Optional
import structlog
from config import Config

# Setup logging
logger = structlog.get_logger(__name__)

class EmbeddedKafkaProducer:
    """Producer adapter for embedded Kafka"""
    
    def __init__(self, bootstrap_servers: str = None, value_serializer=None, 
                 key_serializer=None, **kwargs):
        self.base_url = Config.EMBEDDED_KAFKA_URL
        self.value_serializer = value_serializer
        self.key_serializer = key_serializer
        self.session = requests.Session()
        logger.info("EmbeddedKafkaProducer initialized", base_url=self.base_url)
    
    def send(self, topic: str, value=None, key=None, **kwargs):
        """Send a message to a topic"""
        try:
            # Apply serializers if provided
            if self.value_serializer and value is not None:
                value = self.value_serializer(value)
            elif value is not None and not isinstance(value, str):
                value = str(value)
                
            if self.key_serializer and key is not None:
                key = self.key_serializer(key)
            elif key is not None and not isinstance(key, str):
                key = str(key)
            
            data = {
                'key': key,
                'value': value
            }
            
            response = self.session.post(
                f"{self.base_url}/produce/{topic}",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug("Message sent successfully", topic=topic, key=key)
                return MockFuture()
            else:
                logger.error("Failed to send message", 
                           status_code=response.status_code, 
                           response=response.text)
                raise Exception(f"Failed to send message: {response.text}")
                
        except Exception as e:
            logger.error("Error sending message", error=str(e))
            raise
    
    def flush(self, timeout: float = None):
        """Flush any pending messages"""
        # No-op for embedded Kafka
        pass
    
    def close(self, timeout: float = None):
        """Close the producer"""
        self.session.close()
        logger.info("EmbeddedKafkaProducer closed")

class EmbeddedKafkaConsumer:
    """Consumer adapter for embedded Kafka"""
    
    def __init__(self, *topics, bootstrap_servers: str = None, group_id: str = None, 
                 auto_offset_reset: str = 'latest', value_deserializer=None, 
                 key_deserializer=None, **kwargs):
        self.base_url = Config.EMBEDDED_KAFKA_URL
        self.topics = list(topics)
        self.group_id = group_id
        self.auto_offset_reset = auto_offset_reset
        self.value_deserializer = value_deserializer
        self.key_deserializer = key_deserializer
        self.session = requests.Session()
        self.running = False
        self.poll_interval = 1.0  # seconds
        
        logger.info("EmbeddedKafkaConsumer initialized", 
                   topics=self.topics, group_id=group_id)
    
    def subscribe(self, topics: List[str]):
        """Subscribe to topics"""
        self.topics = topics
        logger.info("Subscribed to topics", topics=topics)
    
    def poll(self, timeout_ms: int = 1000, max_records: int = 500):
        """Poll for messages"""
        messages = {}
        
        for topic in self.topics:
            try:
                url = f"{self.base_url}/topics/{topic}/consume"
                params = {
                    'group_id': self.group_id,
                    'auto_offset_reset': self.auto_offset_reset
                }
                
                response = self.session.get(url, params=params, timeout=2)
                response.raise_for_status()
                
                data = response.json()
                topic_messages = data.get('messages', [])
                
                if topic_messages:
                    # Convert to kafka-python format
                    topic_partition = MockTopicPartition(topic, 0)
                    consumer_records = []
                    
                    for msg in topic_messages[-max_records:]:  # Get latest messages
                        key = msg.get('key')
                        value = msg.get('value')
                        
                        # Apply deserializers if provided
                        if self.key_deserializer and key is not None:
                            try:
                                key = self.key_deserializer(key.encode() if isinstance(key, str) else key)
                            except:
                                pass  # Keep original if deserialization fails
                                
                        if self.value_deserializer and value is not None:
                            try:
                                value = self.value_deserializer(value.encode() if isinstance(value, str) else value)
                            except:
                                pass  # Keep original if deserialization fails
                        
                        record = MockConsumerRecord(
                            topic=topic,
                            partition=0,
                            offset=msg.get('offset', 0),
                            key=key,
                            value=value,
                            timestamp=int(msg.get('timestamp', time.time()) * 1000)
                        )
                        consumer_records.append(record)
                    
                    if consumer_records:
                        messages[topic_partition] = consumer_records
                        
            except Exception as e:
                logger.error("Failed to poll topic", topic=topic, error=str(e))
        
        return messages
    
    def commit(self):
        """Commit offsets"""
        # No-op for embedded Kafka
        pass
    
    def close(self):
        """Close the consumer"""
        self.running = False
        self.session.close()
        logger.info("EmbeddedKafkaConsumer closed")

class EmbeddedKafkaAdminClient:
    """Admin client adapter for embedded Kafka"""
    
    def __init__(self, bootstrap_servers: str = None, **kwargs):
        self.base_url = Config.EMBEDDED_KAFKA_URL
        self.session = requests.Session()
        logger.info("EmbeddedKafkaAdminClient initialized")
    
    def create_topics(self, topic_list, timeout_ms: int = 30000, validate_only: bool = False):
        """Create topics"""
        results = {}
        
        for topic_spec in topic_list:
            topic_name = topic_spec.name if hasattr(topic_spec, 'name') else str(topic_spec)
            
            if validate_only:
                # Just validate, don't actually create
                results[topic_name] = MockTopicMetadata(topic_name, None)
                continue
            
            try:
                url = f"{self.base_url}/topics/{topic_name}"
                response = self.session.post(url, timeout=5)
                response.raise_for_status()
                
                results[topic_name] = MockTopicMetadata(topic_name, None)
                logger.info("Topic created", topic=topic_name)
                
            except Exception as e:
                logger.error("Failed to create topic", topic=topic_name, error=str(e))
                results[topic_name] = MockTopicMetadata(topic_name, e)
        
        return MockCreateTopicsResult(results)
    
    def list_topics(self, timeout_ms: int = 30000):
        """List all topics"""
        try:
            url = f"{self.base_url}/topics"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            topics = data.get('topics', [])
            
            return MockListTopicsResult(topics)
            
        except Exception as e:
            logger.error("Failed to list topics", error=str(e))
            return MockListTopicsResult([])
    
    def close(self):
        """Close the admin client"""
        self.session.close()
        logger.info("EmbeddedKafkaAdminClient closed")

# Mock classes to maintain compatibility with kafka-python

class MockFuture:
    """Mock future object"""
    
    def __init__(self, success: bool, exception: Exception = None):
        self.success = success
        self.exception = exception
    
    def get(self, timeout: float = None):
        if self.success:
            return MockRecordMetadata()
        else:
            raise self.exception or Exception("Send failed")
    
    def add_callback(self, callback):
        # Execute callback immediately
        if self.success:
            callback(MockRecordMetadata(), None)
        else:
            callback(None, self.exception)
    
    def add_errback(self, errback):
        if not self.success:
            errback(self.exception)

class MockRecordMetadata:
    """Mock record metadata"""
    
    def __init__(self, topic: str = "test", partition: int = 0, offset: int = 0):
        self.topic = topic
        self.partition = partition
        self.offset = offset

class MockTopicPartition:
    """Mock topic partition"""
    
    def __init__(self, topic: str, partition: int):
        self.topic = topic
        self.partition = partition
    
    def __hash__(self):
        return hash((self.topic, self.partition))
    
    def __eq__(self, other):
        return self.topic == other.topic and self.partition == other.partition

class MockConsumerRecord:
    """Mock consumer record"""
    
    def __init__(self, topic: str, partition: int, offset: int, 
                 key: Any, value: Any, timestamp: int):
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.key = key
        self.value = value
        self.timestamp = timestamp

class MockTopicMetadata:
    """Mock topic metadata"""
    
    def __init__(self, topic: str, error: Exception = None):
        self.topic = topic
        self.error = error

class MockCreateTopicsResult:
    """Mock create topics result"""
    
    def __init__(self, results: Dict[str, MockTopicMetadata]):
        self.results = results
    
    def values(self):
        return self.results

class MockListTopicsResult:
    """Mock list topics result"""
    
    def __init__(self, topics: List[str]):
        self.topics = set(topics)
    
    def __len__(self):
        return len(self.topics)
    
    def __iter__(self):
        return iter(self.topics)
    
    def __contains__(self, topic):
        return topic in self.topics

# Monkey patch kafka-python imports when using embedded Kafka
def patch_kafka_imports():
    """Replace kafka-python classes with embedded Kafka adapters"""
    import sys
    
    # Create mock kafka module
    class MockKafkaModule:
        KafkaProducer = EmbeddedKafkaProducer
        KafkaConsumer = EmbeddedKafkaConsumer
        KafkaAdminClient = EmbeddedKafkaAdminClient
        TopicPartition = MockTopicPartition
    
    class MockKafkaAdminModule:
        NewTopic = str  # Simple string for topic names
    
    # Replace imports
    sys.modules['kafka'] = MockKafkaModule()
    sys.modules['kafka.admin'] = MockKafkaAdminModule()
    
    logger.info("Kafka imports patched for embedded Kafka")

# Auto-patch if using embedded Kafka
if Config.USE_EMBEDDED_KAFKA:
    patch_kafka_imports()
    logger.info("Using embedded Kafka adapter")