from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


class ElementType(str, Enum):
    # 房屋类型
    HOUSE_SMALL = "小屋"
    HOUSE_LARGE = "大屋"
    HOUSE_FANCY = "豪宅"
    
    # 村庄类型
    VILLAGE_SMALL = "小村庄"
    VILLAGE_MEDIUM = "中村庄"
    VILLAGE_LARGE = "大村庄"
    
    # 城镇类型
    TOWN_SMALL = "小镇"
    TOWN_MEDIUM = "中镇"
    TOWN_LARGE = "大镇"
    
    # 城市类型
    CITY_SMALL = "小城"
    CITY_MEDIUM = "中城"
    CITY_LARGE = "大城"
    
    # 国家类型
    COUNTRY_SMALL = "小国"
    COUNTRY_MEDIUM = "中国"
    COUNTRY_LARGE = "大国"
    
    # 自然地貌
    RIVER_SMALL = "小溪"
    RIVER_MEDIUM = "中河"
    RIVER_LARGE = "大河"
    
    MOUNTAIN_SMALL = "小山"
    MOUNTAIN_MEDIUM = "中山"
    MOUNTAIN_LARGE = "大山"
    
    MINE_COAL = "煤矿"
    MINE_IRON = "铁矿"
    MINE_GOLD = "金矿"
    MINE_GEM = "宝石矿"


def new_id() -> str:
    return uuid4().hex


def default_settings_for(t: ElementType) -> Dict[str, Any]:
    base = {
        "描述": "",
        "阵营/归属": "",
        "人口/规模": "",
        "资源": "",
        "备注": "",
    }
    if "RIVER" in t.name or "MOUNTAIN" in t.name:
        base.update(
            {
                "强度/规模": "中",
                "特殊效果": "",
            }
        )
    if "MINE" in t.name:
        base.update({"矿种": t.value, "产出": ""})
    return base


@dataclass
class MapElement:
    id: str
    type: ElementType
    name: str
    parent_id: Optional[str] = None
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