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

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

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
    def get_producer(self) -> Producer:
        """Get or create Kafka producer"""
        if self.producer is None:
            try:
                producer_config = {
                    'bootstrap.servers': Config.KAFKA_BOOTSTRAP_SERVERS,
                    'client.id': 'ecommerce-producer'
                }
                
                self.producer = Producer(producer_config)
                logger.info("Kafka producer created successfully")
            except Exception as e:
                logger.error("Failed to create Kafka producer", error=str(e))
                raise
        return self.producer
    
    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000)
    def get_consumer(self, topics: List[str], group_id: str) -> Consumer:
        """Create Kafka consumer with retry logic"""
        try:
            consumer_config = {
                'bootstrap.servers': Config.KAFKA_BOOTSTRAP_SERVERS,
                'group.id': group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': True
            }
            
            consumer = Consumer(consumer_config)
            consumer.subscribe(topics)
            logger.info("Kafka consumer created successfully", topics=topics, group_id=group_id)
            return consumer
        except Exception as e:
            logger.error("Failed to create Kafka consumer", error=str(e), topics=topics, group_id=group_id)
            raise
    
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def get_admin_client(self) -> AdminClient:
        """Get or create Kafka admin client"""
        if self.admin_client is None:
            try:
                admin_config = {
                    'bootstrap.servers': Config.KAFKA_BOOTSTRAP_SERVERS
                }
                self.admin_client = AdminClient(admin_config)
                logger.info("Kafka admin client created successfully")
            except Exception as e:
                logger.error("Failed to create Kafka admin client", error=str(e))
                raise
        return self.admin_client
    
    def close_connections(self):
        """Close all Kafka connections"""
        if self.producer:
            self.producer.flush()
            self.producer = None
        if self.admin_client:
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
            
            # Serialize message to JSON
            message_value = json.dumps(enriched_message).encode('utf-8')
            message_key = key.encode('utf-8') if key else None
            
            # Send message
            producer.produce(
                topic=topic,
                value=message_value,
                key=message_key,
                callback=self._delivery_callback
            )
            
            # Wait for message to be delivered
            producer.flush(timeout=10)
            
            self.message_count += 1
            logger.info(
                "Message sent successfully",
                topic=topic,
                correlation_id=enriched_message['correlation_id']
            )
            return True
            
        except KafkaException as e:
            self.error_count += 1
            logger.error("Kafka error sending message", topic=topic, error=str(e))
            self._send_to_dlq(topic, message, "kafka_error")
            return False
        except Exception as e:
            self.error_count += 1
            logger.error("Unexpected error sending message", topic=topic, error=str(e))
            self._send_to_dlq(topic, message, "unexpected_error")
            return False
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            logger.error("Message delivery failed", error=str(err))
        else:
            logger.debug("Message delivered", topic=msg.topic(), partition=msg.partition(), offset=msg.offset())
    
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
            dlq_value = json.dumps(dlq_message).encode('utf-8')
            producer.produce(topic=Config.TOPICS['DLQ'], value=dlq_value)
            producer.flush()
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
                    msg = self.consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            logger.error("Consumer error", error=str(msg.error()))
                            continue
                    
                    self._process_message(msg)
                            
                except Exception as e:
                    logger.error("Error during message consumption", error=str(e))
                    time.sleep(1)  # Brief pause before retrying
                    
        except Exception as e:
            logger.error("Failed to start message consumption", error=str(e))
            raise
    
    def _process_message(self, msg):
        """Process individual message with error handling and deduplication"""
        try:
            # Deserialize message
            message_data = json.loads(msg.value().decode('utf-8'))
            message_key = msg.key().decode('utf-8') if msg.key() else None
            
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
                    topic=msg.topic(),
                    partition=msg.partition(),
                    offset=msg.offset(),
                    correlation_id=correlation_id
                )
            else:
                self.error_count += 1
                logger.error(
                    "Message processing failed",
                    topic=msg.topic(),
                    partition=msg.partition(),
                    offset=msg.offset()
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
        metadata = admin_client.list_topics(timeout=10)
        existing_topics = set(metadata.topics.keys())
        
        # Define topics to create
        topics_to_create = []
        for topic_name in Config.TOPICS.values():
            if topic_name not in existing_topics:
                topic = NewTopic(
                    topic=topic_name,
                    num_partitions=3,
                    replication_factor=1
                )
                topics_to_create.append(topic)
        
        if topics_to_create:
            # Create topics
            fs = admin_client.create_topics(topics_to_create)
            
            # Wait for topics to be created
            for topic, f in fs.items():
                try:
                    f.result()  # The result itself is None
                    logger.info("Topic created successfully", topic=topic)
                except Exception as e:
                    logger.error("Failed to create topic", topic=topic, error=str(e))
        else:
            logger.info("All topics already exist")
            
    except Exception as e:
        logger.error("Error creating topics", error=str(e))
        raise

def health_check_kafka(connection_manager: KafkaConnectionManager) -> bool:
    """Check Kafka cluster health"""
    try:
        admin_client = connection_manager.get_admin_client()
        metadata = admin_client.list_topics(timeout=10)
        logger.info("Kafka health check passed", topic_count=len(metadata.topics))
        return True
    except Exception as e:
        logger.error("Kafka health check failed", error=str(e))
        return False