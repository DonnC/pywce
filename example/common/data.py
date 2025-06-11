# dummy constant data

class LocalDataSource:
    expected_flow_token = "my_secure_token_at_123"
    init_response = {
        "screen": "LOAN",
        "data": {
            "tenure": [
                {
                    "id": "p12",
                    "title": "12 pywce"
                },
                {
                    "id": "p24",
                    "title": "24 pywce"
                }
            ],
            "amount": [
                {
                    "id": "am1",
                    "title": "ZWG 5,000"
                },
                {
                    "id": "am2",
                    "title": "ZWG 3,20,000"
                }
            ],
            "emi": "ZWG 3,000",
            "rate": "8.3% pa",
            "fee": "600"
        }
    }
