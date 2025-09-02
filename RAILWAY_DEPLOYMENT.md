# Railway Deployment Guide for Kafka E-commerce

## Overview
This guide provides step-by-step instructions for deploying the Kafka E-commerce backend to Railway.

## Prerequisites
1. Create a Railway account at https://railway.app
2. Install Railway CLI: `npm install -g @railway/cli`
3. Connect your GitHub repository to Railway

## Deployment Steps

### 1. Login to Railway
```bash
railway login
```

### 2. Initialize Railway Project
```bash
# Navigate to your backend directory
cd "c:\Users\User\Desktop\KAFKA E-commerce"

# Initialize Railway project
railway init
```

### 3. Deploy to Railway
```bash
# Deploy your application
railway up
```

### 4. Set Environment Variables
In Railway Dashboard, add these environment variables:

#### Required Variables
```
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ORDER_SERVICE_PORT=5001
PAYMENT_SERVICE_PORT=5002
INVENTORY_SERVICE_PORT=5003
NOTIFICATION_SERVICE_PORT=5004
ORCHESTRATOR_SERVICE_PORT=5005
MONITORING_SERVICE_PORT=5006
EMBEDDED_KAFKA_PORT=9092
LOG_LEVEL=INFO
METRICS_ENABLED=true
RATE_LIMIT_ENABLED=true
SSL_ENABLED=true
WORKERS=4
```

#### Security Variables (Generate these)
```
SECRET_KEY=your-production-secret-key
JWT_SECRET=your-production-jwt-secret
```

#### External Service Keys (Optional)
```
STRIPE_SECRET_KEY=sk_live_...
SENDGRID_API_KEY=SG...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
```

#### CORS Configuration
```
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

### 5. Add Database (Optional)
If you need a database:
```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

### 6. Custom Domain (Optional)
In Railway Dashboard:
1. Go to your service settings
2. Click "Domains"
3. Add your custom domain
4. Update DNS records as instructed

## Railway Configuration Files

### railway.toml
The `railway.toml` file configures your Railway deployment:
- Build settings
- Health checks
- Resource limits
- Auto-scaling
- Environment variables

### .env.production
Production environment variables with Railway-specific configurations:
- Uses Railway environment variables
- Production-ready security settings
- Optimized performance settings

## Monitoring and Logs

### View Logs
```bash
# View real-time logs
railway logs

# View logs for specific service
railway logs --service your-service-name
```

### Metrics
- Railway provides built-in metrics
- Access via Railway Dashboard
- Monitor CPU, memory, and network usage

## Scaling

### Manual Scaling
In Railway Dashboard:
1. Go to service settings
2. Adjust CPU and memory limits
3. Configure replica count

### Auto-scaling
Configured in `railway.toml`:
- Minimum replicas: 2
- Maximum replicas: 5
- CPU target: 70%
- Memory target: 80%

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `requirements.txt`
   - Verify Python version compatibility
   - Review build logs: `railway logs --build`

2. **Port Issues**
   - Railway automatically assigns PORT
   - Use `${PORT:-8000}` in configuration

3. **Environment Variables**
   - Verify all required variables are set
   - Check variable names (case-sensitive)

4. **Database Connection**
   - Use Railway-provided DATABASE_URL
   - Check connection string format

### Health Checks
- Endpoint: `/health`
- Timeout: 300 seconds
- Railway will restart unhealthy services

## Cost Optimization

### Railway Pricing
- Starter: $5/month (512MB RAM, 1 vCPU)
- Developer: $10/month (1GB RAM, 2 vCPU)
- Team: $20/month (2GB RAM, 4 vCPU)

### Tips
- Use auto-scaling to optimize costs
- Monitor resource usage
- Set appropriate resource limits
- Use staging environment for testing

## Security Best Practices

1. **Environment Variables**
   - Never commit secrets to repository
   - Use Railway's secret management
   - Rotate keys regularly

2. **HTTPS**
   - Railway provides HTTPS by default
   - Use SSL_ENABLED=true

3. **CORS**
   - Configure restrictive CORS origins
   - Update after frontend deployment

4. **Rate Limiting**
   - Enable rate limiting in production
   - Adjust limits based on usage

## Deployment Commands

```bash
# Deploy current branch
railway up

# Deploy specific branch
railway up --branch main

# Deploy with environment
railway up --environment production

# Check deployment status
railway status

# Open service in browser
railway open
```

## Post-Deployment

1. **Test Endpoints**
   - Verify all services are running
   - Test API endpoints
   - Check health endpoint

2. **Update Frontend**
   - Update REACT_APP_API_BASE_URL
   - Point to Railway domain

3. **Monitor Performance**
   - Watch logs for errors
   - Monitor resource usage
   - Set up alerts if needed

Your Kafka E-commerce backend is now ready for production on Railway! 🚀