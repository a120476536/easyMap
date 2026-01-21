from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path

from PySide6.QtGui import QColor

from elements import MapElement, ElementType


@dataclass
class EditorState:
    """编辑器的单一事实来源：所有元素及其层级、选中状态。"""

    elements: Dict[str, MapElement] = field(default_factory=dict)
    selected_id: Optional[str] = None
    # 添加底图设置
    base_color: QColor = field(default_factory=lambda: QColor("#d9d9d9"))
    contrast: float = 0.75

    def add_element(self, element: MapElement) -> None:
        self.elements[element.id] = element
        self.selected_id = element.id

    def get(self, element_id: Optional[str]) -> Optional[MapElement]:
        if not element_id:
            return None
        return self.elements.get(element_id)

    def children_of(self, parent_id: Optional[str]) -> List[MapElement]:
        return [e for e in self.elements.values() if e.parent_id == parent_id]

    def delete_element_recursive(self, element_id: str) -> None:
        # 删除子孙
        for child in list(self.children_of(element_id)):
            self.delete_element_recursive(child.id)
        # 删除自身
        if element_id in self.elements:
            del self.elements[element_id]
        if self.selected_id == element_id:
            self.selected_id = None

    def set_selected(self, element_id: Optional[str]) -> None:
        self.selected_id = element_id if element_id in self.elements else None

    def update_name(self, element_id: str, name: str) -> None:
        e = self.elements.get(element_id)
        if e:
            e.name = name

    def update_setting(self, element_id: str, key: str, value: str) -> None:
        e = self.elements.get(element_id)
        if e:
            e.settings[key] = value

    def update_parent(self, element_id: str, parent_id: Optional[str]) -> None:
        e = self.elements.get(element_id)
        if e:
            e.parent_id = parent_id

    def create_element(
        self,
        t: ElementType,
        parent_id: Optional[str] = None,
        name: Optional[str] = None,
        x: float = 0.0,
        y: float = 0.0,
    ) -> MapElement:
        e = MapElement.create(t=t, name=name, parent_id=parent_id, pos=(x, y))
        self.add_element(e)
        return e
    
    def to_dict(self) -> Dict[str, Any]:
        """将编辑器状态转换为字典（用于序列化）"""
        return {
            "elements": [element.to_dict() for element in self.elements.values()],
            "selected_id": self.selected_id,
            "background": {
                "color": self.base_color.name(),  # 保存为十六进制字符串，如"#d9d9d9"
                "contrast": self.contrast
            }
        }
    
    def load_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载编辑器状态（用于反序列化）"""
        self.elements.clear()
        for element_data in data["elements"]:
            element = MapElement.from_dict(element_data)
            self.elements[element.id] = element
        self.selected_id = data.get("selected_id")
        
        # 加载背景设置
        if "background" in data:
            bg_data = data["background"]
            if "color" in bg_data:
                self.base_color = QColor(bg_data["color"])
            if "contrast" in bg_data:
                self.contrast = bg_data["contrast"]
    
    def save_to_file(self, filepath: Path) -> bool:
        """保存状态到文件"""
        try:
            data = self.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def load_from_file(self, filepath: Path) -> bool:
        """从文件加载状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.load_from_dict(data)
            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False
    
    def clear(self) -> None:
        """清空状态"""
        self.elements.clear()
        self.selected_id = None
        self.base_color = QColor("#d9d9d9")
        self.contrast = 0.75
    
    def set_background(self, color: QColor, contrast: float) -> None:
        """设置背景颜色和对比度"""
        self.base_color = color
        self.contrast = contrast