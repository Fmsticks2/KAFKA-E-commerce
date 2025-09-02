# Production Deployment Guide

This guide explains how to deploy the Kafka E-commerce microservices application for production using Docker and integrate it with a Vercel-deployed frontend.

## Prerequisites

- Docker and Docker Compose installed
- Domain name or public IP address for your server
- SSL certificate (recommended for production)
- Vercel account with deployed frontend

## Production Architecture

The production setup includes:
- **Zookeeper**: Kafka coordination service
- **Kafka**: Message broker for microservices communication
- **E-commerce Services**: Order, Payment, Inventory, and Notification microservices
- **Kafka UI**: Web-based monitoring dashboard for Kafka
- **Nginx**: Reverse proxy with CORS support for Vercel integration
- **Monitoring**: Prometheus and Grafana (optional)

## Quick Start

### 1. Environment Configuration

Copy and configure the production environment file:

```bash
cp .env.production .env
```

Update the following variables in `.env`:

```bash
# Your production domain or IP
EXTERNAL_HOST=your-domain.com

# Vercel frontend URL (replace with your actual Vercel deployment URL)
VERCEL_FRONTEND_URL=https://your-frontend.vercel.app

# Kafka UI credentials (change these!)
KAFKA_UI_AUTH_USER=admin
KAFKA_UI_AUTH_PASSWORD=your-secure-password

# Security settings
JWT_SECRET_KEY=your-jwt-secret-key
API_SECRET_KEY=your-api-secret-key
```

### 2. Deploy Services

Start all services using the production Docker Compose configuration:

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 3. Verify Deployment

Check that all services are running:

```bash
docker-compose -f docker-compose.production.yml ps
```

Test the API endpoints:

```bash
# Health check
curl http://your-domain.com/api/health

# Order service
curl http://your-domain.com/api/orders/health

# Payment service
curl http://your-domain.com/api/payments/health
```

### 4. Access Kafka Monitoring Dashboard

The Kafka UI dashboard is available at:
```
http://your-domain.com/kafka-ui
```

Login with the credentials you set in the `.env` file.

## Vercel Frontend Integration

### Frontend Environment Variables

In your Vercel project settings, add these environment variables:

```bash
NEXT_PUBLIC_API_BASE_URL=http://your-domain.com/api
NEXT_PUBLIC_WS_URL=ws://your-domain.com/ws
```

### CORS Configuration

The backend services are pre-configured with CORS support for Vercel. The allowed origins include:
- Your Vercel deployment URL
- Vercel preview deployments (*.vercel.app)
- Local development (localhost:3000)

## SSL/HTTPS Setup (Recommended)

For production, it's highly recommended to use HTTPS:

### Option 1: Let's Encrypt with Certbot

1. Install Certbot:
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com
```

3. Update Nginx configuration to use HTTPS

### Option 2: CloudFlare or Load Balancer

Use a service like CloudFlare or AWS Application Load Balancer to handle SSL termination.

## Monitoring and Logging

### Kafka UI Dashboard

Access the Kafka monitoring dashboard at `/kafka-ui` to:
- Monitor topic messages
- View consumer group status
- Check broker health
- Analyze message throughput

### Service Logs

View logs for specific services:

```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f order-service
```

### Health Checks

All services provide health check endpoints:
- Order Service: `/api/orders/health`
- Payment Service: `/api/payments/health`
- Inventory Service: `/api/inventory/health`
- Notification Service: `/api/notifications/health`

## Scaling and Performance

### Horizontal Scaling

Scale individual services:

```bash
# Scale order service to 3 replicas
docker-compose -f docker-compose.production.yml up -d --scale ecommerce-app=3
```

### Kafka Configuration

For high-throughput scenarios, consider:
- Increasing Kafka partitions
- Adding more Kafka brokers
- Tuning consumer group configurations

## Security Best Practices

1. **Change Default Passwords**: Update all default passwords in `.env`
2. **Network Security**: Use firewall rules to restrict access
3. **Regular Updates**: Keep Docker images updated
4. **Monitoring**: Set up alerts for service failures
5. **Backup**: Regular backup of Kafka data and application state

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Verify `VERCEL_FRONTEND_URL` in `.env`
   - Check Nginx CORS configuration
   - Ensure frontend uses correct API URL

2. **Kafka Connection Issues**:
   - Check Kafka broker health
   - Verify network connectivity
   - Review Kafka logs

3. **Service Startup Failures**:
   - Check Docker logs
   - Verify environment variables
   - Ensure sufficient system resources

### Debug Commands

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# View service logs
docker-compose -f docker-compose.production.yml logs [service-name]

# Restart specific service
docker-compose -f docker-compose.production.yml restart [service-name]

# Check Kafka topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Maintenance

### Updates

1. Pull latest images:
```bash
docker-compose -f docker-compose.production.yml pull
```

2. Restart services:
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Backup

Regular backup of:
- Kafka data volumes
- Application configuration
- SSL certificates

## Support

For issues and questions:
1. Check service logs
2. Review Kafka UI dashboard
3. Verify network connectivity
4. Check environment configuration

---

**Note**: This setup is designed for production use with proper security, monitoring, and scalability considerations. Always test thoroughly in a staging environment before deploying to production.