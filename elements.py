from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


class ElementType(str, Enum):
    HOUSE = "房屋"
    VILLAGE = "村庄"
    TOWN = "城镇"
    CITY = "城市"
    COUNTRY = "国家"

    RIVER = "河流"
    MOUNTAIN = "山川"
    MINE = "矿场"


def new_id() -> str:
    return uuid4().hex


def default_settings_for(t: ElementType) -> Dict[str, Any]:
    # 这里先做最小可用设定，后续你可以按“玄幻/仙侠”扩展字段
    base = {
        "描述": "",
        "阵营/归属": "",
        "人口/规模": "",
        "资源": "",
        "备注": "",
    }
    if t in {ElementType.RIVER, ElementType.MOUNTAIN}:
        base.update(
            {
                "强度/规模": "中",
                "特殊效果": "",
            }
        )
    if t == ElementType.MINE:
        base.update({"矿种": "灵石/铁/金/秘银", "产出": ""})
    return base


@dataclass
class MapElement:
    id: str
    type: ElementType
    name: str
    parent_id: Optional[str] = None
    # 几何：点状元素用 pos；线状元素用 polyline
    pos: Tuple[float, float] = (0.0, 0.0)
    polyline: List[Tuple[float, float]] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        t: ElementType,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
        pos: Tuple[float, float] = (0.0, 0.0),
    ) -> "MapElement":
        eid = new_id()
        return MapElement(
            id=eid,
            type=t,
            name=name or f"{t.value}-{eid[:4]}",
            parent_id=parent_id,
            pos=pos,
            settings=default_settings_for(t),
        )
