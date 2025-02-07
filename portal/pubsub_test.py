import asyncio
import json

import redis.asyncio as redis

STOPWORD = "STOP"

async def reader(channel: redis.client.PubSub):
    while True:
        try:
            message = await channel.get_message(ignore_subscribe_messages=True, timeout=None)
            if message is not None:
                print(f"(Reader) Message Received: {message}")
                if message["data"].decode() == STOPWORD:
                    print("(Reader) STOP")
                    break

        except asyncio.CancelledError:
            # Handle task cancellation (if needed)
            print("Reader task was cancelled.")
            break

        except Exception as e:
            # Log any other errors
            print(f"(Reader) Error: {e}")

async def main():
    try:
        # Connect to Redis
        r = redis.from_url("redis://localhost")

        # Set up pub/sub
        async with r.pubsub() as pubsub:
            await pubsub.psubscribe("webhook:*")

            # Start the reader task
            future = asyncio.create_task(reader(pubsub))

            # Publish messages to channels
            await r.publish(
                "webhook:incoming",
                json.dumps({
                    "recipient_id": "263770123456",
                    "message": f"Im here waiting for support",
                })
            )

            await r.publish(
                "webhook:outgoing",
                json.dumps({
                    "recipient_id": "263770123456",
                    "type": "MESSAGE",
                    "message": "Hi, this is a test outgoing"
                })
            )

            await r.publish("webhook:outgoing", STOPWORD)

            # Wait for the reader task to finish
            await future

    except Exception as e:
        print(f"Error connecting to Redis or subscribing: {e}")


if __name__ == "__main__":
    asyncio.run(main())
