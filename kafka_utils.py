import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from retrying import retry
import structlog
from config import Config

# Import embedded Kafka adapter if needed
if Config.USE_EMBEDDED_KAFKA:
    from embedded_kafka_adapter import patch_kafka_imports
    patch_kafka_imports()

from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
try:
    from kafka.admin import ConfigResource, ConfigResourceType, NewTopic
except ImportError:
    # For embedded Kafka, NewTopic is just a string
    NewTopic = str
    ConfigResource = str
    ConfigResourceType = str
try:
    from kafka.errors import KafkaError, KafkaTimeoutError
except ImportError:
    # Define basic exceptions for embedded Kafka
    class KafkaError(Exception):
        pass
    class KafkaTimeoutError(KafkaError):
        pass

# Setup structured logging
logger = structlog.get_logger(__name__)

class KafkaConnectionManager:
    """Manages Kafka connections and provides utility methods"""
    
    def __init__(self):
        self.producer = None
        self.admin_client = None
        self._connection_retries = 0
        self.max_connection_retries = 5
    
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer"""
        if self.producer is None:
            try:
                producer_config = Config.get_producer_config()
                # Override serializers for JSON handling
                producer_config['value_serializer'] = lambda v: json.dumps(v).encode('utf-8')
                producer_config['key_serializer'] = lambda k: str(k).encode('utf-8')
                
                self.producer = KafkaProducer(**producer_config)
                logger.info("Kafka producer created successfully")
            except Exception as e:
                logger.error("Failed to create Kafka producer", error=str(e))
                raise
        return self.producer
    
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_consumer(self, topics: List[str], group_id: str) -> KafkaConsumer:
        """Create Kafka consumer with retry logic"""
        try:
            consumer_config = Config.get_consumer_config(group_id)
            # Override deserializers for JSON handling
            consumer_config['value_deserializer'] = lambda m: json.loads(m.decode('utf-8')) if m else None
            consumer_config['key_deserializer'] = lambda m: m.decode('utf-8') if m else None
            
            consumer = KafkaConsumer(
                *topics,
                **consumer_config
            )
            logger.info("Kafka consumer created successfully", topics=topics, group_id=group_id)
            return consumer
        except Exception as e:
            logger.error("Failed to create Kafka consumer", error=str(e), topics=topics, group_id=group_id)
            raise
    
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def get_admin_client(self) -> KafkaAdminClient:
        """Get or create Kafka admin client"""
        if self.admin_client is None:
            try:
                self.admin_client = KafkaAdminClient(
                    bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                    client_id='admin_client'
                )
                logger.info("Kafka admin client created successfully")
            except Exception as e:
                logger.error("Failed to create Kafka admin client", error=str(e))
                raise
        return self.admin_client
    
    def close_connections(self):
        """Close all Kafka connections"""
        if self.producer:
            self.producer.close()
            self.producer = None
        if self.admin_client:
            self.admin_client.close()
            self.admin_client = None
        logger.info("Kafka connections closed")

class MessageProducer:
    """High-level message producer with error handling and monitoring"""
    
    def __init__(self, connection_manager: KafkaConnectionManager):
        self.connection_manager = connection_manager
        self.message_count = 0
        self.error_count = 0
    
    def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None, 
                    correlation_id: Optional[str] = None) -> bool:
        """Send message to Kafka topic with error handling"""
        try:
            # Add metadata to message
            enriched_message = {
                **message,
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id or self._generate_correlation_id()
            }
            
            producer = self.connection_manager.get_producer()
            future = producer.send(topic, value=enriched_message, key=key)
            
            # Wait for message to be sent
            record_metadata = future.get(timeout=10)
            
            self.message_count += 1
            logger.info(
                "Message sent successfully",
                topic=topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                correlation_id=enriched_message['correlation_id']
            )
            return True
            
        except KafkaTimeoutError:
            self.error_count += 1
            logger.error("Timeout sending message to Kafka", topic=topic)
            self._send_to_dlq(topic, message, "timeout_error")
            return False
        except KafkaError as e:
            self.error_count += 1
            logger.error("Kafka error sending message", topic=topic, error=str(e))
            self._send_to_dlq(topic, message, "kafka_error")
            return False
        except Exception as e:
            self.error_count += 1
            logger.error("Unexpected error sending message", topic=topic, error=str(e))
            self._send_to_dlq(topic, message, "unexpected_error")
            return False
    
    def _send_to_dlq(self, original_topic: str, message: Dict[str, Any], error_type: str):
        """Send failed message to Dead Letter Queue"""
        try:
            dlq_message = {
                'original_topic': original_topic,
                'original_message': message,
                'error_type': error_type,
                'failed_at': datetime.utcnow().isoformat()
            }
            
            producer = self.connection_manager.get_producer()
            producer.send(Config.TOPICS['DLQ'], value=dlq_message)
            logger.info("Message sent to DLQ", original_topic=original_topic, error_type=error_type)
        except Exception as e:
            logger.error("Failed to send message to DLQ", error=str(e))
    
    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID"""
        return f"{int(time.time() * 1000)}_{self.message_count}"
    
    def get_metrics(self) -> Dict[str, int]:
        """Get producer metrics"""
        return {
            'messages_sent': self.message_count,
            'errors': self.error_count,
            'success_rate': (self.message_count / (self.message_count + self.error_count)) * 100 if (self.message_count + self.error_count) > 0 else 0
        }

class MessageConsumer:
    """High-level message consumer with error handling and processing"""
    
    def __init__(self, connection_manager: KafkaConnectionManager, topics: List[str], 
                 group_id: str, message_handler: Callable[[Dict[str, Any]], bool]):
        self.connection_manager = connection_manager
        self.topics = topics
        self.group_id = group_id
        self.message_handler = message_handler
        self.consumer = None
        self.running = False
        self.processed_count = 0
        self.error_count = 0
        self.processed_messages = set()  # For deduplication
    
    def start_consuming(self):
        """Start consuming messages"""
        try:
            self.consumer = self.connection_manager.get_consumer(self.topics, self.group_id)
            self.running = True
            
            logger.info("Started consuming messages", topics=self.topics, group_id=self.group_id)
            
            while self.running:
                try:
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            self._process_message(message)
                            
                except Exception as e:
                    logger.error("Error during message consumption", error=str(e))
                    time.sleep(1)  # Brief pause before retrying
                    
        except Exception as e:
            logger.error("Failed to start message consumption", error=str(e))
            raise
    
    def _process_message(self, message):
        """Process individual message with error handling and deduplication"""
        try:
            message_data = message.value
            message_key = message.key
            
            # Extract correlation ID for deduplication
            correlation_id = message_data.get('correlation_id')
            if correlation_id and correlation_id in self.processed_messages:
                logger.info("Duplicate message detected, skipping", correlation_id=correlation_id)
                return
            
            # Process message
            success = self.message_handler(message_data)
            
            if success:
                self.processed_count += 1
                if correlation_id:
                    self.processed_messages.add(correlation_id)
                logger.info(
                    "Message processed successfully",
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                    correlation_id=correlation_id
                )
            else:
                self.error_count += 1
                logger.error(
                    "Message processing failed",
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset
                )
                
        except Exception as e:
            self.error_count += 1
            logger.error("Error processing message", error=str(e))
    
    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Stopped consuming messages", topics=self.topics)
    
    def get_metrics(self) -> Dict[str, int]:
        """Get consumer metrics"""
        return {
            'messages_processed': self.processed_count,
            'errors': self.error_count,
            'success_rate': (self.processed_count / (self.processed_count + self.error_count)) * 100 if (self.processed_count + self.error_count) > 0 else 0
        }

def create_topics_if_not_exist(connection_manager: KafkaConnectionManager):
    """Create Kafka topics if they don't exist"""
    try:
        admin_client = connection_manager.get_admin_client()
        
        # Get existing topics
        existing_topics_result = admin_client.list_topics()
        if hasattr(existing_topics_result, 'topics'):
            existing_topics = existing_topics_result.topics
        else:
            existing_topics = existing_topics_result
        
        # Define topics to create
        topics_to_create = []
        for topic_name in Config.TOPICS.values():
            if topic_name not in existing_topics:
                if Config.USE_EMBEDDED_KAFKA:
                    # For embedded Kafka, just use the topic name
                    topics_to_create.append(topic_name)
                else:
                    topic = NewTopic(
                        name=topic_name,
                        num_partitions=3,
                        replication_factor=1
                    )
                    topics_to_create.append(topic)
        
        if topics_to_create:
            # Create topics
            result = admin_client.create_topics(topics_to_create, validate_only=False)
            
            if Config.USE_EMBEDDED_KAFKA:
                # For embedded Kafka, topics are created immediately
                for topic in topics_to_create:
                    logger.info("Topic created successfully", topic=topic)
            else:
                # Wait for topics to be created
                for topic in topics_to_create:
                    try:
                        logger.info("Topic created successfully", topic=topic.name)
                    except Exception as e:
                        logger.error("Failed to create topic", topic=topic.name, error=str(e))
        else:
            logger.info("All topics already exist")
            
    except Exception as e:
        logger.error("Error creating topics", error=str(e))
        raise

def health_check_kafka(connection_manager: KafkaConnectionManager) -> bool:
    """Check Kafka cluster health"""
    try:
        admin_client = connection_manager.get_admin_client()
        topics = admin_client.list_topics()
        logger.info("Kafka health check passed", topic_count=len(topics))
        return True
    except Exception as e:
        logger.error("Kafka health check failed", error=str(e))
        return False