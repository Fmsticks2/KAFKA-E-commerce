# Full Deployment Guide: Docker Backend + Vercel Frontend

This comprehensive guide covers deploying the Kafka E-commerce system with a Docker backend on a public domain and a Vercel frontend.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Docker Deployment](#backend-docker-deployment)
3. [Domain and SSL Configuration](#domain-and-ssl-configuration)
4. [Frontend Vercel Deployment](#frontend-vercel-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Testing and Verification](#testing-and-verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services
- Docker and Docker Compose installed
- A cloud server (AWS EC2, DigitalOcean, Google Cloud, etc.)
- A domain name (e.g., `yourdomain.com`)
- Vercel account
- GitHub repository with your code

### Required Ports
Ensure these ports are open on your server:
- `80` (HTTP)
- `443` (HTTPS)
- `5011` (Order Service)
- `6002` (Payment Service)
- `5003` (Inventory Service)
- `5004` (Notification Service)
- `5005` (Orchestrator Service)
- `8080` (Kafka UI)

## Backend Docker Deployment

### Step 1: Server Setup

1. **Launch a Cloud Server**
   ```bash
   # Example for Ubuntu 20.04+ server
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install Docker and Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Verify installation
   docker --version
   docker-compose --version
   ```

3. **Configure Firewall**
   ```bash
   # Ubuntu UFW example
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw allow 5011  # Order Service
   sudo ufw allow 6002  # Payment Service
   sudo ufw allow 5003  # Inventory Service
   sudo ufw allow 5004  # Notification Service
   sudo ufw allow 5005  # Orchestrator Service
   sudo ufw allow 8080  # Kafka UI
   sudo ufw enable
   ```

### Step 2: Deploy Application

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/kafka-ecommerce.git
   cd kafka-ecommerce
   ```

2. **Configure Environment**
   ```bash
   # Copy and edit production environment file
   cp .env.production .env
   nano .env
   ```

3. **Update .env Configuration**
   ```bash
   # Replace with your actual domain
   EXTERNAL_HOST=api.yourdomain.com
   API_BASE_URL=https://api.yourdomain.com:5005
   
   # Vercel frontend URL
   VERCEL_FRONTEND_URL=https://kafka-e-commerce.vercel.app
   CORS_ORIGINS=https://*.vercel.app,https://kafka-e-commerce.vercel.app,http://localhost:3000
   
   # Kafka UI credentials (change these!)
   KAFKA_UI_USERNAME=admin
   KAFKA_UI_PASSWORD=your-secure-password-here
   
   # Environment settings
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   ```

4. **Build and Deploy**
   ```bash
   # Build and start services
   docker-compose -f docker-compose.production.yml up -d
   
   # Check status
   docker-compose -f docker-compose.production.yml ps
   
   # View logs
   docker-compose -f docker-compose.production.yml logs -f
   ```

## Domain and SSL Configuration

### Step 3: DNS Configuration

1. **Configure DNS Records**
   In your domain registrar's DNS settings:
   ```
   Type: A
   Name: api
   Value: YOUR_SERVER_IP
   TTL: 300
   
   Type: A
   Name: @
   Value: YOUR_SERVER_IP
   TTL: 300
   ```

2. **Verify DNS Propagation**
   ```bash
   # Check if DNS is working
   nslookup api.yourdomain.com
   ping api.yourdomain.com
   ```

### Step 4: SSL Certificate Setup

1. **Install Certbot**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   ```

2. **Install Nginx**
   ```bash
   sudo apt install nginx -y
   sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

3. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/kafka-ecommerce
   ```
   
   Add this configuration:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
   
       location / {
           proxy_pass http://localhost:5005;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   
       location /order {
           proxy_pass http://localhost:5011;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   
       location /payment {
           proxy_pass http://localhost:6002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   
       location /inventory {
           proxy_pass http://localhost:5003;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   
       location /notification {
           proxy_pass http://localhost:5004;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Enable Site and Get SSL**
   ```bash
   sudo ln -s /etc/nginx/sites-available/kafka-ecommerce /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d api.yourdomain.com
   ```

## Frontend Vercel Deployment

### Step 5: Prepare Frontend

1. **Update Frontend Repository**
   Ensure your frontend code is pushed to GitHub with the latest changes.

2. **Verify Build Configuration**
   ```bash
   cd frontend-dashboard
   npm install
   npm run build
   ```

### Step 6: Deploy to Vercel

1. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import your repository
   - Select the `frontend-dashboard` folder as the root directory

2. **Configure Build Settings**
   ```
   Framework Preset: Create React App
   Root Directory: frontend-dashboard
   Build Command: npm run build
   Output Directory: build
   Install Command: npm install
   ```

3. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Note your Vercel URL (e.g., `https://kafka-e-commerce.vercel.app`)

## Environment Configuration

### Step 7: Configure Vercel Environment Variables

1. **Access Project Settings**
   - Go to your Vercel dashboard
   - Select your project
   - Go to Settings → Environment Variables

2. **Add Environment Variables**
   Add each of these variables:
   
   | Variable Name | Value | Environment |
   |---------------|-------|-------------|
   | `REACT_APP_ORDER_SERVICE_URL` | `https://api.yourdomain.com:5011` | Production, Preview, Development |
   | `REACT_APP_PAYMENT_SERVICE_URL` | `https://api.yourdomain.com:6002` | Production, Preview, Development |
   | `REACT_APP_INVENTORY_SERVICE_URL` | `https://api.yourdomain.com:5003` | Production, Preview, Development |
   | `REACT_APP_NOTIFICATION_SERVICE_URL` | `https://api.yourdomain.com:5004` | Production, Preview, Development |
   | `REACT_APP_ORCHESTRATOR_SERVICE_URL` | `https://api.yourdomain.com:5005` | Production, Preview, Development |
   | `REACT_APP_MONITORING_SERVICE_URL` | `https://api.yourdomain.com:5005` | Production, Preview, Development |
   | `REACT_APP_API_BASE_URL` | `https://api.yourdomain.com` | Production, Preview, Development |

3. **Redeploy Frontend**
   - Go to Deployments tab
   - Click "Redeploy" on the latest deployment
   - Or push a new commit to trigger automatic deployment

### Step 8: Update Backend CORS

1. **Update Backend Environment**
   ```bash
   # On your server, update the .env file
   nano .env
   ```
   
   Update these values:
   ```bash
   VERCEL_FRONTEND_URL=https://your-actual-vercel-url.vercel.app
   CORS_ORIGINS=https://*.vercel.app,https://your-actual-vercel-url.vercel.app,http://localhost:3000
   ```

2. **Restart Services**
   ```bash
   docker-compose -f docker-compose.production.yml down
   docker-compose -f docker-compose.production.yml up -d
   ```

## Testing and Verification

### Step 9: Health Checks

1. **Test Backend Services**
   ```bash
   # Test each service endpoint
   curl https://api.yourdomain.com:5011/health  # Order Service
   curl https://api.yourdomain.com:6002/health  # Payment Service
   curl https://api.yourdomain.com:5003/health  # Inventory Service
   curl https://api.yourdomain.com:5004/health  # Notification Service
   curl https://api.yourdomain.com:5005/health  # Orchestrator Service
   ```

2. **Test Frontend**
   - Open your Vercel URL in a browser
   - Check browser console for any CORS errors
   - Test the monitoring dashboard
   - Verify service health checks work

3. **Test End-to-End Flow**
   - Create a test order
   - Verify payment processing
   - Check inventory updates
   - Confirm notifications are sent

### Step 10: Monitoring Setup

1. **Access Kafka UI**
   - Go to `https://api.yourdomain.com:8080`
   - Login with your configured credentials
   - Verify Kafka topics and messages

2. **Monitor Logs**
   ```bash
   # View service logs
   docker-compose -f docker-compose.production.yml logs -f order-service
   docker-compose -f docker-compose.production.yml logs -f payment-service
   ```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Verify `CORS_ORIGINS` includes your Vercel URL
   - Check that backend services are accessible
   - Ensure SSL certificates are valid

2. **Service Connection Issues**
   - Check firewall settings
   - Verify DNS resolution
   - Test individual service endpoints

3. **SSL Certificate Issues**
   ```bash
   # Renew certificates
   sudo certbot renew
   sudo systemctl reload nginx
   ```

4. **Docker Issues**
   ```bash
   # Restart all services
   docker-compose -f docker-compose.production.yml down
   docker system prune -f
   docker-compose -f docker-compose.production.yml up -d
   ```

5. **Environment Variable Issues**
   - Verify variables are set in Vercel
   - Check variable names (must start with `REACT_APP_`)
   - Redeploy after changing variables

### Useful Commands

```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f [service-name]

# Restart specific service
docker-compose -f docker-compose.production.yml restart [service-name]

# Check system resources
docker stats

# Check nginx status
sudo systemctl status nginx

# Test SSL certificate
ssl-cert-check -c api.yourdomain.com
```

## Security Checklist

- [ ] Changed default Kafka UI credentials
- [ ] Configured firewall properly
- [ ] SSL certificates installed and working
- [ ] Environment variables secured
- [ ] Regular security updates scheduled
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

## Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   # Update Docker images
   docker-compose -f docker-compose.production.yml pull
   docker-compose -f docker-compose.production.yml up -d
   ```

2. **Monitor Resources**
   ```bash
   # Check disk usage
   df -h
   
   # Check memory usage
   free -h
   
   # Check Docker resource usage
   docker system df
   ```

3. **Backup Data**
   ```bash
   # Backup Kafka data
   docker-compose -f docker-compose.production.yml exec kafka kafka-topics --bootstrap-server localhost:9092 --list
   ```

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify all configuration steps were completed
4. Test individual components separately

---

**Deployment Complete!** 🎉

Your Kafka E-commerce system should now be running with:
- Backend: `https://api.yourdomain.com`
- Frontend: `https://your-vercel-url.vercel.app`
- Kafka UI: `https://api.yourdomain.com:8080`