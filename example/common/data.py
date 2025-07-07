# dummy constant data

class LocalDataSource:
    available_booking_slots = [
        {
            "id": "10_00",
            "title": "Morning",
            "description": "Get ahead of your schedules",
            "metadata": "10:00 hrs",
            "enabled": True
        },
        {
            "id": "12_00",
            "title": "Midday",
            "description": "Bright sun, escape the morning breeze",
            "metadata": "12:00 hrs",
            "enabled": False
        },
        {
            "id": "15_00",
            "title": "Evening",
            "description": "Beat the daily traffic",
            "metadata": "15:00 hrs",
            "enabled": True
        }
    ]
    flow_time_slots = {
        "screen": "BOOK_SCREEN",
        "data": {
            "time_slots": available_booking_slots,
            "is_dropdown_visible": True
        }
    }
