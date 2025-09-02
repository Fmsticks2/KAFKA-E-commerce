# Render Deployment Troubleshooting Guide

## Python 3.13 Compatibility Issue with confluent-kafka

### Problem Description
The confluent-kafka package (version 2.3.0) doesn't have pre-built wheels for Python 3.13, causing build failures during Render deployment with the error:

```
Building wheel for confluent-kafka (pyproject.toml): finished with status 'error'
fatal error: librdkafka/rdkafka.h: No such file or directory
```

### Root Cause
- Render uses Python 3.13 by default
- confluent-kafka 2.3.0 doesn't have pre-compiled wheels for Python 3.13
- The package tries to build from source but fails due to missing system dependencies

### Solutions Implemented

#### Solution 1: Specify Python Version
1. **runtime.txt**: Created to specify Python 3.11.9
2. **render.yaml**: Added `runtime: python-3.11` specification

#### Solution 2: System Dependencies
Added build dependencies in render.yaml:
```yaml
buildCommand: |
  apt-get update && apt-get install -y build-essential librdkafka-dev
  pip install --upgrade pip
  pip install -r requirements.txt
```

### Alternative Solutions (if above doesn't work)

#### Option A: Use Different confluent-kafka Version
```bash
# Try an older version with better compatibility
pip install confluent-kafka==2.1.1
```

#### Option B: Use Alternative Kafka Client
```bash
# Consider kafka-python as alternative
pip install kafka-python==2.0.2
```

#### Option C: Docker-based Deployment
Create a Dockerfile with specific Python version:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

CMD ["python", "main.py"]
```

### Verification Steps

1. **Check Python Version in Logs**:
   ```bash
   python --version
   ```

2. **Verify confluent-kafka Installation**:
   ```python
   import confluent_kafka
   print(confluent_kafka.version())
   ```

3. **Test Kafka Connection**:
   ```python
   from confluent_kafka import Producer
   # Test with your Confluent Cloud credentials
   ```

### Monitoring Deployment

1. **Watch Build Logs**: Monitor the build process in Render dashboard
2. **Check Runtime Logs**: Verify the application starts successfully
3. **Test Endpoints**: Ensure health checks pass

### Additional Resources

- [Confluent Kafka Python Compatibility](https://github.com/confluentinc/confluent-kafka-python/issues/1802)
- [Render Python Runtime Specification](https://render.com/docs/python-version)
- [Building Python Packages from Source](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

### Contact Support

If issues persist:
1. Check Render community forums
2. Review confluent-kafka GitHub issues
3. Consider using Docker deployment for more control