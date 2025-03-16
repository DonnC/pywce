from datetime import datetime

def tell_the_date():
    """
    Call this tool when the user wants to know the date.

    Returns:
        str: The current date
    """
    print("== tell_the_date ==> tool called")
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"The date is {current_date}"