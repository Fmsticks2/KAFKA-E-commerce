#!/usr/bin/env python3
"""
Embedded Kafka for Testing

This script creates a simple in-memory Kafka-like message broker
for testing the e-commerce system without requiring external Kafka.
"""

import asyncio
import json
import threading
import time
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any
import structlog
from flask import Flask, request, jsonify

# Setup logging
logger = structlog.get_logger(__name__)

class EmbeddedKafka:
    """Simple in-memory Kafka-like message broker for testing"""
    
    def __init__(self):
        self.topics: Dict[str, deque] = defaultdict(deque)
        self.consumers: Dict[str, List[Callable]] = defaultdict(list)
        self.running = False
        self.lock = threading.Lock()
        
    def create_topic(self, topic_name: str):
        """Create a topic"""
        with self.lock:
            if topic_name not in self.topics:
                self.topics[topic_name] = deque()
                logger.info("Topic created", topic=topic_name)
    
    def produce(self, topic: str, message: dict, key: str = None):
        """Produce a message to a topic"""
        with self.lock:
            if topic not in self.topics:
                self.create_topic(topic)
            
            msg = {
                'key': key,
                'value': message,
                'timestamp': time.time(),
                'offset': len(self.topics[topic])
            }
            
            self.topics[topic].append(msg)
            logger.info("Message produced", topic=topic, key=key, offset=msg['offset'])
            
            # Notify consumers
            self._notify_consumers(topic, msg)
    
    def consume(self, topic: str, group_id: str = None, auto_offset_reset: str = 'latest'):
        """Consume messages from a topic"""
        with self.lock:
            if topic not in self.topics:
                return []
            
            messages = list(self.topics[topic])
            if auto_offset_reset == 'earliest':
                return messages
            else:
                # Return only new messages (for simplicity, return last 10)
                return messages[-10:] if len(messages) > 10 else messages
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic with a callback"""
        with self.lock:
            self.consumers[topic].append(callback)
            logger.info("Consumer subscribed", topic=topic)
    
    def _notify_consumers(self, topic: str, message: dict):
        """Notify all consumers of a new message"""
        for callback in self.consumers[topic]:
            try:
                callback(message)
            except Exception as e:
                logger.error("Consumer callback failed", topic=topic, error=str(e))
    
    def get_topics(self):
        """Get all topics"""
        with self.lock:
            return list(self.topics.keys())
    
    def get_topic_info(self, topic: str):
        """Get topic information"""
        with self.lock:
            if topic in self.topics:
                return {
                    'topic': topic,
                    'message_count': len(self.topics[topic]),
                    'latest_offset': len(self.topics[topic]) - 1 if self.topics[topic] else -1
                }
            return None
    
    def clear_topic(self, topic: str):
        """Clear all messages from a topic"""
        with self.lock:
            if topic in self.topics:
                self.topics[topic].clear()
                logger.info("Topic cleared", topic=topic)

# Global embedded Kafka instance
embedded_kafka = EmbeddedKafka()

# Flask app for Kafka REST API
app = Flask(__name__)

@app.route('/topics', methods=['GET'])
def get_topics():
    """Get all topics"""
    return jsonify({
        'topics': embedded_kafka.get_topics()
    })

@app.route('/topics/<topic_name>', methods=['POST'])
def create_topic(topic_name):
    """Create a topic"""
    embedded_kafka.create_topic(topic_name)
    return jsonify({
        'status': 'success',
        'topic': topic_name
    })

@app.route('/topics/<topic_name>/produce', methods=['POST'])
def produce_message(topic_name):
    """Produce a message to a topic"""
    data = request.get_json()
    message = data.get('message', {})
    key = data.get('key')
    
    embedded_kafka.produce(topic_name, message, key)
    
    return jsonify({
        'status': 'success',
        'topic': topic_name,
        'key': key
    })

@app.route('/topics/<topic_name>/consume', methods=['GET'])
def consume_messages(topic_name):
    """Consume messages from a topic"""
    group_id = request.args.get('group_id')
    auto_offset_reset = request.args.get('auto_offset_reset', 'latest')
    
    messages = embedded_kafka.consume(topic_name, group_id, auto_offset_reset)
    
    return jsonify({
        'topic': topic_name,
        'messages': messages
    })

@app.route('/topics/<topic_name>/info', methods=['GET'])
def get_topic_info(topic_name):
    """Get topic information"""
    info = embedded_kafka.get_topic_info(topic_name)
    if info:
        return jsonify(info)
    else:
        return jsonify({'error': 'Topic not found'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'embedded-kafka',
        'topics_count': len(embedded_kafka.get_topics())
    })

def setup_default_topics():
    """Setup default topics for the e-commerce system"""
    topics = [
        'orders.created',
        'orders.validated',
        'orders.completed',
        'orders.failed',
        'payments.requested',
        'payments.completed',
        'payments.failed',
        'inventory.reserved',
        'inventory.confirmed',
        'inventory.released',
        'notifications.email',
        'notifications.sms',
        'dlq.orders',
        'dlq.payments',
        'dlq.inventory',
        'dlq.notifications'
    ]
    
    for topic in topics:
        embedded_kafka.create_topic(topic)
    
    logger.info("Default topics created", count=len(topics))

def start_embedded_kafka(port=9093):
    """Start the embedded Kafka server"""
    setup_default_topics()
    
    logger.info("Starting Embedded Kafka", port=port)
    print(f"\n{'='*50}")
    print("EMBEDDED KAFKA STARTED")
    print(f"{'='*50}")
    print(f"REST API: http://localhost:{port}")
    print(f"Topics created: {len(embedded_kafka.get_topics())}")
    print("\nAvailable endpoints:")
    print(f"  GET  /topics - List all topics")
    print(f"  POST /topics/<name> - Create topic")
    print(f"  POST /topics/<name>/produce - Produce message")
    print(f"  GET  /topics/<name>/consume - Consume messages")
    print(f"  GET  /topics/<name>/info - Topic info")
    print(f"  GET  /health - Health check")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    import sys
    
    port = 9093
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 9093")
    
    start_embedded_kafka(port)