from typing import Optional
from dataclasses import dataclass


@dataclass
class CheckApiConfig:
    suite: str
    version: Optional[str] = None
    dry: bool = False
