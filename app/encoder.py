"""
Base62 encoder.

Level 1 strategy: let SQLite's AUTOINCREMENT hand out the next integer id,
then encode that id as base62. This is deliberately the simplest possible
ID-generation strategy - and also the first thing that breaks the moment
you want more than one database instance (see LIMITATIONS.md, section 1).
"""

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)


def encode(num: int) -> str:
    if num == 0:
        return ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode(short_code: str) -> int:
    num = 0
    for char in short_code:
        num = num * BASE + ALPHABET.index(char)
    return num
