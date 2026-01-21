from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import os


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
    
    # 自定义类型
    CUSTOM = "自定义"


def new_id() -> str:
    return uuid4().hex


def default_settings_for(t: ElementType) -> Dict[str, Any]:
    # 基础设置
    base = {
        "描述": "",
        "阵营/归属": "",
        "人口/规模": "",
        "资源": "",
        "备注": "",
        "图片路径": "",  # 新增图片路径字段
        "图片宽度": "64",  # 新增图片宽度字段，默认64
        "图片高度": "64",  # 新增图片高度字段，默认64
    }
    
    if t in {ElementType.RIVER_SMALL, ElementType.RIVER_MEDIUM, ElementType.RIVER_LARGE,
             ElementType.MOUNTAIN_SMALL, ElementType.MOUNTAIN_MEDIUM, ElementType.MOUNTAIN_LARGE}:
        base.update(
            {
                "强度/规模": "中",
                "特殊效果": "",
            }
        )
    
    if t in {ElementType.MINE_COAL, ElementType.MINE_IRON, ElementType.MINE_GOLD, ElementType.MINE_GEM}:
        base.update({"矿种": t.value, "产出": ""})
    
    if t == ElementType.CUSTOM:
        base.update({
            "自定义类型": "",
            "图标大小": "32",
            "显示名称": "是",
        })
    
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
    
    def get_image_path(self) -> Optional[str]:
        """获取元素的图片路径"""
        return self.settings.get("图片路径", "")
    
    def set_image_path(self, path: str) -> None:
        """设置元素的图片路径"""
        self.settings["图片路径"] = path
    
    def get_image_size(self) -> Tuple[int, int]:
        """获取图片显示尺寸"""
        try:
            width = int(self.settings.get("图片宽度", "64"))
            height = int(self.settings.get("图片高度", "64"))
            return max(1, width), max(1, height)  # 确保最小为1
        except (ValueError, TypeError):
            return 64, 64  # 默认值