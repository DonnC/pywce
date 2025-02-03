class ChatRole:
    AGENT = "agent"
    USER = "user"


ACTIVE_CHATS = [
    "+1234567890",
    "+9876543210",
    "+263771234567"
]

MESSAGES = {
    "+1234567890": [
        {"role": "user", "message": "Hello"},
        {"role": "agent", "message": "How can I help you?"},
        {"role": "user", "message": "I want to know about my order"}
    ],
    "+9876543210": [
        {"role": "user", "message": "Hi there!"},
        {"role": "agent", "message": "Hello! How can I assist you today?"}
    ]
}

# Simulating a database with a dictionary in Python
MOCK_DB = {
    "chats": {
        "+1234567890": {
            "last_message": "Can you provide your order number?",
            "timestamp": "2025-02-02T09:45:00Z"
        },
        "+9876543210": {
            "last_message": "Hello! How can I assist you today?",
            "timestamp": "2025-02-02T08:30:00Z"
        },
        "+263771234567": {
            "last_message": "I need assistance with my account.",
            "timestamp": "2025-02-01T14:20:00Z"
        }
    }
}
