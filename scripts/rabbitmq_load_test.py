#!/usr/bin/env python3
"""
Direct RabbitMQ Load Test for Task 405 Validation
Sends test messages directly to content_analysis_v2_queue to measure throughput
"""

import json
import time
import pika
import sys
from datetime import datetime
from typing import Dict

# Configuration
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"
QUEUE_NAME = "content_analysis_v2_queue"
NUM_MESSAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 50


def create_test_message(index: int) -> Dict:
    """Create a realistic test message for content analysis."""
    return {
        "event_type": "article.created",
        "article_id": f"test_article_{index}_{int(time.time())}",
        "feed_item_id": f"test_feed_item_{index}",
        "title": f"Load Test Article #{index} - Task 405 RabbitMQ Optimization Validation",
        "content": f"This is test article #{index} generated for Task 405 load testing. "
                   f"The purpose is to validate the RabbitMQ optimization where prefetch_count "
                   f"was increased from 1 to 20 in content-analysis-v2 workers. "
                   f"Expected improvement: 30-100% throughput increase. "
                   f"Generated at {datetime.now().isoformat()}. "
                   f"This content is long enough to trigger realistic processing times in the analysis pipeline.",
        "source": "load_test_script",
        "url": f"https://test.example.com/article-{index}",
        "published_at": datetime.now().isoformat(),
        "feed_id": 1,
        "timestamp": datetime.now().isoformat()
    }


def send_messages(num_messages: int):
    """Send test messages to RabbitMQ queue."""
    print("=" * 60)
    print("Task 405 - Direct RabbitMQ Load Test")
    print("=" * 60)
    print(f"Target: {num_messages} messages")
    print(f"Queue: {QUEUE_NAME}")
    print(f"Started: {datetime.now().isoformat()}")
    print("")

    # Step 1: Connect to RabbitMQ
    print("[1/3] Connecting to RabbitMQ...")
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        print("✓ Connected to RabbitMQ")
        print("")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    # Step 2: Ensure queue exists
    print("[2/3] Verifying queue...")
    try:
        channel.queue_declare(queue=QUEUE_NAME, durable=True, passive=True)
        print(f"✓ Queue '{QUEUE_NAME}' exists")
        print("")
    except Exception as e:
        print(f"❌ Queue verification failed: {e}")
        connection.close()
        sys.exit(1)

    # Step 3: Send messages
    print(f"[3/3] Sending {num_messages} messages...")
    start_time = time.time()
    success_count = 0
    error_count = 0

    for i in range(1, num_messages + 1):
        try:
            message = create_test_message(i)
            message_body = json.dumps(message)

            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json'
                )
            )
            success_count += 1

            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  Progress: {i}/{num_messages} messages sent ({rate:.1f} msg/sec)")

        except Exception as e:
            error_count += 1
            if error_count <= 3:
                print(f"⚠ Error sending message {i}: {e}")

    send_duration = time.time() - start_time

    print("")
    print("=" * 60)
    print("SUBMISSION COMPLETE")
    print("=" * 60)
    print(f"Total messages sent: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Duration: {send_duration:.2f}s")
    print(f"Rate: {success_count / send_duration:.2f} msg/sec")
    print("")

    # Close connection
    connection.close()

    # Step 4: Monitor queue processing
    print("=" * 60)
    print("MONITORING QUEUE PROCESSING")
    print("=" * 60)
    print("Now check queue status with:")
    print(f"  docker exec rabbitmq rabbitmqctl list_queues name messages consumers")
    print("")
    print("Monitor with:")
    print(f"  ./scripts/monitor_rabbitmq_performance.sh 5")
    print("")
    print(f"Expected processing time (est): {success_count / 5:.0f}-{success_count / 2:.0f}s")
    print("(Assuming 2-5 articles/sec throughput)")
    print("")

    return {
        "messages_sent": success_count,
        "errors": error_count,
        "duration": send_duration,
        "rate": success_count / send_duration if send_duration > 0 else 0
    }


if __name__ == "__main__":
    try:
        results = send_messages(NUM_MESSAGES)
        print(f"✅ Load test submission complete!")
        print(f"Check queue processing with: docker exec rabbitmq rabbitmqctl list_queues")
    except KeyboardInterrupt:
        print("\n⚠ Load test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        sys.exit(1)
