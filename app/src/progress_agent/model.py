"""能力模型资产的加载。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Union

ModelPath = Union[str, Path]

DEFAULT_ABILITY_FILE = "abilities/agent-app-developer.v0.1.json"


@dataclass(frozen=True)
class AbilityItem:
    """单个能力项。"""

    id: str
    name: str
    description: str
    detection_methods: list[str]
    detection_note: str


@dataclass(frozen=True)
class AbilityDimension:
    """能力维度及其下属能力项。"""

    id: str
    name: str
    description: str
    items: list[AbilityItem]


@dataclass(frozen=True)
class AbilityModel:
    """完整能力模型。"""

    role_label: str
    model_version: str
    dimensions: list[AbilityDimension]

    @property
    def items(self) -> list[AbilityItem]:
        return [item for dimension in self.dimensions for item in dimension.items]


def repo_root() -> Path:
    """返回仓库根目录（progress_agent/）。"""

    return Path(__file__).resolve().parents[3]


def default_model_path() -> Path:
    return repo_root() / DEFAULT_ABILITY_FILE


def load_model(path: ModelPath | None = None) -> AbilityModel:
    """从 JSON 加载能力模型。path 缺省时使用仓库内默认模型。"""

    model_file = Path(path) if path else default_model_path()
    raw = json.loads(model_file.read_text(encoding="utf-8"))

    dimensions = []
    for dimension_raw in raw["dimensions"]:
        items = [AbilityItem(**item_raw) for item_raw in dimension_raw["items"]]
        dimensions.append(
            AbilityDimension(
                id=dimension_raw["id"],
                name=dimension_raw["name"],
                description=dimension_raw["description"],
                items=items,
            )
        )

    return AbilityModel(
        role_label=raw["role_label"],
        model_version=raw["model_version"],
        dimensions=dimensions,
    )
