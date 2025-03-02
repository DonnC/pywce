import asyncio

from pywce import AiService


async def main():
    wa_id = "crm_nikk"
    agent = "CRM Niki"
    instructions = """You are a seasoned CRM expert for a local bank in Zimbabwe
    working to help clients on their day to day issues. Your main issues are mainly
    - transactional issues
    - loans issues
    - omnichannel issues on ussd, mobile, whatsapp and internet banking platform
    - Any other bank related issues.

    You are a polite, patient and professional expert in your conduct.
    """

    ai = AiService(agent, instructions, {})

    print("[Ai] Hi I'm CRM Niki, how can I help you today?\n")

    while True:
        user = input("[User] ")
        response = await ai.generate_response(user, wa_id)
        print(f"[Ai] {response}")


if __name__ == "__main__":
    asyncio.run(main())