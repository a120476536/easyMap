import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QFormLayout,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from canvas_items import ElementItem
from editor_state import EditorState
from elements import ElementType
from map_logic import MapLogic
from map_renderer import MapRenderer


class EzMapWindow(QMainWindow):
    """主窗口：单色底图 + 元素编辑（树/属性/增删）。"""

    def __init__(self) -> None:
        super().__init__()
        self.logic = MapLogic()
        self.renderer = MapRenderer()
        self.state = EditorState()

        self._element_items: dict[str, ElementItem] = {}
        self._tree_item_by_id: dict[str, QTreeWidgetItem] = {}

        self.base_color = QColor("#d9d9d9")
        self.contrast = 0.75

        self.setWindowTitle("简易易制地图 - 架空类别地图编辑器（雏形）")
        self.resize(1200, 760)
        self._setup_ui()
        self.generate_and_draw()

    def _setup_ui(self) -> None:
        root = QHBoxLayout()

        # 左：元素树 + 基础工具
        left = QGroupBox("元素")
        left_layout = QVBoxLayout()

        self.btn_add_village = QPushButton("添加：村庄(点)")
        self.btn_add_village.clicked.connect(lambda: self.add_point_element(ElementType.VILLAGE))
        self.btn_add_city = QPushButton("添加：城市(点)")
        self.btn_add_city.clicked.connect(lambda: self.add_point_element(ElementType.CITY))
        self.btn_add_country = QPushButton("添加：国家(点)")
        self.btn_add_country.clicked.connect(lambda: self.add_point_element(ElementType.COUNTRY))
        self.btn_add_river = QPushButton("添加：河流(线)")
        self.btn_add_river.clicked.connect(lambda: self.add_line_element(ElementType.RIVER))
        self.btn_add_mountain = QPushButton("添加：山川(线)")
        self.btn_add_mountain.clicked.connect(lambda: self.add_line_element(ElementType.MOUNTAIN))
        self.btn_delete = QPushButton("删除选中(含设定)")
        self.btn_delete.clicked.connect(self.delete_selected)

        left_layout.addWidget(self.btn_add_village)
        left_layout.addWidget(self.btn_add_city)
        left_layout.addWidget(self.btn_add_country)
        left_layout.addWidget(self.btn_add_river)
        left_layout.addWidget(self.btn_add_mountain)
        left_layout.addWidget(self.btn_delete)

        left_layout.addWidget(QLabel("层级（示例）：国家 → 城市 → 村庄"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "类型"])
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        left_layout.addWidget(self.tree, 1)

        left.setLayout(left_layout)
        left.setFixedWidth(320)

        # 中：画布
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("#101010"))
        self.view.setDragMode(QGraphicsView.RubberBandDrag)

        # 右：底图色值 + 属性面板
        right = QGroupBox("属性/底图")
        right_layout = QVBoxLayout()

        bg_box = QGroupBox("底图（单色可调）")
        bg_layout = QVBoxLayout()
        self.btn_pick_color = QPushButton("选择底色")
        self.btn_pick_color.clicked.connect(self.pick_base_color)
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(0, 100)
        self.slider_contrast.setValue(int(self.contrast * 100))
        self.slider_contrast.valueChanged.connect(self.on_contrast_changed)
        self.btn_regen = QPushButton("重新生成底图")
        self.btn_regen.clicked.connect(self.generate_and_draw)
        bg_layout.addWidget(self.btn_pick_color)
        bg_layout.addWidget(QLabel("对比度"))
        bg_layout.addWidget(self.slider_contrast)
        bg_layout.addWidget(self.btn_regen)
        bg_box.setLayout(bg_layout)
        right_layout.addWidget(bg_box)

        zoom_box = QGroupBox("视图缩放")
        zoom_layout = QHBoxLayout()
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(25, 300)  # 百分比
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_label = QLabel("100%")
        zoom_layout.addWidget(self.zoom_slider, 1)
        zoom_layout.addWidget(self.zoom_label)
        zoom_box.setLayout(zoom_layout)
        right_layout.addWidget(zoom_box)

        prop_box = QGroupBox("元素设定（点击元素/树查看）")
        prop_layout = QVBoxLayout()
        form = QFormLayout()
        self.edit_name = QLineEdit()
        self.edit_name.editingFinished.connect(self.on_name_edited)
        form.addRow("名称", self.edit_name)
        prop_layout.addLayout(form)

        self.settings_table = QTableWidget(0, 2)
        self.settings_table.setHorizontalHeaderLabels(["字段", "值"])
        self.settings_table.horizontalHeader().setStretchLastSection(True)
        self.settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.settings_table.itemChanged.connect(self.on_setting_item_changed)
        prop_layout.addWidget(self.settings_table, 1)

        prop_box.setLayout(prop_layout)
        right_layout.addWidget(prop_box, 1)

        right.setLayout(right_layout)
        right.setFixedWidth(360)

        root.addWidget(left)
        root.addWidget(self.view, 1)
        root.addWidget(right)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def generate_and_draw(self) -> None:
        # 纯色底图（满足“不要烟熏”的诉求）
        pix = self.renderer.solid_background(
            self.logic.width, self.logic.height, color=self.base_color, target_size=(2000, 2000)
        )

        self.scene.clear()
        self._element_items.clear()
        self.scene.addPixmap(pix)

        # 恢复元素图形项
        for e in self.state.elements.values():
            self._add_item_for_element(e)

        self._rebuild_tree()
        self._refresh_property_panel()

    def pick_base_color(self) -> None:
        c = QColorDialog.getColor(self.base_color, self, "选择底图底色")
        if c.isValid():
            self.base_color = c
            self.generate_and_draw()

    def on_contrast_changed(self, value: int) -> None:
        self.contrast = max(0.0, min(1.0, value / 100.0))
        self.generate_and_draw()

    def _scene_center_pos(self) -> tuple[float, float]:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        return (center.x(), center.y())

    def add_point_element(self, t: ElementType) -> None:
        x, y = self._scene_center_pos()
        parent_id = None
        sel = self.state.get(self.state.selected_id)
        if sel and sel.type in {ElementType.COUNTRY, ElementType.CITY, ElementType.TOWN}:
            parent_id = sel.id
        e = self.state.create_element(t=t, parent_id=parent_id, x=x, y=y)
        self._add_item_for_element(e)
        self._rebuild_tree()
        self.select_element(e.id)

    def delete_selected(self) -> None:
        eid = self.state.selected_id
        if not eid:
            return
        self.state.delete_element_recursive(eid)
        self.generate_and_draw()

    def add_line_element(self, t: ElementType) -> None:
        x, y = self._scene_center_pos()
        parent_id = None
        sel = self.state.get(self.state.selected_id)
        if sel and sel.type == ElementType.COUNTRY:
            parent_id = sel.id
        # 默认一条小折线，便于拖动整体
        poly = [(-60, -10), (-20, 10), (30, -5), (70, 15)]
        e = self.state.create_element(t=t, parent_id=parent_id, x=x, y=y)
        e.polyline = poly
        self._add_item_for_element(e)
        self._rebuild_tree()
        self.select_element(e.id)

    def _add_item_for_element(self, e) -> None:
        if e.id in self._element_items:
            return
        item = ElementItem(e)
        item.clicked.connect(self.select_element)
        if e.type in {ElementType.RIVER, ElementType.MOUNTAIN}:
            item.set_polyline_from_element(e)
        self.scene.addItem(item)
        self._element_items[e.id] = item

    def select_element(self, element_id: str) -> None:
        self.state.set_selected(element_id)
        for eid, item in self._element_items.items():
            item.setSelected(eid == element_id)
            item.setZValue(10 if eid == element_id else 1)
        self._select_tree_item(element_id)
        self._refresh_property_panel()

    def _select_tree_item(self, element_id: str) -> None:
        it = self._tree_item_by_id.get(element_id)
        if not it:
            return
        self.tree.blockSignals(True)
        self.tree.setCurrentItem(it)
        self.tree.blockSignals(False)

    def on_tree_selection_changed(self) -> None:
        item = self.tree.currentItem()
        if not item:
            return
        eid = item.data(0, Qt.UserRole)
        if eid:
            self.select_element(eid)

    def _rebuild_tree(self) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        self._tree_item_by_id.clear()

        def add_node(eid: str, parent_item: QTreeWidgetItem | None) -> None:
            e = self.state.elements[eid]
            it = QTreeWidgetItem([e.name, e.type.value])
            it.setData(0, Qt.UserRole, e.id)
            self._tree_item_by_id[e.id] = it
            if parent_item is None:
                self.tree.addTopLevelItem(it)
            else:
                parent_item.addChild(it)
            for child in sorted(self.state.children_of(e.id), key=lambda x: x.name):
                add_node(child.id, it)

        roots = [e for e in self.state.elements.values() if e.parent_id is None]
        for e in sorted(roots, key=lambda x: x.name):
            add_node(e.id, None)

        self.tree.expandAll()
        self.tree.blockSignals(False)

    def _refresh_property_panel(self) -> None:
        e = self.state.get(self.state.selected_id)
        self.settings_table.blockSignals(True)
        if not e:
            self.edit_name.setText("")
            self.settings_table.setRowCount(0)
            self.settings_table.blockSignals(False)
            return

        self.edit_name.setText(e.name)
        keys = list(e.settings.keys())
        self.settings_table.setRowCount(len(keys))
        for row, k in enumerate(keys):
            key_item = QTableWidgetItem(str(k))
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            val_item = QTableWidgetItem(str(e.settings.get(k, "")))
            self.settings_table.setItem(row, 0, key_item)
            self.settings_table.setItem(row, 1, val_item)
        self.settings_table.blockSignals(False)

    def on_name_edited(self) -> None:
        e = self.state.get(self.state.selected_id)
        if not e:
            return
        name = self.edit_name.text().strip()
        if not name:
            return
        self.state.update_name(e.id, name)
        self._rebuild_tree()

    def on_setting_item_changed(self, item: QTableWidgetItem) -> None:
        e = self.state.get(self.state.selected_id)
        if not e:
            return
        if item.column() != 1:
            return
        key_item = self.settings_table.item(item.row(), 0)
        if not key_item:
            return
        self.state.update_setting(e.id, key_item.text(), item.text())

    def on_zoom_changed(self, value: int) -> None:
        # 重置再按比例缩放，避免积累
        self.view.resetTransform()
        scale = value / 100.0
        self.view.scale(scale, scale)
        self.zoom_label.setText(f"{value}%")
