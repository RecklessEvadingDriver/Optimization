import re
from typing import List


def parse_bot_tokens(token_str: str | None) -> List[str]:
    if not token_str:
        return []
    return [tok.strip() for tok in re.split(r"[,\s]+", token_str) if tok.strip()]
