# Complete Prompt: Real-Time E-Commerce Order Processing System with Kafka in Python

## Project Overview
Build a distributed, event-driven e-commerce order processing system using Apache Kafka and Python. The system will demonstrate real-time message processing, event choreography, and microservices communication patterns.

## Architecture Requirements

### Core Components
1. **Order Service** - Handles order creation and validation
2. **Payment Service** - Processes payments and handles failures
3. **Inventory Service** - Manages stock levels and reservations
4. **Notification Service** - Sends customer notifications
5. **Order Orchestrator** - Coordinates the entire order flow

### Kafka Topics Structure
```
orders.created        - New order events
orders.validated      - Validated orders ready for processing
payments.requested    - Payment processing requests
payments.completed    - Successful payments
payments.failed       - Failed payment attempts
inventory.reserved    - Stock reservation events
inventory.released    - Stock release events
notifications.email   - Email notification queue
orders.completed      - Successfully completed orders
orders.failed         - Failed order processing
```

## Technical Specifications

### Message Schema (JSON)
```json
// Order Event
{
  "order_id": "string",
  "customer_id": "string", 
  "items": [{"product_id": "string", "quantity": int, "price": float}],
  "total_amount": float,
  "timestamp": "ISO8601",
  "status": "string"
}

// Payment Event
{
  "order_id": "string",
  "payment_id": "string",
  "amount": float,
  "payment_method": "string",
  "status": "string",
  "timestamp": "ISO8601"
}

// Inventory Event
{
  "product_id": "string",
  "quantity_reserved": int,
  "order_id": "string",
  "timestamp": "ISO8601"
}
```

### Implementation Requirements

1. **Error Handling & Resilience**
   - Dead Letter Queue (DLQ) for failed messages
   - Retry mechanisms with exponential backoff
   - Circuit breaker pattern for external services
   - Idempotent message processing

2. **Data Consistency**
   - At-least-once delivery guarantee
   - Message deduplication using order_id
   - Event sourcing for order state tracking

3. **Monitoring & Observability**
   - Structured logging with correlation IDs
   - Metrics collection (processed messages, errors, latency)
   - Health check endpoints

4. **Configuration Management**
   - Environment-based configuration
   - Kafka broker connection settings
   - Service-specific parameters

## Deliverables

### 1. Core Services (Python files)
- `order_service.py` - Order creation and validation
- `payment_service.py` - Payment processing logic
- `inventory_service.py` - Stock management
- `notification_service.py` - Customer notifications
- `order_orchestrator.py` - End-to-end order coordination

### 2. Infrastructure Files
- `docker-compose.yml` - Kafka cluster setup
- `requirements.txt` - Python dependencies
- `config.py` - Application configuration
- `kafka_utils.py` - Kafka connection utilities

### 3. Testing Suite
- `test_integration.py` - End-to-end order flow tests
- `test_services.py` - Unit tests for each service
- `test_kafka_connectivity.py` - Kafka connection tests
- `load_test.py` - Performance testing script

### 4. Utilities & Scripts
- `create_topics.py` - Kafka topic creation script
- `data_generator.py` - Sample order data generator
- `monitor.py` - Real-time system monitoring
- `reset_system.py` - Clean slate for testing

### 5. Documentation
- `README.md` - Setup and usage instructions
- `ARCHITECTURE.md` - System design documentation
- `API_SPEC.md` - Service interfaces and message formats

## Comprehensive Test Suite

### 1. Integration Tests
```python
# Test complete order flow
def test_successful_order_flow():
    # Place order → Validate → Process payment → Reserve inventory → Send notification
    
def test_payment_failure_flow():
    # Place order → Payment fails → Release inventory → Send failure notification
    
def test_inventory_shortage_flow():
    # Place order → Insufficient stock → Cancel order → Refund → Notify customer
```

### 2. Kafka Connectivity Tests
- Producer connection and message sending
- Consumer group functionality
- Topic creation and configuration
- Message serialization/deserialization

### 3. Performance Tests
- Concurrent order processing (100 orders/second)
- Message throughput and latency measurement
- System behavior under load
- Resource utilization monitoring

### 4. Failure Scenario Tests
- Kafka broker downtime simulation
- Service crash and recovery
- Network partition handling
- Message corruption scenarios

## Demo Scenarios

### Scenario 1: Happy Path
1. Customer places order for 2 items
2. Order validation succeeds
3. Payment processes successfully
4. Inventory reserved for items
5. Confirmation email sent
6. Order marked as completed

### Scenario 2: Payment Failure
1. Customer places order
2. Payment processing fails
3. Inventory reservation released
4. Failure notification sent
5. Order marked as failed

### Scenario 3: Inventory Shortage
1. Customer orders out-of-stock item
2. Inventory service rejects reservation
3. Payment refunded if already processed
4. Customer notified of unavailability

## Success Criteria

### Functional Requirements ✅
- [ ] All services can produce and consume Kafka messages
- [ ] Complete order flow executes successfully
- [ ] Error scenarios are handled gracefully
- [ ] Messages are properly formatted and validated
- [ ] System maintains data consistency

### Technical Requirements ✅
- [ ] Kafka cluster runs via Docker Compose
- [ ] All topics are created automatically
- [ ] Services can recover from failures
- [ ] Dead letter queues capture failed messages
- [ ] Comprehensive logging is implemented

### Testing Requirements ✅
- [ ] Integration tests pass for all scenarios
- [ ] Unit tests cover service logic
- [ ] Performance tests demonstrate throughput
- [ ] Failure tests validate resilience
- [ ] Test coverage > 80%

### Documentation Requirements ✅
- [ ] Setup instructions are clear and complete
- [ ] Architecture diagram included
- [ ] API documentation is comprehensive
- [ ] Demo scenarios are documented
- [ ] Troubleshooting guide provided

## Development Stack
```
Language: Python 3.8+
Kafka Client: kafka-python
Web Framework: Flask (for health checks)
Testing: pytest, pytest-asyncio
Containerization: Docker & Docker Compose
Data Format: JSON
Logging: structlog
Configuration: python-dotenv
Metrics: prometheus-client
```

This comprehensive system will demonstrate mastery of event-driven architecture, Kafka messaging patterns, microservices design, and production-ready Python development practices.