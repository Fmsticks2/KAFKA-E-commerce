# Kafka E-commerce Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Kafka E-commerce application:
- **Backend**: Deploy to Render
- **Frontend**: Deploy to Vercel

## Backend Deployment (Render)

### Prerequisites
1. Create a Render account at https://render.com
2. Connect your GitHub repository to Render
3. Ensure your backend code is in the repository

### Deployment Steps

#### 1. Create Web Service
1. Go to Render Dashboard
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `kafka-ecommerce-backend`
- **Environment**: `Python`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your production branch)
- **Root Directory**: Leave empty (or specify if backend is in subdirectory)

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

#### 2. Environment Variables (Backend)
Add these environment variables in Render Dashboard:

**Application Settings:**
```
ENVIRONMENT=production
DEBUG=false
PORT=10000
HOST=0.0.0.0
```

**Kafka Configuration:**
```
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_ENABLE_AUTO_COMMIT=true
KAFKA_AUTO_COMMIT_INTERVAL_MS=1000
```

**Service Ports:**
```
ORDER_SERVICE_PORT=5001
PAYMENT_SERVICE_PORT=5002
INVENTORY_SERVICE_PORT=5003
NOTIFICATION_SERVICE_PORT=5004
ORCHESTRATOR_SERVICE_PORT=5005
MONITORING_SERVICE_PORT=5006
EMBEDDED_KAFKA_PORT=9092
```

**External Services:**
```
PAYMENT_GATEWAY_URL=https://api.stripe.com
EMAIL_SERVICE_URL=https://api.sendgrid.com
SMS_SERVICE_URL=https://api.twilio.com
```

**Security (Generate these):**
```
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

**Monitoring:**
```
LOG_LEVEL=INFO
METRICS_ENABLED=true
```

**CORS Configuration:**
```
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
```

#### 3. Advanced Settings
- **Health Check Path**: `/health`
- **Auto-Deploy**: Enable
- **Instance Type**: Starter (can upgrade later)

---

## Frontend Deployment (Vercel)

### Prerequisites
1. Create a Vercel account at https://vercel.com
2. Install Vercel CLI: `npm i -g vercel`
3. Ensure your frontend code is ready

### Deployment Steps

#### 1. Deploy via Vercel CLI
```bash
# Navigate to frontend directory
cd frontend-dashboard-new

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

#### 2. Deploy via Vercel Dashboard
1. Go to Vercel Dashboard
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:

**Project Settings:**
- **Framework Preset**: Create React App
- **Root Directory**: `frontend-dashboard-new` (if in subdirectory)
- **Build Command**: `npm run build`
- **Output Directory**: `build`
- **Install Command**: `npm install`

#### 3. Environment Variables (Frontend)
Add these in Vercel Dashboard → Project Settings → Environment Variables:

**Required Variables:**
```
REACT_APP_API_BASE_URL=https://your-backend-domain.onrender.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0
```

**Optional Variables:**
```
REACT_APP_APP_NAME=Kafka E-commerce Dashboard
REACT_APP_SUPPORT_EMAIL=support@yourcompany.com
REACT_APP_ANALYTICS_ID=your-analytics-id
```

---

## Build & Run Settings Summary

### Backend (Render)
```yaml
# render.yaml (optional - can configure via dashboard)
services:
  - type: web
    name: kafka-ecommerce-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    plan: starter
    healthCheckPath: /health
    autoDeploy: true
```

### Frontend (Vercel)
```json
# vercel.json
{
  "version": 2,
  "name": "kafka-ecommerce-dashboard",
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "build" }
    }
  ]
}
```

---

## Post-Deployment Steps

### 1. Update CORS Settings
After frontend deployment, update backend CORS_ORIGINS:
```
CORS_ORIGINS=https://your-actual-vercel-domain.vercel.app
```

### 2. Update Frontend API URL
Update frontend environment variable:
```
REACT_APP_API_BASE_URL=https://your-actual-render-domain.onrender.com
```

### 3. Test Deployment
1. Visit your frontend URL
2. Test all service endpoints
3. Check browser console for errors
4. Verify API connectivity

### 4. Set up Custom Domains (Optional)
- **Render**: Add custom domain in service settings
- **Vercel**: Add custom domain in project settings

---

## Troubleshooting

### Common Backend Issues
1. **Build Failures**: Check requirements.txt and Python version
2. **Port Issues**: Ensure PORT environment variable is set to 10000
3. **Kafka Issues**: Verify embedded Kafka configuration
4. **CORS Errors**: Update CORS_ORIGINS with correct frontend URL

### Common Frontend Issues
1. **Build Failures**: Check package.json and Node.js version
2. **API Connection**: Verify REACT_APP_API_BASE_URL
3. **Routing Issues**: Ensure vercel.json has correct rewrites
4. **Environment Variables**: Check all REACT_APP_ prefixed variables

### Monitoring
- **Render**: Use built-in logs and metrics
- **Vercel**: Use Vercel Analytics and logs
- **Application**: Monitor via /health endpoint

---

## Security Considerations

1. **Environment Variables**: Never commit secrets to repository
2. **HTTPS**: Both platforms provide HTTPS by default
3. **CORS**: Configure restrictive CORS origins
4. **Headers**: Security headers are configured in vercel.json
5. **Secrets**: Use platform secret management features

---

## Scaling Considerations

### Backend (Render)
- Start with Starter plan
- Monitor resource usage
- Upgrade to Standard/Pro as needed
- Consider horizontal scaling for high traffic

### Frontend (Vercel)
- Vercel scales automatically
- Monitor bandwidth usage
- Consider Pro plan for team features
- Use CDN for global performance

---

## Cost Optimization

### Render
- Starter plan: $7/month
- Standard plan: $25/month
- Use sleep mode for development environments

### Vercel
- Hobby plan: Free (with limitations)
- Pro plan: $20/month per user
- Monitor bandwidth and function execution

This completes the deployment setup for your Kafka E-commerce application!