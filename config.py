import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Environment Configuration
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, production
    DEBUG = os.getenv('DEBUG', 'true' if ENVIRONMENT == 'development' else 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if ENVIRONMENT == 'development' else 'INFO')
    
    # Kafka Configuration (Using Embedded Kafka)
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'ecommerce-system')
    KAFKA_ACKS = os.getenv('KAFKA_ACKS', 'all')
    KAFKA_RETRIES = int(os.getenv('KAFKA_RETRIES', '3'))
    KAFKA_BATCH_SIZE = int(os.getenv('KAFKA_BATCH_SIZE', '16384'))
    KAFKA_LINGER_MS = int(os.getenv('KAFKA_LINGER_MS', '10'))
    KAFKA_BUFFER_MEMORY = int(os.getenv('KAFKA_BUFFER_MEMORY', '33554432'))
    KAFKA_AUTO_OFFSET_RESET = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'latest')
    KAFKA_ENABLE_AUTO_COMMIT = os.getenv('KAFKA_ENABLE_AUTO_COMMIT', 'True').lower() == 'true'
    KAFKA_AUTO_COMMIT_INTERVAL_MS = int(os.getenv('KAFKA_AUTO_COMMIT_INTERVAL_MS', '1000'))
    KAFKA_SESSION_TIMEOUT_MS = int(os.getenv('KAFKA_SESSION_TIMEOUT_MS', '30000'))
    KAFKA_HEARTBEAT_INTERVAL_MS = int(os.getenv('KAFKA_HEARTBEAT_INTERVAL_MS', '3000'))
    KAFKA_MAX_POLL_RECORDS = int(os.getenv('KAFKA_MAX_POLL_RECORDS', '500'))
    KAFKA_REQUEST_TIMEOUT_MS = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '40000'))
    
    # Embedded Kafka REST API
    EMBEDDED_KAFKA_URL = os.getenv('EMBEDDED_KAFKA_URL', 'http://localhost:9092')
    USE_EMBEDDED_KAFKA = os.getenv('USE_EMBEDDED_KAFKA', 'false').lower() == 'true'
    
    # Topic Configuration
    TOPICS = {
        'ORDERS_CREATED': 'orders.created',
        'ORDERS_VALIDATED': 'orders.validated',
        'PAYMENTS_REQUESTED': 'payments.requested',
        'PAYMENTS_COMPLETED': 'payments.completed',
        'PAYMENTS_FAILED': 'payments.failed',
        'INVENTORY_RESERVED': 'inventory.reserved',
        'INVENTORY_RELEASED': 'inventory.released',
        'NOTIFICATIONS_EMAIL': 'notifications.email',
        'ORDERS_COMPLETED': 'orders.completed',
        'ORDERS_FAILED': 'orders.failed',
        'DLQ': 'dead.letter.queue'
    }
    
    # Service Configuration
    ORDER_SERVICE_PORT = int(os.getenv('ORDER_SERVICE_PORT', '5011'))
    PAYMENT_SERVICE_PORT = int(os.getenv('PAYMENT_SERVICE_PORT', '6002'))
    INVENTORY_SERVICE_PORT = int(os.getenv('INVENTORY_SERVICE_PORT', '5003'))
    NOTIFICATION_SERVICE_PORT = int(os.getenv('NOTIFICATION_SERVICE_PORT', '5004'))
    ORCHESTRATOR_SERVICE_PORT = int(os.getenv('ORCHESTRATOR_SERVICE_PORT', '5005'))
    
    # Consumer Group IDs
    CONSUMER_GROUPS = {
        'ORDER_SERVICE': 'order-service-group',
        'PAYMENT_SERVICE': 'payment-service-group',
        'INVENTORY_SERVICE': 'inventory-service-group',
        'NOTIFICATION_SERVICE': 'notification-service-group',
        'ORCHESTRATOR_SERVICE': 'orchestrator-service-group',
        'MONITORING_SERVICE': 'monitoring-service-group'
    }
    
    # Retry Configuration
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_BACKOFF_MS = int(os.getenv('RETRY_BACKOFF_MS', '1000'))
    RETRY_BACKOFF_MULTIPLIER = float(os.getenv('RETRY_BACKOFF_MULTIPLIER', '2.0'))
    
    # Circuit Breaker Configuration
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60'))
    
    # Order Processing Settings
    PAYMENT_PROCESSING_TIMEOUT = int(os.getenv('PAYMENT_PROCESSING_TIMEOUT', '60'))  # 1 minute
    INVENTORY_RESERVATION_TIMEOUT = int(os.getenv('INVENTORY_RESERVATION_TIMEOUT', '30'))  # 30 seconds
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    
    # Database Configuration (for inventory and order state)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ecommerce.db')
    
    # External Service URLs
    PAYMENT_GATEWAY_URL = os.getenv('PAYMENT_GATEWAY_URL', 'https://api.payment-gateway.com')
    EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL', 'https://api.email-service.com')
    
    # Monitoring Configuration
    METRICS_PORT = int(os.getenv('METRICS_PORT', '8090'))
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '15'))  # Reduced for faster detection
    METRICS_COLLECTION_INTERVAL = int(os.getenv('METRICS_COLLECTION_INTERVAL', '60'))
    ALERT_RETENTION_DAYS = int(os.getenv('ALERT_RETENTION_DAYS', '7'))
    MONITORING_SERVICE_PORT = int(os.getenv('MONITORING_SERVICE_PORT', '5005'))  # Fixed port conflict
    
    # Service Startup Configuration
    SERVICE_STARTUP_TIMEOUT = int(os.getenv('SERVICE_STARTUP_TIMEOUT', '60'))  # Increased timeout
    SERVICE_READINESS_CHECK_INTERVAL = int(os.getenv('SERVICE_READINESS_CHECK_INTERVAL', '2'))  # Check every 2 seconds
    SERVICE_HEALTH_CHECK_TIMEOUT = int(os.getenv('SERVICE_HEALTH_CHECK_TIMEOUT', '10'))  # Health check timeout
    
    # Inter-service Communication
    SERVICE_REQUEST_TIMEOUT = int(os.getenv('SERVICE_REQUEST_TIMEOUT', '30'))  # Request timeout between services
    SERVICE_RETRY_ATTEMPTS = int(os.getenv('SERVICE_RETRY_ATTEMPTS', '3'))  # Retry attempts for service calls
    SERVICE_RETRY_DELAY = int(os.getenv('SERVICE_RETRY_DELAY', '2'))  # Delay between retries
    
    # Performance Configuration
    MAX_CONCURRENT_ORDERS = int(os.getenv('MAX_CONCURRENT_ORDERS', '100'))
    ORDER_PROCESSING_TIMEOUT = int(os.getenv('ORDER_PROCESSING_TIMEOUT', '300'))
    
    @classmethod
    def get_kafka_config(cls):
        """Get Kafka configuration dictionary for confluent-kafka"""
        return {
            'bootstrap.servers': cls.KAFKA_BOOTSTRAP_SERVERS,
            'auto.offset.reset': cls.KAFKA_AUTO_OFFSET_RESET,
            'enable.auto.commit': cls.KAFKA_ENABLE_AUTO_COMMIT,
            'auto.commit.interval.ms': cls.KAFKA_AUTO_COMMIT_INTERVAL_MS,
            'session.timeout.ms': cls.KAFKA_SESSION_TIMEOUT_MS,
            'heartbeat.interval.ms': cls.KAFKA_HEARTBEAT_INTERVAL_MS,
            'max.poll.records': cls.KAFKA_MAX_POLL_RECORDS,
            'request.timeout.ms': cls.KAFKA_REQUEST_TIMEOUT_MS
        }
    
    @classmethod
    def get_producer_config(cls):
        """Get Kafka producer configuration for confluent-kafka"""
        return {
            'bootstrap.servers': cls.KAFKA_BOOTSTRAP_SERVERS,
            'acks': 'all',
            'retries': cls.MAX_RETRIES,
            'retry.backoff.ms': cls.RETRY_BACKOFF_MS,
            'request.timeout.ms': cls.KAFKA_REQUEST_TIMEOUT_MS
        }
    
    @classmethod
    def get_consumer_config(cls, group_id):
        """Get Kafka consumer configuration for confluent-kafka"""
        config = cls.get_kafka_config()
        config.update({
            'group.id': group_id
        })
        return config
    
    @classmethod
    def get_cors_origins(cls):
        """Get CORS origins configuration for frontend integration"""
        cors_origins_env = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        
        # Parse comma-separated origins
        origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
        
        # Add default development origins if not in production
        if cls.ENVIRONMENT != 'production':
            dev_origins = ['http://localhost:3000', 'http://127.0.0.1:3000']
            for origin in dev_origins:
                if origin not in origins:
                    origins.append(origin)
        
        return origins