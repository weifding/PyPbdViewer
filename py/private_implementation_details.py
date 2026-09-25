"""FNV-1a 字符串哈希，对应 C# PrivateImplementationDetails."""


def compute_string_hash(text: str) -> int:
    """FNV-1a 32-bit 哈希."""
    if not text:
        return -1 & 0xFFFFFFFF
    hash_val = 2166136261
    for ch in text:
        hash_val ^= ord(ch)
        hash_val = (hash_val * 16777619) & 0xFFFFFFFF
    return hash_val
