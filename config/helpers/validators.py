import re


def validate_name(name):
    if not name:
        return False

    if len(name.strip()) < 4:
        return False

    return True



def validate_email(email):
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    return re.match(pattern, email) is not None



def validate_password(password):
    if not password:
        return False

    if len(password) < 8:
        return False

    if not re.search(r"[A-Za-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True