# Render Deployment Fix Guide

## Issue Summary
The deployment was failing due to confluent-kafka build issues on Render's Python 3.13 environment. The main problems were:

1. **Python Version Mismatch**: Render was using Python 3.13 while the project specified 3.11
2. **Missing System Dependencies**: librdkafka development headers were not properly installed
3. **Package Version Compatibility**: confluent-kafka 2.3.0 had build issues with newer Python versions

## Fixes Applied

### 1. Updated Requirements
- Downgraded `confluent-kafka` from 2.3.0 to 2.1.1 (better wheel support)
- Created `requirements-prod.txt` with production-optimized dependencies
- Added `gunicorn` and `gevent` for production WSGI server

### 2. Fixed Python Version Consistency
- Updated `render.yaml` to use `python-3.11.9` (matches `runtime.txt`)
- Ensured all deployment files use the same Python version

### 3. Enhanced Build Command
```bash
apt-get update && apt-get install -y build-essential librdkafka-dev pkg-config libssl-dev libffi-dev
pip install --upgrade pip setuptools wheel
pip install --only-binary=all -r requirements-prod.txt || pip install -r requirements-prod.txt
```

### 4. Updated Dockerfile
- Added proper system dependencies for confluent-kafka
- Uses production requirements file
- Multi-stage build for optimized image size

## Deployment Options

### Option 1: Render (Recommended)
Use the updated `render.yaml` configuration:
- Consistent Python 3.11.9 runtime
- Enhanced build command with all necessary dependencies
- Production requirements file

### Option 2: Docker Deployment
Use the updated Dockerfile for container-based deployment:
```bash
docker build -t kafka-ecommerce .
docker run -p 10000:10000 kafka-ecommerce
```

### Option 3: Alternative Package
If confluent-kafka continues to cause issues, consider using `kafka-python` instead:
```python
# Replace confluent-kafka with kafka-python in requirements
kafka-python==2.0.2
```

## Testing the Fix

1. **Local Testing**:
   ```bash
   pip install -r requirements-prod.txt
   python main.py
   ```

2. **Docker Testing**:
   ```bash
   docker build -t test-kafka-ecommerce .
   docker run -p 10000:10000 test-kafka-ecommerce
   ```

3. **Render Deployment**:
   - Push changes to your repository
   - Render will automatically redeploy using the new configuration

## Additional Troubleshooting

If issues persist:

1. **Check Render Logs**: Look for specific error messages in the build logs
2. **Verify Environment Variables**: Ensure all required environment variables are set
3. **Test Dependencies Locally**: Install requirements-prod.txt in a clean Python 3.11 environment
4. **Consider Managed Kafka**: Use Confluent Cloud or AWS MSK instead of embedded Kafka

## Environment Variables to Set in Render

Ensure these are configured in your Render dashboard:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `PORT=10000`
- `HOST=0.0.0.0`
- All Kafka-related configuration variables

## Next Steps

1. Deploy with the updated configuration
2. Monitor the build logs for any remaining issues
3. Test the health endpoint: `https://your-app.onrender.com/health`
4. Verify Kafka connectivity and service functionality