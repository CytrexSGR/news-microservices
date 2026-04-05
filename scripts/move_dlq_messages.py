#!/usr/bin/env python3
"""
Move messages from DLQ back to main queue for reprocessing.
"""
import pika
import sys

def move_messages(source_queue: str, dest_queue: str, max_messages: int = 100):
    """Move messages from source queue to destination queue."""

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=pika.PlainCredentials('guest', 'guest')
        )
    )
    channel = connection.channel()

    moved = 0
    failed = 0

    print(f"Moving messages from {source_queue} to {dest_queue}...")

    for _ in range(max_messages):
        method, properties, body = channel.basic_get(queue=source_queue, auto_ack=False)

        if method is None:
            break

        try:
            # Publish to destination queue
            channel.basic_publish(
                exchange='',
                routing_key=dest_queue,
                body=body,
                properties=properties
            )

            # Acknowledge the message from source queue
            channel.basic_ack(delivery_tag=method.delivery_tag)
            moved += 1
            print(f"Moved message {moved}")

        except Exception as e:
            print(f"Failed to move message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            failed += 1

    connection.close()

    print(f"\nSummary:")
    print(f"  Moved: {moved}")
    print(f"  Failed: {failed}")

    return moved, failed


if __name__ == "__main__":
    source = "analysis_v3_requests_queue_dlq"
    dest = "analysis_v3_requests_queue"

    if len(sys.argv) > 1:
        max_msgs = int(sys.argv[1])
    else:
        max_msgs = 100

    moved, failed = move_messages(source, dest, max_msgs)
    sys.exit(0 if failed == 0 else 1)
