# Render Deployment Guide for Kafka E-commerce Backend

This guide provides step-by-step instructions for deploying the Kafka E-commerce backend to Render.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push your code to GitHub
3. **External Services**: Set up required external services

## Required External Services

### 1. Kafka Service
Render doesn't provide managed Kafka. Use one of these options:
- **Confluent Cloud** (Recommended) - See detailed setup below
- **Upstash Kafka**
- **AWS MSK**
- **CloudKarafka**

## Confluent Cloud Setup (Recommended)

Confluent Cloud provides a fully managed Apache Kafka service that's perfect for production deployments. Here's how to set it up for this project:

### Step 1: Create Confluent Cloud Account

1. **Sign up**: Go to [confluent.cloud](https://confluent.cloud) and create an account
2. **Choose plan**: Start with the "Basic" plan (free tier available)
3. **Verify email**: Complete email verification

### Step 2: Create Kafka Cluster

1. **Create cluster**:
   ```bash
   # Login to Confluent Cloud
   confluent login
   
   # Create a new cluster
   confluent kafka cluster create kafka-ecommerce \
     --cloud aws \
     --region us-east-1 \
     --type basic
   ```

2. **Or via Web Console**:
   - Click "Create cluster"
   - Choose "Basic" cluster type
   - Select cloud provider (AWS recommended)
   - Choose region closest to your Render deployment
   - Name: `kafka-ecommerce`

### Step 3: Create API Keys

1. **Create cluster API key**:
   ```bash
   # Create API key for the cluster
   confluent api-key create --resource <cluster-id>
   ```

2. **Or via Web Console**:
   - Go to "API Keys" tab in your cluster
   - Click "Create key"
   - Choose "Global access"
   - Save the API Key and Secret securely

### Step 4: Create Required Topics

Create all the topics needed for the e-commerce system:

#### Option A: Using CLI
```bash
# Set your cluster as current
confluent kafka cluster use <cluster-id>

# Create topics
confluent kafka topic create orders.created --partitions 3 --replication-factor 3
confluent kafka topic create orders.validated --partitions 3 --replication-factor 3
confluent kafka topic create orders.completed --partitions 3 --replication-factor 3
confluent kafka topic create orders.failed --partitions 3 --replication-factor 3
confluent kafka topic create payments.requested --partitions 3 --replication-factor 3
confluent kafka topic create payments.completed --partitions 3 --replication-factor 3
confluent kafka topic create payments.failed --partitions 3 --replication-factor 3
confluent kafka topic create inventory.reserved --partitions 3 --replication-factor 3
confluent kafka topic create inventory.released --partitions 3 --replication-factor 3
confluent kafka topic create notifications.email --partitions 3 --replication-factor 3
confluent kafka topic create dead.letter.queue --partitions 3 --replication-factor 3
```

#### Option B: Using Web Console (Recommended for Beginners)

1. **Navigate to your cluster**:
   - Go to [confluent.cloud](https://confluent.cloud)
   - Sign in to your account
   - Select your `kafka-ecommerce` cluster

2. **Access Topics section**:
   - Click on "Topics" in the left sidebar
   - Click "Create topic" button

3. **Create each topic with these settings**:

   **Topic 1: orders.created**
   - Topic name: `orders.created`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 2: orders.validated**
   - Topic name: `orders.validated`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 3: orders.completed**
   - Topic name: `orders.completed`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 4: orders.failed**
   - Topic name: `orders.failed`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 5: payments.requested**
   - Topic name: `payments.requested`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 6: payments.completed**
   - Topic name: `payments.completed`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 7: payments.failed**
   - Topic name: `payments.failed`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 8: inventory.reserved**
   - Topic name: `inventory.reserved`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 9: inventory.released**
   - Topic name: `inventory.released`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 10: notifications.email**
   - Topic name: `notifications.email`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

   **Topic 11: dead.letter.queue**
   - Topic name: `dead.letter.queue`
   - Partitions: `3`
   - Show advanced settings → Replication factor: `3`
   - Click "Create with defaults"

4. **Verify topics creation**:
   - After creating all topics, you should see 11 topics in your Topics list
   - Each topic should show 3 partitions and replication factor 3
   - Topics should be in "Active" status

**💡 Pro Tip**: You can also bulk create topics by preparing a JSON configuration file and using the Confluent Cloud REST API, but the web console method above is the most straightforward for getting started.

### Step 5: Configure Environment Variables

Add these Confluent Cloud specific environment variables to your Render service:

```bash
# Confluent Cloud Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_SASL_USERNAME=<your-api-key>
KAFKA_SASL_PASSWORD=<your-api-secret>
KAFKA_SSL_CA_LOCATION=/etc/ssl/certs/ca-certificates.crt

# Optional: Schema Registry (if using Avro)
SCHEMA_REGISTRY_URL=https://psrc-xxxxx.us-east-2.aws.confluent.cloud
SCHEMA_REGISTRY_BASIC_AUTH_USER_INFO=<sr-api-key>:<sr-api-secret>
```

### Step 6: Update Application Configuration

Ensure your application is configured to use SASL_SSL. The project already supports this via environment variables.

### Step 7: Test Connection

Test the connection before deploying:

```python
# test_confluent_connection.py
from kafka import KafkaProducer, KafkaConsumer
import os

# Test producer
producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    security_protocol='SASL_SSL',
    sasl_mechanism='PLAIN',
    sasl_plain_username=os.getenv('KAFKA_SASL_USERNAME'),
    sasl_plain_password=os.getenv('KAFKA_SASL_PASSWORD')
)

# Send test message
producer.send('orders.created', b'test message')
producer.flush()
print("✅ Successfully connected to Confluent Cloud!")
```

### Step 8: Monitor Your Cluster

1. **Confluent Cloud Console**: Monitor topics, throughput, and consumer lag
2. **Metrics**: View detailed metrics and alerts
3. **Stream Lineage**: Visualize data flow
4. **Cost Management**: Monitor usage and costs

### Confluent Cloud Pricing

- **Basic Plan**: $0.00/hour + $0.10/GB ingress + $0.09/GB egress
- **Standard Plan**: $1.50/hour + $0.10/GB ingress + $0.09/GB egress
- **Dedicated Plan**: Custom pricing for high-throughput workloads

### Security Best Practices

1. **API Key Rotation**: Rotate API keys regularly
2. **Network Security**: Use VPC peering for production
3. **Access Control**: Implement ACLs for topic-level security
4. **Encryption**: Data is encrypted in transit and at rest

### Troubleshooting Confluent Cloud

#### Connection Issues
```bash
# Test connectivity
telnet pkc-xxxxx.us-east-1.aws.confluent.cloud 9092

# Check API key permissions
confluent kafka topic list
```

#### Authentication Errors
- Verify API key and secret are correct
- Ensure API key has proper permissions
- Check if API key is active

#### Topic Issues
```bash
# List topics
confluent kafka topic list

# Describe topic
confluent kafka topic describe orders.created

# Check topic configuration
confluent kafka topic configuration list orders.created
```

### 2. Database (PostgreSQL)
- Use Render's managed PostgreSQL service
- Or external providers like AWS RDS, Google Cloud SQL

### 3. Redis Cache
- Use Render's managed Redis service
- Or external providers like Redis Cloud, AWS ElastiCache

## Deployment Steps

### Step 1: Create Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `kafka-ecommerce-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Starter` (for testing) or `Standard` (for production)

### Step 2: Environment Variables

Set these environment variables in Render dashboard:

#### Application Settings
```
ENVIRONMENT=production
DEBUG=false
PORT=10000
HOST=0.0.0.0
```

#### Kafka Configuration
```
KAFKA_BOOTSTRAP_SERVERS=your-kafka-bootstrap-servers
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_SASL_USERNAME=your-kafka-username
KAFKA_SASL_PASSWORD=your-kafka-password
```

#### Database (PostgreSQL)
```
DATABASE_URL=postgresql://user:password@host:port/database
DB_SSL_MODE=require
```

#### Redis
```
REDIS_URL=redis://user:password@host:port
REDIS_SSL=true
```

#### Security
```
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key
API_KEY=your-api-key
CORS_ORIGINS=https://your-frontend-domain.com
```

#### External Services
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
SENDGRID_API_KEY=SG...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

#### Monitoring
```
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
```

### Step 3: Advanced Settings

#### Health Check
- **Health Check Path**: `/health`
- **Health Check Grace Period**: `300` seconds

#### Auto-Deploy
- Enable "Auto-Deploy" for automatic deployments on git push

#### Custom Domains
- Add your custom domain in the "Settings" tab
- Configure DNS records as instructed

### Step 4: Database Setup

#### Option 1: Render PostgreSQL
1. Create a new PostgreSQL service in Render
2. Copy the connection string
3. Set `DATABASE_URL` environment variable

#### Option 2: External PostgreSQL
1. Set up PostgreSQL on your preferred provider
2. Configure connection details in environment variables

### Step 5: Redis Setup

#### Option 1: Render Redis
1. Create a new Redis service in Render
2. Copy the connection string
3. Set `REDIS_URL` environment variable

#### Option 2: External Redis
1. Set up Redis on your preferred provider
2. Configure connection details in environment variables

## Configuration Files

### render.yaml (Already created)
The `render.yaml` file in your project root contains the service configuration.

### .env.render (Production Environment)
Use the `.env.render` file as a template for setting environment variables.

## Deployment Commands

### Manual Deployment
```bash
# Deploy from Render dashboard
# Or trigger via API
curl -X POST "https://api.render.com/v1/services/YOUR_SERVICE_ID/deploys" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Automatic Deployment
- Push to your main branch
- Render will automatically deploy

## Monitoring and Logging

### Built-in Monitoring
- View logs in Render dashboard
- Monitor resource usage
- Set up alerts

### External Monitoring
- **Sentry**: Error tracking and performance monitoring
- **New Relic**: Application performance monitoring
- **Datadog**: Infrastructure and application monitoring

### Log Management
```python
# Logs are automatically collected by Render
# Access via dashboard or API
# Configure log retention in service settings
```

## Scaling

### Horizontal Scaling
- Increase instance count in service settings
- Configure auto-scaling based on CPU/memory usage

### Vertical Scaling
- Upgrade instance type (Starter → Standard → Pro)
- Adjust CPU and memory allocation

## Security Best Practices

### Environment Variables
- Never commit secrets to git
- Use Render's environment variable encryption
- Rotate secrets regularly

### Network Security
- Configure CORS origins properly
- Use HTTPS only
- Implement rate limiting

### Database Security
- Use SSL connections
- Implement connection pooling
- Regular security updates

## Troubleshooting

### Common Issues

#### Build Failures
```bash
# Check requirements.txt
# Ensure Python version compatibility
# Review build logs in dashboard
```

#### Connection Issues
```bash
# Verify environment variables
# Check external service connectivity
# Review firewall settings
```

#### Performance Issues
```bash
# Monitor resource usage
# Optimize database queries
# Implement caching
# Consider scaling up
```

### Debug Commands
```bash
# View logs
render logs --service-id YOUR_SERVICE_ID

# Check service status
render services list

# Restart service
render services restart YOUR_SERVICE_ID
```

## Cost Optimization

### Instance Types
- **Starter**: $7/month (512MB RAM, 0.1 CPU)
- **Standard**: $25/month (2GB RAM, 1 CPU)
- **Pro**: $85/month (8GB RAM, 2 CPU)

### Cost-Saving Tips
1. Use appropriate instance size
2. Implement efficient caching
3. Optimize database queries
4. Monitor resource usage
5. Use external services wisely

## Backup and Recovery

### Database Backups
- Render PostgreSQL: Automatic daily backups
- External databases: Configure backup schedules

### Application Backups
- Code: Stored in Git repository
- Environment: Document all configurations
- Data: Regular database exports

## Post-Deployment Checklist

- [ ] Service is running and healthy
- [ ] All environment variables are set
- [ ] Database connection is working
- [ ] Redis connection is working
- [ ] Kafka connection is working
- [ ] External services are configured
- [ ] Health checks are passing
- [ ] Logs are being generated
- [ ] Monitoring is active
- [ ] Custom domain is configured (if applicable)
- [ ] SSL certificate is active
- [ ] CORS is properly configured
- [ ] Rate limiting is working
- [ ] Error tracking is active

## Support and Resources

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Render Community**: [community.render.com](https://community.render.com)
- **Render Status**: [status.render.com](https://status.render.com)
- **Support**: [render.com/support](https://render.com/support)

## Quick Start Commands

```bash
# 1. Push code to GitHub
git add .
git commit -m "Deploy to Render"
git push origin main

# 2. Create service in Render dashboard
# 3. Set environment variables
# 4. Deploy and monitor
```

Your Kafka E-commerce backend should now be successfully deployed on Render!