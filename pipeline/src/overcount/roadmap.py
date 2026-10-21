"""The learning path: roadmap nodes, each owning some topics and some counting methods."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .schema import Slug
from .taxonomy import METHOD_INFO, METHODS, TOPICS, Method, Topic


class Node(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Slug
    title: str = Field(min_length=1)
    blurb: str = Field(min_length=1)
    topics: list[Topic] = Field(min_length=1)
    methods: list[Method] = []


class Roadmap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    nodes: list[Node] = Field(min_length=1)

    @model_validator(mode="after")
    def each_topic_and_method_has_one_home(self) -> "Roadmap":
        groups: list[tuple[str, tuple[str, ...], list[str]]] = [
            ("topic", TOPICS, [t for n in self.nodes for t in n.topics]),
            ("method", METHODS, [m for n in self.nodes for m in n.methods]),
        ]
        for name, everything, placed in groups:
            twice = sorted({x for x in placed if placed.count(x) > 1})
            missing = sorted(set(everything) - set(placed))
            if twice:
                raise ValueError(f"each {name} belongs to exactly one roadmap node; repeated: {twice}")
            if missing:
                raise ValueError(f"every {name} needs a roadmap node; missing: {missing}")
        return self


def load_roadmap(path: Path) -> Roadmap:
    return Roadmap.model_validate(yaml.safe_load(path.read_text()))


def roadmap_json(roadmap: Roadmap) -> list[dict[str, Any]]:
    """The roadmap as published in index.json, with each method's display name and blurb."""
    return [
        {
            "id": node.id,
            "title": node.title,
            "blurb": node.blurb,
            "topics": list(node.topics),
            "methods": [
                {"id": method, "name": METHOD_INFO[method][0], "blurb": METHOD_INFO[method][1]}
                for method in node.methods
            ],
        }
        for node in roadmap.nodes
    ]
