from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtCore import Qt


class MapRenderer:
    """底图渲染工具：单色/高度图等。"""

    def __init__(self) -> None:
        pass

    @staticmethod
    def _clamp01(x: float) -> float:
        return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

    @staticmethod
    def height_to_mono_color(val: float, base: QColor, contrast: float = 0.75) -> QColor:
        """
        单色底图：把噪声值映射到“明暗”，再用 base 做轻微染色。
        contrast 越大，明暗对比越强（0~1）。
        """
        # val: -1~1 -> 0~1
        t = (val + 1.0) * 0.5
        # 简单对比度曲线（靠近 0.5 拉开）
        c = MapRenderer._clamp01(contrast)
        t = 0.5 + (t - 0.5) * (0.6 + 1.4 * c)
        t = MapRenderer._clamp01(t)

        # 明暗：在 30~245 之间，避免太“脏”或太“死白”
        lum = int(30 + t * 215)
        # 轻微染色：把 base 的 RGB 与 lum 混合
        mix = 0.25  # 越大越偏向 base
        r = int((1 - mix) * lum + mix * base.red())
        g = int((1 - mix) * lum + mix * base.green())
        b = int((1 - mix) * lum + mix * base.blue())
        return QColor(r, g, b)

    def height_map_to_pixmap_mono(
        self,
        height_map,
        base_color: QColor,
        contrast: float = 0.75,
        target_size=(2000, 2000),
    ) -> QPixmap:
        """把高度图转成“单色底图”的 Pixmap，并按需求缩放。"""
        height, width = height_map.shape
        img = QImage(width, height, QImage.Format_RGB32)
        for y in range(height):
            for x in range(width):
                img.setPixelColor(
                    x, y, self.height_to_mono_color(height_map[y][x], base=base_color, contrast=contrast)
                )

        pix = QPixmap.fromImage(img)
        if target_size:
            return pix.scaled(*target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pix

    def solid_background(self, width: int, height: int, color: QColor, target_size=(2000, 2000)) -> QPixmap:
        """纯色底图（满足“不要烟熏效果”）。"""
        img = QImage(width, height, QImage.Format_RGB32)
        img.fill(color)
        pix = QPixmap.fromImage(img)
        if target_size:
            return pix.scaled(*target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pix

    # 兼容旧调用（如果还有地方调用 height_map_to_pixmap）
    def height_map_to_pixmap(self, height_map, target_size=(2000, 2000)) -> QPixmap:
        return self.height_map_to_pixmap_mono(
            height_map,
            base_color=QColor("#d9d9d9"),
            contrast=0.75,
            target_size=target_size,
        )
