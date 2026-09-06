"""
ORM / dataclass models shared across all phases.
These are the canonical Python objects — JSON serialisation lives here too.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Resource:
    title: str
    url: str
    type: str           # "video" | "article" | "repo" | "book"
    description: str
    is_free: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Checkpoint:
    week: int
    title: str
    description: str
    criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Module:
    id: str
    week_start: int
    week_end: int
    title: str
    description: str
    concepts: list[str]
    resources: list[Resource]
    checkpoint: Checkpoint
    project: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class LearningPath:
    session_id: str
    topic: str
    skill_level: str
    total_weeks: int
    modules: list[Module]
    prerequisites: list[str]
    final_project: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "LearningPath":
        modules = []
        for m in data["modules"]:
            resources = [Resource(**r) for r in m["resources"]]
            checkpoint = Checkpoint(**m["checkpoint"])
            modules.append(Module(
                **{k: v for k, v in m.items() if k not in ("resources", "checkpoint")},
                resources=resources,
                checkpoint=checkpoint,
            ))
        return cls(
            **{k: v for k, v in data.items() if k != "modules"},
            modules=modules,
        )
