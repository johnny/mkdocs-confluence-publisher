from typing import Dict


class ConfluencePage:
    def __init__(self, id: int, title: str):
        self.id: int = id
        self.title: str = title

    def __repr__(self) -> str:
        return f"ConfluencePage(id={self.id}, title='{self.title}')"

    def __eq__(self, other):
        if not isinstance(other, ConfluencePage):
            return NotImplemented
        return self.id == other.id and self.title == other.title


MD_to_Page = Dict[str, ConfluencePage]
