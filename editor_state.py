from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from elements import MapElement, ElementType


@dataclass
class EditorState:
    """编辑器的单一事实来源：所有元素及其层级、选中状态。"""

    elements: Dict[str, MapElement] = field(default_factory=dict)
    selected_id: Optional[str] = None

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

