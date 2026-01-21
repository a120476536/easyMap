from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QPainter, QFont, QFontMetrics, QPixmap, QImage
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
        self.element = element  # 保存元素的引用，用于更新图片尺寸
        
        self._apply_from_element(element)
        
        # 获取项目根目录
        self.project_root = Path(__file__).parent
        
        # 图片相关
        self.original_pixmap = None  # 原始图片
        self.display_pixmap = None   # 显示用（调整大小后的）图片
        self._load_image()
        
        # 创建气泡提示（初始隐藏）
        self._create_tooltip()
        
        # 创建名称标签
        self._create_name_label()

    def _apply_from_element(self, element: MapElement) -> None:
        self.setPos(element.pos[0], element.pos[1])

    def _load_image(self):
        """根据元素设置加载图片"""
        # 1. 首先尝试加载自定义图片
        image_path = self.element.get_image_path()
        if image_path and image_path.strip():
            # 清理路径中的可能空格
            image_path = image_path.strip()
            
            # 尝试构建完整路径
            full_path = None
            
            # 如果路径已经是绝对路径
            if Path(image_path).is_absolute():
                full_path = Path(image_path)
            else:
                # 尝试项目根目录下的路径
                full_path = self.project_root / image_path
                
                # 如果文件不存在，尝试在imgs/custom目录下查找
                if not full_path.exists():
                    # 如果路径是纯文件名，尝试在imgs/custom目录下
                    if '/' not in image_path and '\\' not in image_path:
                        custom_path = self.project_root / "imgs" / "custom" / image_path
                        if custom_path.exists():
                            full_path = custom_path
                    # 如果路径以custom/开头
                    elif image_path.startswith("custom/"):
                        custom_path = self.project_root / "imgs" / image_path
                        if custom_path.exists():
                            full_path = custom_path
            
            if full_path and full_path.exists():
                pixmap = QPixmap(str(full_path))
                if not pixmap.isNull():
                    self.original_pixmap = pixmap
                    self._resize_image()
                    return
        
        # 2. 尝试加载系统默认图片
        self._load_default_image()

    def _resize_image(self):
        """根据元素设置调整图片大小"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return
            
        width, height = self.element.get_image_size()
        
        if width > 0 and height > 0:
            self.display_pixmap = self.original_pixmap.scaled(
                width, height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            self.display_pixmap = self.original_pixmap

    def _load_default_image(self):
        """加载系统默认图片（仅当没有自定义图片时调用）"""
        img_dir = self.project_root / "imgs"
        
        type_to_image = {
            ElementType.HOUSE_SMALL: "house_small.png",
            ElementType.HOUSE_LARGE: "house_large.png",
            ElementType.HOUSE_FANCY: "house_fancy.png",
            ElementType.VILLAGE_SMALL: "village_small.png",
            ElementType.VILLAGE_MEDIUM: "village_medium.png",
            ElementType.VILLAGE_LARGE: "village_large.png",
            ElementType.CITY_SMALL: "city_small.png",
            ElementType.CITY_MEDIUM: "city_medium.png",
            ElementType.CITY_LARGE: "city_large.png",
            ElementType.COUNTRY_SMALL: "country_small.png",
            ElementType.COUNTRY_MEDIUM: "country_medium.png",
            ElementType.COUNTRY_LARGE: "country_large.png",
            ElementType.RIVER_SMALL: "river_small.png",
            ElementType.RIVER_MEDIUM: "river_medium.png",
            ElementType.RIVER_LARGE: "river_large.png",
            ElementType.MOUNTAIN_SMALL: "mountain_small.png",
            ElementType.MOUNTAIN_MEDIUM: "mountain_medium.png",
            ElementType.MOUNTAIN_LARGE: "mountain_large.png",
            ElementType.MINE_COAL: "mine_coal.png",
            ElementType.MINE_IRON: "mine_iron.png",
            ElementType.MINE_GOLD: "mine_gold.png",
            ElementType.MINE_GEM: "mine_gem.png",
        }
        
        image_name = type_to_image.get(self.element_type)
        if image_name:
            img_path = img_dir / image_name
            if img_path.exists():
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    self.original_pixmap = pixmap
                    self._resize_image()
                    return
        
        # 3. 创建默认图标
        self._create_default_icon()

    def _create_default_icon(self):
        """创建默认图标"""
        width, height = self.element.get_image_size()
        size = max(width, height, 64)
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景圆形
        painter.setBrush(QColor("#e0e0e0"))
        painter.setPen(QPen(QColor("#808080"), 2))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # 绘制元素类型简写
        font_size = min(14, size//4)
        painter.setFont(QFont("Arial", font_size, QFont.Bold))
        painter.setPen(QColor("#404040"))
        
        type_text = "?"
        if self.element_type == ElementType.CUSTOM:
            type_text = "自"
        elif "HOUSE" in self.element_type.name:
            type_text = "房"
        elif "VILLAGE" in self.element_type.name:
            type_text = "村"
        elif "CITY" in self.element_type.name:
            type_text = "城"
        elif "COUNTRY" in self.element_type.name:
            type_text = "国"
        elif "RIVER" in self.element_type.name:
            type_text = "河"
        elif "MOUNTAIN" in self.element_type.name:
            type_text = "山"
        elif "MINE" in self.element_type.name:
            type_text = "矿"
            
        painter.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, type_text)
        painter.end()
        
        self.original_pixmap = pixmap
        self.display_pixmap = pixmap

    def update_display_size(self):
        """更新图片显示尺寸"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            self._resize_image()
            self.update()
            self._update_name_label_position()

    def _update_name_label_position(self):
        """更新名称标签位置"""
        if not hasattr(self, 'name_label'):
            return
            
        metrics = QFontMetrics(self.name_label.font())
        text_width = metrics.horizontalAdvance(self.element_name)
        text_height = metrics.height()
        
        if self.display_pixmap and not self.display_pixmap.isNull():
            self.name_label.setPos(-text_width/2, -self.display_pixmap.height()/2 - text_height - 5)
        else:
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

    def _create_tooltip(self):
        """创建气泡提示"""
        self.tooltip = QGraphicsRectItem(self)
        self.tooltip.setRect(QRectF(0, 0, 220, 140))
        self.tooltip.setBrush(QColor(255, 255, 220, 230))
        self.tooltip.setPen(QPen(QColor(200, 200, 180), 1))
        self.tooltip.setZValue(100)
        self.tooltip.setVisible(False)
        self.tooltip.setPos(20, -160)
        
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
        self._update_name_label_position()
        self.name_label.setZValue(5)

    def hoverEnterEvent(self, event):
        """鼠标悬停进入事件"""
        self.tooltip.setVisible(True)
        self._update_tooltip_content()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """鼠标悬停离开事件"""
        self.tooltip.setVisible(False)
        super().hoverLeaveEvent(event)

    def _update_tooltip_content(self):
        """更新气泡提示内容"""
        content = f"名称: {self.element_name}\n"
        content += f"类型: {self.element_type.value}\n"
        content += f"ID: {self.element_id[:8]}...\n"
        content += f"位置: ({self.pos().x():.1f}, {self.pos().y():.1f})"
        
        if self.original_pixmap and not self.original_pixmap.isNull():
            original_width = self.original_pixmap.width()
            original_height = self.original_pixmap.height()
            display_width = self.display_pixmap.width() if self.display_pixmap else original_width
            display_height = self.display_pixmap.height() if self.display_pixmap else original_height
            
            image_path = self.element.get_image_path()
            if image_path:
                content += f"\n图片: {Path(image_path).name}"
            content += f"\n原尺寸: {original_width}×{original_height}"
            content += f"\n显示尺寸: {display_width}×{display_height}"
        
        self.tooltip_text.setText(content)

    def boundingRect(self) -> QRectF:
        if self.display_pixmap and not self.display_pixmap.isNull():
            width = self.display_pixmap.width()
            height = self.display_pixmap.height()
            return QRectF(-width/2, -height/2, width, height)
        
        if "RIVER" in self.element_type.name or "MOUNTAIN" in self.element_type.name:
            if self._path is not None:
                return self._path.boundingRect().adjusted(-5, -5, 5, 5)
        
        r = self._radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None) -> None:
        # 如果有图片，直接绘制图片
        if self.display_pixmap and not self.display_pixmap.isNull():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            width = self.display_pixmap.width()
            height = self.display_pixmap.height()
            painter.drawPixmap(
                QRectF(-width/2, -height/2, width, height),
                self.display_pixmap,
                QRectF(0, 0, width, height)
            )
            return
        
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

        # 自定义类型或未处理类型：绘制默认图标
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

    def _paint_house(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 1.5))
        
        if self.element_type == ElementType.HOUSE_SMALL:
            painter.setBrush(QColor("#f7f2e8"))
            painter.drawRect(-r * 0.7, -r * 0.3, r * 1.4, r * 1.4)
            roof = QPainterPath()
            roof.moveTo(-r * 0.7, -r * 0.3)
            roof.lineTo(0, -r * 1.0)
            roof.lineTo(r * 0.7, -r * 0.3)
            roof.closeSubpath()
            painter.setBrush(QColor("#c75f3e"))
            painter.drawPath(roof)
            
        elif self.element_type == ElementType.HOUSE_LARGE:
            painter.setBrush(QColor("#f0e6d6"))
            painter.drawRect(-r * 1.0, -r * 0.5, r * 2.0, r * 1.5)
            roof = QPainterPath()
            roof.moveTo(-r * 1.0, -r * 0.5)
            roof.lineTo(0, -r * 1.3)
            roof.lineTo(r * 1.0, -r * 0.5)
            roof.closeSubpath()
            painter.setBrush(QColor("#b84c2e"))
            painter.drawPath(roof)
            painter.setBrush(QColor("#a8d0e6"))
            painter.drawRect(-r * 0.7, r * 0.1, r * 0.4, r * 0.4)
            painter.drawRect(r * 0.3, r * 0.1, r * 0.4, r * 0.4)
            
        else:  # HOUSE_FANCY
            painter.setBrush(QColor("#e8e0d0"))
            painter.drawRect(-r * 1.2, -r * 0.7, r * 2.4, r * 1.7)
            roof = QPainterPath()
            roof.moveTo(-r * 1.2, -r * 0.7)
            roof.lineTo(0, -r * 1.8)
            roof.lineTo(r * 1.2, -r * 0.7)
            roof.closeSubpath()
            painter.setBrush(QColor("#a83c1e"))
            painter.drawPath(roof)
            painter.setBrush(QColor("#7eb9d6"))
            for i in range(3):
                painter.drawRect(-r * 0.9 + i * r * 0.9, r * 0.2, r * 0.5, r * 0.5)
            painter.setBrush(QColor("#d9cbb8"))
            painter.drawRect(-r * 0.2, r * 0.4, r * 0.4, r * 0.8)

    def _paint_village(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 1.5))
        
        if self.element_type == ElementType.VILLAGE_SMALL:
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

    def _paint_city(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 2))
        
        if self.element_type == ElementType.CITY_SMALL:
            painter.setBrush(QColor("#d0c8b8"))
            painter.drawRect(-r * 2.0, -r * 1.5, r * 4.0, r * 3.0)
            painter.setBrush(QColor("#887058"))
            painter.drawRect(-r * 2.0, -r * 1.5, r * 4.0, r * 0.5)
            painter.setBrush(QColor("#f0e6d6"))
            painter.drawRect(-r * 0.6, -r * 0.4, r * 1.2, r * 1.8)
            painter.setBrush(QColor("#c8b8a8"))
            painter.drawRect(-r * 1.5, -r * 0.8, r * 0.5, r * 1.2)
            
        elif self.element_type == ElementType.CITY_MEDIUM:
            painter.setBrush(QColor("#c8c0b0"))
            painter.drawRect(-r * 3.0, -r * 2.0, r * 6.0, r * 4.0)
            painter.setBrush(QColor("#786048"))
            painter.drawRect(-r * 3.0, -r * 2.0, r * 6.0, r * 0.6)
            for i in range(4):
                painter.setBrush(QColor("#e8e0d0"))
                x = -r * 2.0 + i * r * 1.2
                painter.drawRect(x, -r * 0.5, r * 0.8, r * 1.5)
                
        else:  # CITY_LARGE
            painter.setBrush(QColor("#c0b8a8"))
            painter.drawRect(-r * 4.0, -r * 2.5, r * 8.0, r * 5.0)
            painter.setBrush(QColor("#685038"))
            painter.drawRect(-r * 4.0, -r * 2.5, r * 8.0, r * 0.7)
            painter.setBrush(QColor("#f0e6d6"))
            painter.drawRect(-r * 1.0, -r * 1.0, r * 2.0, r * 2.5)
            for x in [-r*3.0, -r*1.0, r*1.0, r*3.0]:
                painter.setBrush(QColor("#b8a890"))
                painter.drawRect(x - r*0.3, -r*1.5, r*0.6, r*2.0)

    def _paint_country(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1a1a1a"), 2))
        
        if self.element_type == ElementType.COUNTRY_SMALL:
            painter.setBrush(QColor("#d8d8d8"))
            path = QPainterPath()
            path.moveTo(0, -r * 1.5)
            path.quadTo(r * 1.0, -r * 0.5, 0, r * 1.0)
            path.quadTo(-r * 1.0, -r * 0.5, 0, -r * 1.5)
            painter.drawPath(path)
            painter.setBrush(QColor("#a4b9d6"))
            painter.drawEllipse(-r * 0.4, -r * 0.4, r * 0.8, r * 0.8)
            
        elif self.element_type == ElementType.COUNTRY_MEDIUM:
            painter.setBrush(QColor("#e0e0e0"))
            painter.drawRect(-r * 1.2, -r * 0.8, r * 2.4, r * 1.6)
            crown = QPainterPath()
            crown.moveTo(-r * 1.2, -r * 0.8)
            for i in range(5):
                crown.lineTo(-r * 0.9 + i * r * 0.6, -r * 1.5)
                crown.lineTo(-r * 0.6 + i * r * 0.6, -r * 0.8)
            painter.setBrush(QColor("#d4af37"))
            painter.drawPath(crown)
            
        else:  # COUNTRY_LARGE
            painter.setBrush(QColor("#f0f0f0"))
            painter.drawRect(-r * 1.5, -r * 1.0, r * 3.0, r * 2.0)
            painter.setPen(QPen(QColor("#888"), 3))
            painter.drawLine(0, -r * 1.0, 0, r * 1.0)
            painter.drawLine(-r * 0.3, -r * 0.5, r * 0.3, -r * 0.5)
            painter.setPen(QPen(QColor("#1a1a1a"), 2))
            painter.setBrush(QColor("#a4b9d6"))
            painter.drawEllipse(-r * 0.6, -r * 0.6, r * 1.2, r * 1.2)

    def _paint_mine(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#2e1d12"), 2))
        
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
        path = QPainterPath()
        path.moveTo(-r, r * 0.5)
        path.quadTo(0, -r * 0.5, r, r * 0.5)
        path.lineTo(r, r)
        path.lineTo(-r, r)
        path.closeSubpath()
        painter.drawPath(path)
        
        painter.setBrush(ore_color)
        for i in range(3):
            painter.drawEllipse(-r * 0.5 + i * r * 0.5, r * 0.2, r * 0.3, r * 0.3)