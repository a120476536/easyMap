from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QPainter, QFont, QFontMetrics
from PySide6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QGraphicsSimpleTextItem, QGraphicsRectItem, QGraphicsOpacityEffect

from elements import MapElement, ElementType


class ElementItem(QGraphicsObject):
    """画布上的元素图形项：承载 element_id 并可被选中/拖拽。"""

    clicked = Signal(str)

    def __init__(self, element: MapElement):
        super().__init__()
        self.element_id = element.id
        self.element_type = element.type
        self.element_name = element.name
        self._radius = 10.0
        self.setFlags(
            QGraphicsObject.ItemIsSelectable
            | QGraphicsObject.ItemIsMovable
            | QGraphicsObject.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._apply_from_element(element)
        
        # 创建气泡提示（初始隐藏）
        self._create_tooltip()
        
        # 创建名称标签
        self._create_name_label()

    def _apply_from_element(self, element: MapElement) -> None:
        self.setPos(element.pos[0], element.pos[1])

    def _create_tooltip(self):
        """创建气泡提示"""
        self.tooltip = QGraphicsRectItem(self)
        self.tooltip.setRect(QRectF(0, 0, 200, 120))
        self.tooltip.setBrush(QColor(255, 255, 220, 230))
        self.tooltip.setPen(QPen(QColor(200, 200, 180), 1))
        self.tooltip.setZValue(100)
        self.tooltip.setVisible(False)
        
        # 添加阴影效果
        self.tooltip.setPos(20, -140)
        
        # 创建文本项
        self.tooltip_text = QGraphicsSimpleTextItem(self.tooltip)
        self.tooltip_text.setFont(QFont("Arial", 10))
        self.tooltip_text.setBrush(QColor(50, 50, 50))
        self.tooltip_text.setPos(10, 10)
        
    def _create_name_label(self):
        """创建名称标签"""
        self.name_label = QGraphicsSimpleTextItem(self)
        self.name_label.setText(self.element_name)
        self.name_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.name_label.setBrush(QColor(30, 30, 30))
        
        # 计算位置：在图标顶部
        metrics = QFontMetrics(self.name_label.font())
        text_width = metrics.horizontalAdvance(self.element_name)
        text_height = metrics.height()
        
        # 不同类型的元素，名称位置不同
        if "HOUSE" in self.element_type.name:
            self.name_label.setPos(-text_width/2, -25)
        elif "VILLAGE" in self.element_type.name:
            self.name_label.setPos(-text_width/2, -35)
        elif "CITY" in self.element_type.name:
            self.name_label.setPos(-text_width/2, -45)
        elif "COUNTRY" in self.element_type.name:
            self.name_label.setPos(-text_width/2, -35)
        elif "MINE" in self.element_type.name:
            self.name_label.setPos(-text_width/2, -35)
        else:
            self.name_label.setPos(-text_width/2, -25)
            
        self.name_label.setZValue(5)

    def hoverEnterEvent(self, event):
        """鼠标悬停进入事件"""
        # 显示气泡提示
        self.tooltip.setVisible(True)
        
        # 更新气泡内容
        self._update_tooltip_content()
        
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """鼠标悬停离开事件"""
        # 隐藏气泡提示
        self.tooltip.setVisible(False)
        
        super().hoverLeaveEvent(event)

    def _update_tooltip_content(self):
        """更新气泡提示内容"""
        content = f"名称: {self.element_name}\n"
        content += f"类型: {self.element_type.value}\n"
        content += f"ID: {self.element_id[:8]}...\n"
        content += f"位置: ({self.pos().x():.1f}, {self.pos().y():.1f})"
        
        self.tooltip_text.setText(content)

    def boundingRect(self) -> QRectF:
        if "RIVER" in self.element_type.name or "MOUNTAIN" in self.element_type.name:
            if self._path is not None:
                return self._path.boundingRect().adjusted(-5, -5, 5, 5)
        r = self._radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None) -> None:
        # 河流/山川：用线条表示，可整体拖动
        if "RIVER" in self.element_type.name or "MOUNTAIN" in self.element_type.name:
            if self._path is not None:
                if "RIVER" in self.element_type.name:
                    if self.element_type == ElementType.RIVER_SMALL:
                        color = QColor("#2b5d80")
                        width = 2
                    elif self.element_type == ElementType.RIVER_MEDIUM:
                        color = QColor("#1e4a6f")
                        width = 4
                    else:  # RIVER_LARGE
                        color = QColor("#0d3559")
                        width = 6
                else:  # MOUNTAIN
                    if self.element_type == ElementType.MOUNTAIN_SMALL:
                        color = QColor("#5c5247")
                        width = 3
                    elif self.element_type == ElementType.MOUNTAIN_MEDIUM:
                        color = QColor("#4a4238")
                        width = 5
                    else:  # MOUNTAIN_LARGE
                        color = QColor("#383129")
                        width = 7
                pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(self._path)
                return

        painter.setRenderHint(QPainter.Antialiasing)

        # 房屋类型
        if "HOUSE" in self.element_type.name:
            self._paint_house(painter)
            return
            
        # 村庄类型
        if "VILLAGE" in self.element_type.name:
            self._paint_village(painter)
            return
            
        # 城市类型
        if "CITY" in self.element_type.name:
            self._paint_city(painter)
            return
            
        # 国家类型
        if "COUNTRY" in self.element_type.name:
            self._paint_country(painter)
            return
            
        # 矿场类型
        if "MINE" in self.element_type.name:
            self._paint_mine(painter)
            return

        # fallback - 使用简单的图标
        r = self._radius
        painter.setPen(QPen(QColor("#222"), 2))
        painter.setBrush(QBrush(QColor("#f2f2f2")))
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))

    def set_river_polyline(self, element: MapElement) -> None:
        if "RIVER" not in element.type.name:
            self._path = None
            self.update()
            return
        path = QPainterPath()
        if element.polyline:
            x0, y0 = element.polyline[0]
            path.moveTo(x0, y0)
            for (x, y) in element.polyline[1:]:
                path.lineTo(x, y)
        self._path = path
        self.update()

    def set_polyline_from_element(self, element: MapElement) -> None:
        if "RIVER" not in element.type.name and "MOUNTAIN" not in element.type.name:
            self._path = None
            self.update()
            return
        path = QPainterPath()
        pts = element.polyline or [(0, 0), (50, 0)]
        x0, y0 = pts[0]
        path.moveTo(x0, y0)
        for (x, y) in pts[1:]:
            path.lineTo(x, y)
        self._path = path
        self.update()

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        self.clicked.emit(self.element_id)

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    _path: Optional[QPainterPath] = None

    # --- 房屋图标 ---
    def _paint_house(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 1.5))
        
        if self.element_type == ElementType.HOUSE_SMALL:
            painter.setBrush(QColor("#f7f2e8"))
            # 小房子
            painter.drawRect(-r * 0.7, -r * 0.3, r * 1.4, r * 1.4)
            # 屋顶
            roof = QPainterPath()
            roof.moveTo(-r * 0.7, -r * 0.3)
            roof.lineTo(0, -r * 1.0)
            roof.lineTo(r * 0.7, -r * 0.3)
            roof.closeSubpath()
            painter.setBrush(QColor("#c75f3e"))
            painter.drawPath(roof)
            
        elif self.element_type == ElementType.HOUSE_LARGE:
            painter.setBrush(QColor("#f0e6d6"))
            # 大房子
            painter.drawRect(-r * 1.0, -r * 0.5, r * 2.0, r * 1.5)
            # 屋顶
            roof = QPainterPath()
            roof.moveTo(-r * 1.0, -r * 0.5)
            roof.lineTo(0, -r * 1.3)
            roof.lineTo(r * 1.0, -r * 0.5)
            roof.closeSubpath()
            painter.setBrush(QColor("#b84c2e"))
            painter.drawPath(roof)
            # 窗户
            painter.setBrush(QColor("#a8d0e6"))
            painter.drawRect(-r * 0.7, r * 0.1, r * 0.4, r * 0.4)
            painter.drawRect(r * 0.3, r * 0.1, r * 0.4, r * 0.4)
            
        else:  # HOUSE_FANCY
            painter.setBrush(QColor("#e8e0d0"))
            # 豪宅
            painter.drawRect(-r * 1.2, -r * 0.7, r * 2.4, r * 1.7)
            # 复杂屋顶
            roof = QPainterPath()
            roof.moveTo(-r * 1.2, -r * 0.7)
            roof.lineTo(0, -r * 1.8)
            roof.lineTo(r * 1.2, -r * 0.7)
            roof.closeSubpath()
            painter.setBrush(QColor("#a83c1e"))
            painter.drawPath(roof)
            # 多个窗户
            painter.setBrush(QColor("#7eb9d6"))
            for i in range(3):
                painter.drawRect(-r * 0.9 + i * r * 0.9, r * 0.2, r * 0.5, r * 0.5)
            # 门
            painter.setBrush(QColor("#d9cbb8"))
            painter.drawRect(-r * 0.2, r * 0.4, r * 0.4, r * 0.8)

    # --- 村庄图标 ---
    def _paint_village(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 1.5))
        
        if self.element_type == ElementType.VILLAGE_SMALL:
            # 小村庄：2个小房子
            for offset in [(-r * 0.5, 0), (r * 0.5, r * 0.2)]:
                painter.save()
                painter.translate(offset[0], offset[1])
                painter.scale(0.7, 0.7)
                painter.setBrush(QColor("#f7f2e8"))
                painter.drawRect(-r * 0.7, -r * 0.3, r * 1.4, r * 1.4)
                roof = QPainterPath()
                roof.moveTo(-r * 0.7, -r * 0.3)
                roof.lineTo(0, -r * 1.0)
                roof.lineTo(r * 0.7, -r * 0.3)
                roof.closeSubpath()
                painter.setBrush(QColor("#c75f3e"))
                painter.drawPath(roof)
                painter.restore()
            
        elif self.element_type == ElementType.VILLAGE_MEDIUM:
            # 中村庄：3个房子
            offsets = [(-r, 0), (0, r*0.3), (r, 0)]
            for i, offset in enumerate(offsets):
                painter.save()
                painter.translate(offset[0], offset[1])
                painter.scale(0.6, 0.6)
                if i == 1:
                    painter.setBrush(QColor("#f0e6d6"))
                    painter.drawRect(-r * 1.0, -r * 0.5, r * 2.0, r * 1.5)
                    roof = QPainterPath()
                    roof.moveTo(-r * 1.0, -r * 0.5)
                    roof.lineTo(0, -r * 1.3)
                    roof.lineTo(r * 1.0, -r * 0.5)
                    roof.closeSubpath()
                    painter.setBrush(QColor("#b84c2e"))
                    painter.drawPath(roof)
                else:
                    painter.setBrush(QColor("#f7f2e8"))
                    painter.drawRect(-r * 0.7, -r * 0.3, r * 1.4, r * 1.4)
                    roof = QPainterPath()
                    roof.moveTo(-r * 0.7, -r * 0.3)
                    roof.lineTo(0, -r * 1.0)
                    roof.lineTo(r * 0.7, -r * 0.3)
                    roof.closeSubpath()
                    painter.setBrush(QColor("#c75f3e"))
                    painter.drawPath(roof)
                painter.restore()
                
        else:  # VILLAGE_LARGE
            # 大村庄：5个房子
            offsets = [(-r*0.8, -r*0.3), (0, -r*0.5), (r*0.8, -r*0.3), 
                      (-r*0.5, r*0.4), (r*0.5, r*0.4)]
            for i, offset in enumerate(offsets):
                painter.save()
                painter.translate(offset[0], offset[1])
                painter.scale(0.5, 0.5)
                if i == 1:
                    painter.setBrush(QColor("#e8e0d0"))
                    painter.drawRect(-r * 1.2, -r * 0.7, r * 2.4, r * 1.7)
                    roof = QPainterPath()
                    roof.moveTo(-r * 1.2, -r * 0.7)
                    roof.lineTo(0, -r * 1.8)
                    roof.lineTo(r * 1.2, -r * 0.7)
                    roof.closeSubpath()
                    painter.setBrush(QColor("#a83c1e"))
                    painter.drawPath(roof)
                elif i < 3:
                    painter.setBrush(QColor("#f0e6d6"))
                    painter.drawRect(-r * 1.0, -r * 0.5, r * 2.0, r * 1.5)
                    roof = QPainterPath()
                    roof.moveTo(-r * 1.0, -r * 0.5)
                    roof.lineTo(0, -r * 1.3)
                    roof.lineTo(r * 1.0, -r * 0.5)
                    roof.closeSubpath()
                    painter.setBrush(QColor("#b84c2e"))
                    painter.drawPath(roof)
                else:
                    painter.setBrush(QColor("#f7f2e8"))
                    painter.drawRect(-r * 0.7, -r * 0.3, r * 1.4, r * 1.4)
                    roof = QPainterPath()
                    roof.moveTo(-r * 0.7, -r * 0.3)
                    roof.lineTo(0, -r * 1.0)
                    roof.lineTo(r * 0.7, -r * 0.3)
                    roof.closeSubpath()
                    painter.setBrush(QColor("#c75f3e"))
                    painter.drawPath(roof)
                painter.restore()

    # --- 城市图标 ---
    def _paint_city(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 2))
        
        if self.element_type == ElementType.CITY_SMALL:
            # 小城市
            painter.setBrush(QColor("#d0c8b8"))
            painter.drawRect(-r * 2.0, -r * 1.5, r * 4.0, r * 3.0)
            # 城墙
            painter.setBrush(QColor("#887058"))
            painter.drawRect(-r * 2.0, -r * 1.5, r * 4.0, r * 0.5)
            # 主建筑
            painter.setBrush(QColor("#f0e6d6"))
            painter.drawRect(-r * 0.6, -r * 0.4, r * 1.2, r * 1.8)
            # 塔楼
            painter.setBrush(QColor("#c8b8a8"))
            painter.drawRect(-r * 1.5, -r * 0.8, r * 0.5, r * 1.2)
            
        elif self.element_type == ElementType.CITY_MEDIUM:
            # 中城市
            painter.setBrush(QColor("#c8c0b0"))
            painter.drawRect(-r * 3.0, -r * 2.0, r * 6.0, r * 4.0)
            # 双层城墙
            painter.setBrush(QColor("#786048"))
            painter.drawRect(-r * 3.0, -r * 2.0, r * 6.0, r * 0.6)
            # 多个建筑
            for i in range(4):
                painter.setBrush(QColor("#e8e0d0"))
                x = -r * 2.0 + i * r * 1.2
                painter.drawRect(x, -r * 0.5, r * 0.8, r * 1.5)
                
        else:  # CITY_LARGE
            # 大城市
            painter.setBrush(QColor("#c0b8a8"))
            painter.drawRect(-r * 4.0, -r * 2.5, r * 8.0, r * 5.0)
            # 坚固城墙
            painter.setBrush(QColor("#685038"))
            painter.drawRect(-r * 4.0, -r * 2.5, r * 8.0, r * 0.7)
            # 城堡
            painter.setBrush(QColor("#f0e6d6"))
            painter.drawRect(-r * 1.0, -r * 1.0, r * 2.0, r * 2.5)
            # 多个塔楼
            for x in [-r*3.0, -r*1.0, r*1.0, r*3.0]:
                painter.setBrush(QColor("#b8a890"))
                painter.drawRect(x - r*0.3, -r*1.5, r*0.6, r*2.0)

    # --- 国家图标 ---
    def _paint_country(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1a1a1a"), 2))
        
        if self.element_type == ElementType.COUNTRY_SMALL:
            # 小国：带徽章的盾牌
            painter.setBrush(QColor("#d8d8d8"))
            path = QPainterPath()
            path.moveTo(0, -r * 1.5)
            path.quadTo(r * 1.0, -r * 0.5, 0, r * 1.0)
            path.quadTo(-r * 1.0, -r * 0.5, 0, -r * 1.5)
            painter.drawPath(path)
            # 徽章
            painter.setBrush(QColor("#a4b9d6"))
            painter.drawEllipse(-r * 0.4, -r * 0.4, r * 0.8, r * 0.8)
            
        elif self.element_type == ElementType.COUNTRY_MEDIUM:
            # 中国：带王冠的盾牌
            painter.setBrush(QColor("#e0e0e0"))
            painter.drawRect(-r * 1.2, -r * 0.8, r * 2.4, r * 1.6)
            # 王冠
            crown = QPainterPath()
            crown.moveTo(-r * 1.2, -r * 0.8)
            for i in range(5):
                crown.lineTo(-r * 0.9 + i * r * 0.6, -r * 1.5)
                crown.lineTo(-r * 0.6 + i * r * 0.6, -r * 0.8)
            painter.setBrush(QColor("#d4af37"))
            painter.drawPath(crown)
            
        else:  # COUNTRY_LARGE
            # 大国：带剑和盾牌的复杂徽章
            painter.setBrush(QColor("#f0f0f0"))
            painter.drawRect(-r * 1.5, -r * 1.0, r * 3.0, r * 2.0)
            # 剑
            painter.setPen(QPen(QColor("#888"), 3))
            painter.drawLine(0, -r * 1.0, 0, r * 1.0)
            painter.drawLine(-r * 0.3, -r * 0.5, r * 0.3, -r * 0.5)
            # 盾牌
            painter.setPen(QPen(QColor("#1a1a1a"), 2))
            painter.setBrush(QColor("#a4b9d6"))
            painter.drawEllipse(-r * 0.6, -r * 0.6, r * 1.2, r * 1.2)

    # --- 矿场图标 ---
    def _paint_mine(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#2e1d12"), 2))
        
        # 根据矿种改变颜色
        if self.element_type == ElementType.MINE_COAL:
            mine_color = QColor("#333333")
            ore_color = QColor("#666666")
        elif self.element_type == ElementType.MINE_IRON:
            mine_color = QColor("#5c5c5c")
            ore_color = QColor("#b8b8b8")
        elif self.element_type == ElementType.MINE_GOLD:
            mine_color = QColor("#d4af37")
            ore_color = QColor("#ffd700")
        else:  # MINE_GEM
            mine_color = QColor("#4169e1")
            ore_color = QColor("#9370db")
            
        painter.setBrush(mine_color)
        # 矿洞入口
        path = QPainterPath()
        path.moveTo(-r, r * 0.5)
        path.quadTo(0, -r * 0.5, r, r * 0.5)
        path.lineTo(r, r)
        path.lineTo(-r, r)
        path.closeSubpath()
        painter.drawPath(path)
        
        # 矿石
        painter.setBrush(ore_color)
        for i in range(3):
            painter.drawEllipse(-r * 0.5 + i * r * 0.5, r * 0.2, r * 0.3, r * 0.3)