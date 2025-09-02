# Vercel Environment Variables Configuration

## Required Environment Variables for Production

Add these environment variables in your Vercel project settings for the deployed frontend at `https://kafka-e-commerce.vercel.app`:

### Service URLs (Replace with your Docker backend domain)

```bash
REACT_APP_ORDER_SERVICE_URL=https://your-docker-backend-domain.com:5011
REACT_APP_PAYMENT_SERVICE_URL=https://your-docker-backend-domain.com:6002
REACT_APP_INVENTORY_SERVICE_URL=https://your-docker-backend-domain.com:5003
REACT_APP_NOTIFICATION_SERVICE_URL=https://your-docker-backend-domain.com:5004
REACT_APP_ORCHESTRATOR_SERVICE_URL=https://your-docker-backend-domain.com:5005
REACT_APP_MONITORING_SERVICE_URL=https://your-docker-backend-domain.com:5005
```

### Optional Base URL

```bash
REACT_APP_API_BASE_URL=https://your-docker-backend-domain.com
```

## How to Add in Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: `kafka-ecommerce-dashboard`
3. Navigate to **Settings** → **Environment Variables**
4. For each variable:
   - **Name**: Copy the variable name (e.g., `REACT_APP_ORDER_SERVICE_URL`)
   - **Value**: Replace `your-docker-backend-domain.com` with your actual domain
   - **Environment**: Select `Production`, `Preview`, and `Development`
   - Click **Save**

## Example with Real Domain

If your Docker backend is deployed at `api.mycompany.com`, your variables would be:

```bash
REACT_APP_ORDER_SERVICE_URL=https://api.mycompany.com:5011
REACT_APP_PAYMENT_SERVICE_URL=https://api.mycompany.com:6002
REACT_APP_INVENTORY_SERVICE_URL=https://api.mycompany.com:5003
REACT_APP_NOTIFICATION_SERVICE_URL=https://api.mycompany.com:5004
REACT_APP_ORCHESTRATOR_SERVICE_URL=https://api.mycompany.com:5005
REACT_APP_MONITORING_SERVICE_URL=https://api.mycompany.com:5005
REACT_APP_API_BASE_URL=https://api.mycompany.com
```

## After Adding Variables

1. **Redeploy**: Go to **Deployments** tab and click **Redeploy** on the latest deployment
2. **Verify**: Check that the frontend can connect to your backend services
3. **Test**: Use the monitoring dashboard to verify all services are accessible

## Backend CORS Configuration

Ensure your Docker backend `.env.production` file includes:

```bash
VERCEL_FRONTEND_URL=https://kafka-e-commerce.vercel.app
CORS_ORIGINS=https://*.vercel.app,https://kafka-e-commerce.vercel.app,http://localhost:3000
```

## Fallback Behavior

If environment variables are not set, the frontend will fall back to localhost URLs:
- Order Service: `http://localhost:5011`
- Payment Service: `http://localhost:6002`
- Inventory Service: `http://localhost:5003`
- Notification Service: `http://localhost:5004`
- Orchestrator Service: `http://localhost:5005`
- Monitoring Service: `http://localhost:5005`

This allows for local development without additional configuration.