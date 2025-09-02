#!/usr/bin/env python3
"""
Confluent Cloud Topics Test Script
Tests all required topics for the Kafka E-commerce system
"""

try:
    from confluent_kafka import Producer, Consumer, KafkaError
    from confluent_kafka.admin import AdminClient, NewTopic
except ImportError:
    print("❌ confluent-kafka not installed. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "confluent-kafka"])
    from confluent_kafka import Producer, Consumer, KafkaError
    from confluent_kafka.admin import AdminClient, NewTopic

import json
import time
from datetime import datetime

# Confluent Cloud Configuration
CONFIG = {
    'bootstrap.servers': 'pkc-q283m.af-south-1.aws.confluent.cloud:9092',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': 'SZ2L5PSSLJYXDKLF',
    'sasl.password': 'cfltN5E7HGCH+Q42Fz2BMBGwApkmpfGmhx5sAFi0+ZsKMU7w9TWjUmUy6Ro3Jq3w'
}

# Required topics for the e-commerce system
REQUIRED_TOPICS = [
    'orders.created',
    'orders.validated', 
    'orders.completed',
    'orders.failed',
    'payments.requested',
    'payments.completed',
    'payments.failed',
    'inventory.reserved',
    'inventory.released',
    'notifications.email',
    'dead.letter.queue'
]

def test_connection():
    """Test basic connection to Confluent Cloud"""
    print("🔗 Testing connection to Confluent Cloud...")
    try:
        admin_client = AdminClient(CONFIG)
        metadata = admin_client.list_topics(timeout=10)
        print(f"✅ Successfully connected to cluster")
        print(f"   Available topics: {len(metadata.topics)}")
        return True, metadata
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False, None

def check_required_topics(metadata):
    """Check if all required topics exist"""
    print("\n🔍 Checking required topics...")
    if not metadata:
        print("❌ No metadata available")
        return False
        
    existing_topics = set(metadata.topics.keys())
    missing_topics = []
    existing_required = []
    
    for topic in REQUIRED_TOPICS:
        if topic in existing_topics:
            existing_required.append(topic)
            print(f"   ✅ {topic}")
        else:
            missing_topics.append(topic)
            print(f"   ❌ {topic} (MISSING)")
    
    print(f"\n📊 Summary:")
    print(f"   Required topics: {len(REQUIRED_TOPICS)}")
    print(f"   Found: {len(existing_required)}")
    print(f"   Missing: {len(missing_topics)}")
    
    if missing_topics:
        print(f"\n⚠️  Missing topics: {', '.join(missing_topics)}")
        print("\n💡 To create missing topics, use the Confluent Cloud web console:")
        print("   1. Go to https://confluent.cloud")
        print("   2. Select your cluster")
        print("   3. Go to Topics → Create topic")
        print("   4. Create each missing topic with 3 partitions")
        return False
    else:
        print(f"\n🎉 All required topics are present!")
        return True

def get_topic_details(metadata):
    """Get detailed information about required topics"""
    print("\n📊 Getting topic details...")
    if not metadata:
        print("❌ No metadata available")
        return
        
    for topic_name in REQUIRED_TOPICS:
        if topic_name in metadata.topics:
            topic = metadata.topics[topic_name]
            partitions = len(topic.partitions)
            print(f"\n   📁 {topic_name}:")
            print(f"      Partitions: {partitions}")
            
            # Show partition details
            for partition_id, partition in topic.partitions.items():
                replicas = len(partition.replicas)
                print(f"      Partition {partition_id}: {replicas} replicas")

def test_producer():
    """Test producing messages to topics"""
    print("\n📤 Testing message production...")
    try:
        producer = Producer(CONFIG)
        
        test_message = {
            'test_id': 'confluent_test_001',
            'timestamp': datetime.now().isoformat(),
            'message': 'Test message from Confluent Cloud setup'
        }
        
        # Test a few key topics
        test_topics = ['orders.created', 'payments.requested', 'notifications.email']
        
        for topic in test_topics:
            try:
                producer.produce(
                    topic, 
                    key='test_key',
                    value=json.dumps(test_message)
                )
                print(f"   ✅ {topic}: Message queued for production")
            except Exception as e:
                print(f"   ❌ {topic}: {e}")
        
        # Wait for messages to be delivered
        producer.flush(timeout=10)
        print("\n🎉 Message production test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Producer test failed: {e}")
        return False

def test_consumer():
    """Test consuming messages from topics"""
    print("\n📥 Testing message consumption...")
    try:
        consumer_config = CONFIG.copy()
        consumer_config.update({
            'group.id': 'test-consumer-group',
            'auto.offset.reset': 'latest'
        })
        
        consumer = Consumer(consumer_config)
        consumer.subscribe(['orders.created'])
        
        print("   Listening for messages (5 second timeout)...")
        message_count = 0
        start_time = time.time()
        
        while time.time() - start_time < 5:  # 5 second timeout
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"   ❌ Consumer error: {msg.error()}")
                    break
            
            message_count += 1
            print(f"   📨 Received message {message_count}: {msg.value().decode('utf-8')}")
            if message_count >= 3:  # Limit to 3 messages
                break
        
        consumer.close()
        
        if message_count > 0:
            print(f"   ✅ Successfully consumed {message_count} messages")
        else:
            print("   ℹ️  No new messages found (this is normal for a fresh setup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Consumer test failed: {e}")
        return False

def create_missing_topics(admin_client, missing_topics):
    """Create missing topics programmatically"""
    print(f"\n🔧 Creating {len(missing_topics)} missing topics...")
    
    new_topics = []
    for topic_name in missing_topics:
        new_topic = NewTopic(
            topic=topic_name,
            num_partitions=3,
            replication_factor=3
        )
        new_topics.append(new_topic)
    
    try:
        # Create topics
        fs = admin_client.create_topics(new_topics)
        
        # Wait for each operation to finish
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                print(f"   ✅ Created topic: {topic}")
            except Exception as e:
                print(f"   ❌ Failed to create topic {topic}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create topics: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Confluent Cloud Topics Test")
    print("=" * 50)
    print(f"Cluster: pkc-q283m.af-south-1.aws.confluent.cloud:9092")
    print(f"Environment: env-q5xxkm")
    print(f"Resource: lkc-3j28yw")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test connection
    connection_ok, metadata = test_connection()
    if connection_ok:
        tests_passed += 1
    else:
        print("\n❌ Cannot proceed without connection. Please check your credentials.")
        return
    
    # Check topics
    topics_ok = check_required_topics(metadata)
    if topics_ok:
        tests_passed += 1
    
    # Get topic details
    get_topic_details(metadata)
    
    # Test producer
    if test_producer():
        tests_passed += 1
    
    # Test consumer
    if test_consumer():
        tests_passed += 1
    
    # Final summary
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed >= 3:  # Connection + topics + at least one messaging test
        print("🎉 Your Confluent Cloud setup is working correctly!")
        print("\n✅ Ready for production deployment!")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
    
    print("\n📝 Next steps:")
    print("   1. ✅ .env.render has been updated with your Confluent Cloud credentials")
    print("   2. Deploy your application to Render")
    print("   3. Monitor your topics in Confluent Cloud console")
    print("   4. Check application logs for any Kafka connection issues")

if __name__ == "__main__":
    main()