def mask_account(account_number: str) -> str:
    """Mask an account number, showing only the last 4 digits."""
    if len(account_number) <= 4:
        return account_number
    return "XXXX" + account_number[-4:]


def mask_phone(phone: str) -> str:
    """Mask a phone number, showing only the last 4 digits."""
    if len(phone) <= 4:
        return phone
    return "XXXXX" + phone[-4:]
