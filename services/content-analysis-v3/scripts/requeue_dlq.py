#!/usr/bin/env python3
"""
Requeue messages from DLQ to main queue after schema fix.
"""
import pika
import sys

# RabbitMQ connection
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost', port=5672)
)
channel = connection.channel()

DLQ_NAME = 'analysis_v3_requests_queue_dlq'
MAIN_QUEUE = 'analysis_v3_requests_queue'

print(f"🔄 Requeuing messages from {DLQ_NAME} to {MAIN_QUEUE}...")

requeued = 0
failed = 0

try:
    while True:
        # Get one message from DLQ
        method, properties, body = channel.basic_get(queue=DLQ_NAME, auto_ack=False)

        if method is None:
            break  # No more messages

        try:
            # Publish to main queue (without x-death headers to avoid loop)
            new_properties = pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type=properties.content_type
            )

            channel.basic_publish(
                exchange='',
                routing_key=MAIN_QUEUE,
                body=body,
                properties=new_properties
            )

            # Acknowledge (remove from DLQ)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            requeued += 1

            if requeued % 10 == 0:
                print(f"  ✓ Requeued {requeued} messages...")

        except Exception as e:
            print(f"  ✗ Failed to requeue message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            failed += 1

finally:
    connection.close()

print(f"\n✅ Done! Requeued: {requeued}, Failed: {failed}")
print(f"These messages will now be reprocessed with the fixed schema.")
