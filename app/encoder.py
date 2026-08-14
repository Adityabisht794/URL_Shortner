ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(num: int) -> str:
    """Turn a DB auto-increment id into a short base62 code."""
    if num == 0:
        return ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode(code: str) -> int:
    num = 0
    for char in code:
        num = num * BASE + ALPHABET.index(char)
    return num
