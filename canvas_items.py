from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QBrush, QPen, QColor, QPainterPath, QPainter
from PySide6.QtWidgets import QGraphicsObject

from elements import MapElement, ElementType


class ElementItem(QGraphicsObject):
    """画布上的元素图形项：承载 element_id 并可被选中/拖拽。"""

    clicked = Signal(str)

    def __init__(self, element: MapElement):
        super().__init__()
        self.element_id = element.id
        self.element_type = element.type
        self._radius = 10.0
        self.setFlags(
            QGraphicsObject.ItemIsSelectable
            | QGraphicsObject.ItemIsMovable
            | QGraphicsObject.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._apply_from_element(element)

    def _apply_from_element(self, element: MapElement) -> None:
        self.setPos(element.pos[0], element.pos[1])

    def boundingRect(self) -> QRectF:
        if self.element_type in {ElementType.RIVER, ElementType.MOUNTAIN} and self._path is not None:
            return self._path.boundingRect().adjusted(-5, -5, 5, 5)
        r = self._radius
        return QRectF(-r - 2, -r - 2, 2 * (r + 2), 2 * (r + 2))

    def paint(self, painter, option, widget=None) -> None:
        # 河流/山川：用线条表示，可整体拖动
        if self.element_type in {ElementType.RIVER, ElementType.MOUNTAIN} and self._path is not None:
            color = QColor("#2b5d80") if self.element_type == ElementType.RIVER else QColor("#5c5247")
            width = 4 if self.element_type == ElementType.RIVER else 3
            pen = QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self._path)
            return

        painter.setRenderHint(QPainter.Antialiasing)

        # 点状元素：画小图标（卡通但不廉价）
        if self.element_type in {ElementType.VILLAGE, ElementType.TOWN, ElementType.CITY, ElementType.HOUSE}:
            self._paint_village_like(painter)
            return
        if self.element_type == ElementType.COUNTRY:
            self._paint_country(painter)
            return
        if self.element_type == ElementType.MINE:
            self._paint_mine(painter)
            return
        if self.element_type == ElementType.MOUNTAIN:
            self._paint_mountain_peak(painter)
            return

        # fallback
        r = self._radius
        painter.setPen(QPen(QColor("#222"), 2))
        painter.setBrush(QBrush(QColor("#f2f2f2")))
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))

    def set_river_polyline(self, element: MapElement) -> None:
        if element.type != ElementType.RIVER:
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
        if element.type not in {ElementType.RIVER, ElementType.MOUNTAIN}:
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
        # 拖动点状元素时，把新坐标交给外层同步（这里先返回，让外层在 scene 里监听）
        return super().itemChange(change, value)

    _path: Optional[QPainterPath] = None

    # --- icon painters ---
    def _paint_village_like(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1e1e1e"), 2))
        painter.setBrush(QColor("#f7f2e8"))
        # house base
        painter.drawRect(-r * 0.9, 0, r * 1.8, r * 1.1)
        # roof
        roof = QPainterPath()
        roof.moveTo(-r, 0)
        roof.lineTo(0, -r * 0.9)
        roof.lineTo(r, 0)
        roof.closeSubpath()
        painter.setBrush(QColor("#c75f3e"))
        painter.drawPath(roof)
        # door
        painter.setBrush(QColor("#d9cbb8"))
        painter.drawRect(-r * 0.2, r * 0.3, r * 0.4, r * 0.8)

    def _paint_country(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#1a1a1a"), 2))
        painter.setBrush(QColor("#d8d8d8"))
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))
        painter.setBrush(QColor("#a4b9d6"))
        painter.drawRect(-r * 0.8, -r * 0.2, r * 1.6, r * 0.9)

    def _paint_mine(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#2e1d12"), 2))
        painter.setBrush(QColor("#e6e1d8"))
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))
        path = QPainterPath()
        path.moveTo(-r * 0.8, r * 0.3)
        path.lineTo(-r * 0.3, -r * 0.6)
        path.lineTo(r * 0.4, r * 0.2)
        path.lineTo(r * 0.8, -r * 0.5)
        painter.setPen(QPen(QColor("#4a3a2f"), 2))
        painter.drawPath(path)

    def _paint_mountain_peak(self, painter: QPainter) -> None:
        r = self._radius
        painter.setPen(QPen(QColor("#3b3b3b"), 2))
        painter.setBrush(QColor("#e8e8e8"))
        path = QPainterPath()
        path.moveTo(-r, r * 0.8)
        path.lineTo(0, -r)
        path.lineTo(r, r * 0.8)
        path.closeSubpath()
        painter.drawPath(path)

