# Kafka E-commerce Order Processing System

A comprehensive, production-ready e-commerce order processing system built with Apache Kafka, demonstrating event-driven architecture, microservices patterns, and distributed system best practices.

## 🏗️ Architecture Overview

This system implements a complete order processing workflow using event-driven architecture with the following components:

### Core Services
- **Order Service** (Port 5011): Manages order lifecycle and validation
- **Payment Service** (Port 6002): Handles payment processing with success/failure simulation
- **Inventory Service** (Port 5003): Manages stock levels, reservations, and releases
- **Notification Service** (Port 5004): Sends customer notifications via multiple channels
- **Order Orchestrator** (Port 5005): Coordinates the complete order processing flow
- **Monitoring Service** (Port 5005): Provides system health monitoring and metrics

### Event Flow
```
Order Created → Order Validation → Payment Processing → Inventory Reservation → Order Completion → Notifications
```

### Kafka Topics
- `orders.created` - New order events
- `orders.validated` - Order validation events
- `orders.completed` - Successfully completed orders
- `orders.failed` - Failed order events
- `payments.requested` - Payment processing requests
- `payments.completed` - Successful payment events
- `payments.failed` - Failed payment events
- `inventory.reserved` - Inventory reservation events
- `inventory.released` - Inventory release events
- `notifications.email` - Email notification events
- `dead.letter.queue` - Failed message handling

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Docker and Docker Compose (for Kafka infrastructure)
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd kafka-ecommerce

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

#### For Development (Default)
```bash
# Copy environment template
cp .env.example .env

# Edit .env file for development (optional - defaults work)
# ENVIRONMENT=development
# DEBUG=true
# LOG_LEVEL=DEBUG
```

#### For Production
```bash
# Copy environment template
cp .env.example .env

# Edit .env file for production
echo "ENVIRONMENT=production" > .env
echo "DEBUG=false" >> .env
echo "LOG_LEVEL=INFO" >> .env
# Add other production configurations as needed
```

### 3. Start Kafka Infrastructure
```bash
# Start Kafka, Zookeeper, and Kafka UI
docker-compose up -d

# Wait for Kafka to be ready (about 30 seconds)
docker-compose logs kafka
```

### 4. Start the System

#### Option A: Complete System (Recommended)
```bash
# Start all services with automatic health checks and dependency management
python main.py
```

#### Option B: Individual Services (Advanced)
```bash
# Terminal 1: Order Service
python order_service.py

# Terminal 2: Payment Service
python payment_service.py

# Terminal 3: Inventory Service
python inventory_service.py

# Terminal 4: Notification Service
python notification_service.py

# Terminal 5: Order Orchestrator
python order_orchestrator.py

# Terminal 6: Monitoring Service
python monitoring_service.py
```

### 5. Verify System Health
```bash
# Check individual service health
curl http://localhost:5011/health  # Order Service
curl http://localhost:6002/health  # Payment Service
curl http://localhost:5003/health  # Inventory Service
curl http://localhost:5004/health  # Notification Service
curl http://localhost:5005/health  # Orchestrator & Monitoring

# Visit the monitoring dashboard
open http://localhost:5005

# Check system status
python main.py --status

# Run integration tests
python test_suite.py
```

## 📊 System Endpoints

### Service Health Checks
- Order Service: http://localhost:5011/health
- Payment Service: http://localhost:6002/health
- Inventory Service: http://localhost:5003/health
- Notification Service: http://localhost:5004/health
- Order Orchestrator: http://localhost:5005/health
- Monitoring Service: http://localhost:5005/health

### Management Dashboards
- **Monitoring Dashboard**: http://localhost:5005/dashboard
- **Order Flow Tracking**: http://localhost:5005/flows
- **Kafka UI**: http://localhost:8080
- **Prometheus Metrics**: http://localhost:5005/metrics/prometheus

### API Endpoints

#### Order Service (Port 5011)
```bash
# Create order
POST /orders
{
  "customer_id": "customer_123",
  "items": [
    {"product_id": "laptop", "quantity": 1, "price": 999.99}
  ],
  "total_amount": 999.99
}

# Get order status
GET /orders/{order_id}

# List orders
GET /orders
```

#### Payment Service (Port 6002)
```bash
# Process payment
POST /payments
{
  "order_id": "order_123",
  "amount": 999.99,
  "payment_method": "credit_card"
}

# Get payment status
GET /payments/{payment_id}
```

#### Inventory Service (Port 5003)
```bash
# Check inventory
GET /inventory

# Make reservation
POST /reservations
{
  "order_id": "order_123",
  "items": [{"product_id": "laptop", "quantity": 1}]
}

# Release reservation
DELETE /reservations/{reservation_id}
```

#### Notification Service (Port 5004)
```bash
# Send notification
POST /notifications
{
  "customer_id": "customer_123",
  "type": "order_confirmation",
  "message": "Your order has been confirmed"
}

# Get notification status
GET /notifications/{notification_id}
```

## 🧪 Testing

### Automated Testing

#### Run All Tests
```bash
# Run complete test suite
python -m pytest tests/ -v --tb=short

# Run tests with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

#### Run Specific Test Suites
```bash
# Infrastructure tests
python -m pytest tests/test_kafka_integration.py -v
python -m pytest tests/test_service_health.py -v

# Business logic tests
python -m pytest tests/test_order_flow.py -v
python -m pytest tests/test_payment_processing.py -v
python -m pytest tests/test_inventory_management.py -v
python -m pytest tests/test_notification_delivery.py -v

# System tests
python -m pytest tests/test_monitoring.py -v
python -m pytest tests/test_integration.py -v
```

#### Performance Testing
```bash
# Load testing
python tests/load_test.py --orders=100 --concurrent=10

# Stress testing
python tests/stress_test.py --duration=300 --rps=50
```

### Manual Testing

#### Test Complete Order Flow
```bash
# 1. Create order
ORDER_ID=$(curl -s -X POST http://localhost:5011/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_customer",
    "items": [{"product_id": "laptop_001", "quantity": 1, "price": 999.99}],
    "total_amount": 999.99,
    "customer_email": "test@example.com"
  }' | jq -r '.order_id')

# 2. Track order processing
watch -n 2 "curl -s http://localhost:5011/orders/$ORDER_ID | jq '.status'"

# 3. Check system events
curl http://localhost:5005/orders/$ORDER_ID/events
```

#### Test Failure Scenarios
```bash
# Test insufficient inventory
curl -X POST http://localhost:5011/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test_customer",
    "items": [{"product_id": "rare_item", "quantity": 1000, "price": 99.99}],
    "total_amount": 99990.00
  }'

# Test payment failure
curl -X POST http://localhost:6002/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test_order",
    "amount": 999999.99,
    "payment_method": "credit_card",
    "card_details": {"number": "4000000000000002"}
  }'
```

### Test Coverage
- **Infrastructure**: Kafka connectivity, service health, dependency management
- **Business Logic**: Order validation, payment processing, inventory management
- **Integration**: End-to-end workflows, service communication, event handling
- **Failure Handling**: Service failures, network issues, timeout scenarios
- **Performance**: Load testing, concurrent processing, resource utilization
- **Security**: Input validation, error handling, data sanitization

## 📈 Monitoring and Observability

### Built-in Monitoring
- **Service Health Monitoring**: Automatic health checks for all services
- **Kafka Message Tracking**: Monitor message flow across all topics
- **Order Processing Metrics**: Track order completion rates and processing times
- **Error Rate Monitoring**: Alert on high error rates
- **Performance Metrics**: Response times and throughput monitoring

### Prometheus Metrics
The system exposes Prometheus-compatible metrics:
```bash
curl http://localhost:5006/metrics/prometheus
```

### Alerts
The monitoring service automatically generates alerts for:
- Service downtime
- High error rates
- Slow response times
- Processing timeouts

## 🔧 Configuration

All configuration is centralized in `config.py`:

```python
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

# Service Ports
ORDER_SERVICE_PORT = 5001
PAYMENT_SERVICE_PORT = 5002
# ... etc

# Processing Timeouts
ORDER_PROCESSING_TIMEOUT = 300  # 5 minutes
PAYMENT_PROCESSING_TIMEOUT = 60  # 1 minute

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF_MS = 1000
```

## 🚀 Deployment

### Development Deployment
```bash
# 1. Clone and setup
git clone <repository-url>
cd kafka-ecommerce
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env for development settings

# 3. Start infrastructure
docker-compose up -d

# 4. Start application
python main.py
```

### Production Deployment

#### Using Docker
```bash
# 1. Build production image
docker build -t kafka-ecommerce:latest .

# 2. Run with production configuration
docker run -d \
  --name kafka-ecommerce \
  --env-file .env.production \
  -p 5011:5011 \
  -p 6002:6002 \
  -p 5003:5003 \
  -p 5004:5004 \
  -p 5005:5005 \
  kafka-ecommerce:latest
```

#### Using Docker Compose (Production)
```bash
# 1. Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# 2. Scale services as needed
docker-compose -f docker-compose.prod.yml up -d --scale order-service=3
```

#### Cloud Deployment (AWS/GCP/Azure)
```bash
# 1. Configure cloud-specific settings in .env
KAFKA_BOOTSTRAP_SERVERS=your-managed-kafka-cluster:9092
DATABASE_URL=your-managed-database-url
REDIS_URL=your-managed-redis-url

# 2. Deploy using your preferred method:
# - Kubernetes
# - ECS/Fargate
# - Google Cloud Run
# - Azure Container Instances
```

### Environment-Specific Configuration

#### Development (.env)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

#### Staging (.env.staging)
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
KAFKA_BOOTSTRAP_SERVERS=staging-kafka:9092
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
KAFKA_BOOTSTRAP_SERVERS=prod-kafka-cluster:9092
SSL_ENABLED=true
MONITORING_ENABLED=true
```

## 🔧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check if Kafka is running
docker ps | grep kafka

# Check service logs
python main.py --logs

# Check individual service health
curl http://localhost:5011/health
```

#### Port Conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep :5011

# Kill conflicting processes
sudo kill -9 <PID>

# Or change ports in .env
ORDER_SERVICE_PORT=5021
```

#### Kafka Connection Issues
```bash
# Test Kafka connectivity
python -c "from confluent_kafka import Producer; Producer({'bootstrap.servers': 'localhost:9092'})"

# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Reset Kafka (development only)
docker-compose down -v
docker-compose up -d
```

#### Memory Issues
```bash
# Check system resources
free -h
df -h

# Reduce service memory usage
export KAFKA_HEAP_OPTS="-Xmx512M -Xms512M"

# Monitor service memory
ps aux | grep python
```

### Performance Optimization

#### Kafka Optimization
```bash
# Increase Kafka performance
export KAFKA_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=20"

# Tune producer settings
KAFKA_BATCH_SIZE=32768
KAFKA_LINGER_MS=5
KAFKA_COMPRESSION_TYPE=snappy
```

#### Service Optimization
```bash
# Use production WSGI server
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5011 order_service:app

# Enable connection pooling
CONNECTION_POOL_SIZE=20
CONNECTION_POOL_MAX_OVERFLOW=30
```

## 🔒 Security Considerations

### Production Security
- Enable SSL/TLS for all service communication
- Use API keys for service authentication
- Implement rate limiting
- Enable audit logging
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Regular security updates

### Configuration Security
```bash
# Use environment variables for secrets
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}
DATABASE_PASSWORD=${DATABASE_PASSWORD}

# Never commit secrets to version control
echo ".env*" >> .gitignore
echo "secrets/" >> .gitignore
```

## 🏃‍♂️ Demo Scenarios

### Happy Path - Successful Order
```bash
# 1. Create order
curl -X POST http://localhost:5011/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo_customer",
    "items": [{"product_id": "laptop", "quantity": 1, "price": 999.99}],
    "total_amount": 999.99
  }'

# 2. Track order progress
curl http://localhost:5011/orders/{order_id}

# 3. View orchestration flow
curl http://localhost:5005/flows/{order_id}
```

### Failure Scenario - Insufficient Inventory
```bash
# Create order with excessive quantity
curl -X POST http://localhost:5011/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "demo_customer",
    "items": [{"product_id": "laptop", "quantity": 1000, "price": 999.99}],
    "total_amount": 999990.00
  }'
```

### Payment Failure Scenario
```bash
# Create payment with invalid amount
curl -X POST http://localhost:6002/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "test_order",
    "amount": -100.00,
    "payment_method": "credit_card"
  }'
```

## 🛠️ Development

### Project Structure
```
kafka-ecommerce/
├── main.py                    # System launcher
├── config.py                  # Configuration management
├── kafka_utils.py             # Kafka utilities
├── order_service.py           # Order management service
├── payment_service.py         # Payment processing service
├── inventory_service.py       # Inventory management service
├── notification_service.py    # Notification service
├── order_orchestrator.py      # Order flow orchestration
├── monitoring_service.py      # System monitoring
├── test_suite.py             # Comprehensive test suite
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Kafka infrastructure
└── README.md                 # This file
```

### Adding New Services
1. Create service file following the existing pattern
2. Add service configuration to `config.py`
3. Update `main.py` to include the new service
4. Add health check endpoint
5. Add tests to `test_suite.py`

### Message Schema
All Kafka messages follow a consistent schema:
```json
{
  "order_id": "uuid",
  "customer_id": "string",
  "timestamp": "ISO8601",
  "status": "string",
  "data": {},
  "metadata": {}
}
```

## 🔍 Troubleshooting

### Common Issues

**Kafka Connection Errors**
```bash
# Check Kafka status
docker-compose ps
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka
```

**Service Startup Failures**
```bash
# Check service logs
python main.py --service order_service

# Check port conflicts
netstat -an | grep :5001
```

**Test Failures**
```bash
# Run tests with verbose output
pytest test_suite.py -v --tb=long

# Check service health before testing
python main.py --status
```

### Performance Tuning

**Kafka Configuration**
- Adjust `num.partitions` for higher throughput
- Tune `batch.size` and `linger.ms` for producers
- Configure `fetch.min.bytes` for consumers

**Service Configuration**
- Adjust worker threads in Flask applications
- Tune connection pool sizes
- Configure appropriate timeouts

## 📋 Success Criteria

### Functional Requirements ✅
- [x] Complete order processing workflow
- [x] Event-driven architecture with Kafka
- [x] Microservices with clear boundaries
- [x] Error handling and failure scenarios
- [x] Data consistency across services

### Technical Requirements ✅
- [x] Kafka integration with proper topics
- [x] RESTful APIs for all services
- [x] Comprehensive logging
- [x] Health checks and monitoring
- [x] Configuration management

### Testing Requirements ✅
- [x] Integration tests
- [x] Kafka connectivity tests
- [x] Performance tests
- [x] Failure scenario tests
- [x] End-to-end workflow tests

### Documentation Requirements ✅
- [x] Complete setup instructions
- [x] API documentation
- [x] Architecture overview
- [x] Troubleshooting guide
- [x] Demo scenarios

## 📊 System Metrics & Monitoring

### Built-in Monitoring Features
- **Real-time Dashboards**: Order flow visualization and system health
- **Prometheus Metrics**: Custom metrics for all services
- **Health Checks**: Comprehensive service health monitoring
- **Event Tracking**: Complete audit trail of all system events
- **Performance Metrics**: Latency, throughput, and error rate monitoring
- **Alerting**: Configurable alerts for system anomalies

### Key Performance Indicators
- **Order Processing Time**: Average time from order creation to completion
- **Payment Success Rate**: Percentage of successful payment transactions
- **Inventory Accuracy**: Real-time inventory vs actual stock levels
- **Notification Delivery Rate**: Percentage of successfully delivered notifications
- **System Uptime**: Overall system availability
- **Throughput**: Orders processed per minute/hour
- **Error Rate**: Percentage of failed transactions
- **Resource Utilization**: CPU, memory, and network usage

### Monitoring Endpoints
```bash
# Service health
GET /health - Service health status
GET /health/detailed - Detailed health information

# Metrics
GET /metrics - Prometheus-compatible metrics
GET /metrics/custom - Application-specific metrics

# Status and performance
GET /status - Detailed service status
GET /performance - Performance metrics
GET /events - Recent system events
```

## 🔄 Switching Between Environments

### Quick Environment Switch
```bash
# Switch to development
echo "ENVIRONMENT=development" > .env
python main.py

# Switch to production
echo "ENVIRONMENT=production" > .env
echo "DEBUG=false" >> .env
echo "LOG_LEVEL=INFO" >> .env
python main.py
```

### Environment-Specific Features

#### Development Mode
- Enhanced logging and debugging
- Hot reload capabilities
- Test data generation
- Relaxed security settings
- Local Kafka instance

#### Production Mode
- Optimized performance settings
- Enhanced security measures
- Comprehensive monitoring
- Error tracking and alerting
- External service integrations

## 📚 Additional Resources

### Documentation
- [API Documentation](docs/api.md) - Complete API reference
- [Architecture Guide](docs/architecture.md) - System design and patterns
- [Deployment Guide](docs/deployment.md) - Production deployment strategies
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

### Learning Resources
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Event-Driven Architecture Patterns](https://microservices.io/patterns/data/event-driven-architecture.html)
- [Microservices Best Practices](https://microservices.io/)

## 🤝 Contributing

### Development Setup
```bash
# 1. Fork and clone the repository
git clone https://github.com/your-username/kafka-ecommerce.git
cd kafka-ecommerce

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install development dependencies
pip install -r requirements-dev.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests
python -m pytest tests/
```

### Contribution Guidelines
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Add type hints
- Include docstrings

### Reporting Issues
When reporting issues, please include:
- System information (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs and error messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Getting Help
- **Documentation**: Check this README and docs/ folder
- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Email**: Contact the development team at [support@example.com]

### Commercial Support
For enterprise support, custom development, or consulting services, please contact our team.

---

## 🎯 Project Status

### Current Version: 1.0.0
- ✅ Core order processing functionality
- ✅ Payment processing with simulation
- ✅ Inventory management
- ✅ Notification system
- ✅ Monitoring and observability
- ✅ Comprehensive testing
- ✅ Production-ready deployment

### Roadmap
- 🔄 Enhanced security features
- 🔄 Advanced analytics and reporting
- 🔄 Multi-tenant support
- 🔄 GraphQL API
- 🔄 Mobile app integration
- 🔄 Machine learning recommendations

### Changelog
See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

**Built with ❤️ using Apache Kafka, Python, and modern microservices architecture.**