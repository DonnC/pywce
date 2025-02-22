from pywce import AiService

if __name__ == '__main__':
    wa_id = "crm_nikk"
    agent = "CRM Nikk"
    instructions = """You are a seasoned CRM expert for a local bank in Zimbabwe
    working to help clients on their day to day issues. Your main issues are mainly
    - transactional issues
    - loans issues
    - omnichannel issues on ussd, mobile, whatsapp and internet banking platform
    - Any other bank related issues.
    
    You are known for being polite, patience and professional in your conduct.
    """

    ai = AiService(agent, instructions, {})

    print("[Ai] Hi im CRM Nikk, how can i help you?\n")

    while True:
        user = str(input("[User] "))
        response = ai.generate_response(user, wa_id)
        print(f"[Ai] {response}")
