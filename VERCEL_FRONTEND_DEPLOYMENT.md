# Vercel Frontend Deployment Guide

This guide explains how to deploy the frontend to Vercel and configure it to work with a Docker production backend.

## Frontend Configuration

The frontend has been updated to use environment variables for service URLs, allowing it to connect to different backend deployments.

### Required Environment Variables for Vercel

Add these environment variables in your Vercel project settings:

```bash
# Individual Service URLs (replace with your Docker backend domain)
REACT_APP_ORDER_SERVICE_URL=https://your-docker-backend-domain.com:5011
REACT_APP_PAYMENT_SERVICE_URL=https://your-docker-backend-domain.com:6002
REACT_APP_INVENTORY_SERVICE_URL=https://your-docker-backend-domain.com:5003
REACT_APP_NOTIFICATION_SERVICE_URL=https://your-docker-backend-domain.com:5004
REACT_APP_ORCHESTRATOR_SERVICE_URL=https://your-docker-backend-domain.com:5005
REACT_APP_MONITORING_SERVICE_URL=https://your-docker-backend-domain.com:5005

# Optional: Legacy API Base URL
REACT_APP_API_BASE_URL=https://your-docker-backend-domain.com
```

### How to Add Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Select your project (`kafka-ecommerce-dashboard`)
3. Go to **Settings** → **Environment Variables**
4. Add each variable:
   - **Name**: `REACT_APP_ORDER_SERVICE_URL`
   - **Value**: `https://your-docker-backend-domain.com:5011`
   - **Environment**: Select `Production`, `Preview`, and `Development`
5. Repeat for all service URLs
6. Click **Save**
7. Redeploy your application

## Backend Configuration

The backend `.env.production` file has been updated with your Vercel frontend URL:

```bash
VERCEL_FRONTEND_URL=https://kafka-e-commerce.vercel.app
CORS_ORIGINS=https://*.vercel.app,https://kafka-e-commerce.vercel.app,http://localhost:3000
```

## Deployment Steps

### 1. Deploy Backend to Docker

```bash
# Build and deploy using docker-compose
docker-compose -f docker-compose.production.yml up -d

# Or build individual services
docker build -t kafka-ecommerce-backend .
docker run -d -p 5005:5005 --env-file .env.production kafka-ecommerce-backend
```

### 2. Update Vercel Environment Variables

Replace `your-docker-backend-domain.com` with your actual Docker backend domain in all the environment variables.

### 3. Redeploy Frontend

After updating environment variables in Vercel:

1. Go to **Deployments** tab
2. Click **Redeploy** on the latest deployment
3. Or push a new commit to trigger automatic deployment

## Testing the Connection

1. Open your Vercel frontend: https://kafka-e-commerce.vercel.app
2. Check the browser console for any CORS errors
3. Test the service health checks in the monitoring dashboard
4. Verify that API calls are going to the correct backend URLs

## Troubleshooting

### CORS Issues
- Ensure your Docker backend domain is added to `CORS_ORIGINS` in `.env.production`
- Check that the backend is accessible from the internet
- Verify SSL certificates if using HTTPS

### Environment Variables Not Working
- Ensure all variables start with `REACT_APP_`
- Check that variables are set for the correct environment (Production)
- Redeploy after adding/changing variables

### Service Connection Issues
- Verify that all backend services are running on the specified ports
- Check firewall settings on your Docker host
- Ensure the backend domain is accessible from the internet

## Current Deployment Status

- **Frontend URL**: https://kafka-e-commerce.vercel.app
- **Backend Configuration**: Updated for CORS compatibility
- **Service URLs**: Configurable via environment variables
- **Fallback**: Localhost URLs for local development

## Next Steps

1. Deploy your backend to Docker with a public domain
2. Update the Vercel environment variables with the actual backend domain
3. Redeploy the frontend
4. Test the full application flow