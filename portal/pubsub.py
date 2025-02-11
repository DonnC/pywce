"""
A test script for the redis pub/sub

You can use this after running the live support portal
to simulate message requests from engine
"""

import asyncio
import json
from random import shuffle, randint

import redis.asyncio as redis

CHATS = ["263778060126", "2637790123456", "263770123456"]

REDIS_URL = "redis://localhost"
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
        r = redis.from_url(REDIS_URL)

        # Set up pub/sub
        async with r.pubsub() as pubsub:
            shuffle(CHATS)
            chat = CHATS[randint(0, len(CHATS) - 1)]

            await pubsub.psubscribe("webhook:*")

            # Start the reader task
            future = asyncio.create_task(reader(pubsub))

            # Publish messages to channels
            await r.publish(
                "webhook:incoming",
                json.dumps({
                    "recipient_id": chat,
                    "message": f"Im here waiting for support",
                })
            )

            await r.publish(
                "webhook:outgoing",
                json.dumps({
                    "recipient_id": chat,
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
