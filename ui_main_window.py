import random
import os
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QSize,QRect
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QPen
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
    QMenu,
    QPushButton,
    QSpinBox,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QScrollArea
)

from canvas_items import ElementItem
from editor_state import EditorState
from elements import ElementType, MapElement
from map_logic import MapLogic
from map_renderer import MapRenderer


class IconButton(QPushButton):
    """自定义图标按钮，支持图标和文本"""
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setIcon(icon)
        self.setIconSize(QSize(32, 32))
        
        # 设置按钮文本
        self.setText(text)
        
        # 设置按钮样式，让图标在上，文字在下
        self.setStyleSheet("""
            QPushButton {
                text-align: center;
                padding: 10px 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f8f8;
                font-size: 11px;
                spacing: 4px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
                border-color: #aaa;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
        """)
        self.setFixedHeight(80)
        self.setFixedWidth(80)
        
        # 设置按钮布局（图标在上，文字在下）
        self.setLayoutDirection(Qt.LeftToRight)
        
    def sizeHint(self):
        # 返回自定义的大小提示
        return QSize(80, 80)


class CollapsibleGroup(QWidget):
    """可折叠/展开的分组容器"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.setup_ui(title)
        
    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题按钮 - 初始显示▶
        self.title_btn = QPushButton(f"▶ {title}")
        self.title_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #e8e8e8;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d8d8d8;
            }
        """)
        self.title_btn.setCheckable(True)
        self.title_btn.setChecked(False)
        self.title_btn.clicked.connect(self.toggle_expand)
        layout.addWidget(self.title_btn)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)
        layout.addWidget(self.content_widget)
        
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        # 更新箭头图标
        if self.is_expanded:
            self.title_btn.setText("▼ " + self.title_btn.text().replace("▶ ", ""))
        else:
            self.title_btn.setText("▶ " + self.title_btn.text().replace("▼ ", ""))
    
    def add_widget(self, widget, row, col):
        self.content_layout.addWidget(widget, row, col)
    
    def clear_layout(self):
        # 清空布局中的所有widget
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class EzMapWindow(QMainWindow):
    """主窗口：单色底图 + 元素编辑（树/属性/增删）。"""

    def __init__(self) -> None:
        super().__init__()
        self.logic = MapLogic()
        self.renderer = MapRenderer()
        self.state = EditorState()

        self._element_items: dict[str, ElementItem] = {}
        self._tree_item_by_id: dict[str, QTreeWidgetItem] = {}
        
        # 记录当前选择的元素类型（用于单击放置）
        self._selected_element_type: ElementType = None
        # 记录是否处于放置模式
        self._is_placing = False

        self.base_color = QColor("#d9d9d9")
        self.contrast = 0.75

        # 获取项目根目录和图片目录
        # self.project_root = Path(__file__).parent
        self.project_root = Path.cwd()
        self.img_dir = self.project_root / "imgs"
        # 确保图片目录存在
        self.img_dir.mkdir(exist_ok=True)
        
        # 为每个元素创建独立的图片目录
        self.custom_img_dir = self.img_dir / "custom"
        self.custom_img_dir.mkdir(exist_ok=True)
        
        self.setWindowTitle("简易易制地图 - 架空类别地图编辑器（雏形）")
        self.resize(1200, 760)
        self._setup_ui()
        self.generate_and_draw()

    def _setup_ui(self) -> None:
        root = QHBoxLayout()

        # 左：元素树 + 基础工具
        left = QGroupBox("元素")
        left_layout = QVBoxLayout()

        # 创建滚动区域来容纳所有添加按钮
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(5)

        # 房屋分类
        self.house_group = CollapsibleGroup("房屋")
        self._setup_house_buttons()
        scroll_layout.addWidget(self.house_group)

        # 村庄分类
        self.village_group = CollapsibleGroup("村庄")
        self._setup_village_buttons()
        scroll_layout.addWidget(self.village_group)

        # 城市分类
        self.city_group = CollapsibleGroup("城市")
        self._setup_city_buttons()
        scroll_layout.addWidget(self.city_group)

        # 国家分类
        self.country_group = CollapsibleGroup("国家")
        self._setup_country_buttons()
        scroll_layout.addWidget(self.country_group)

        # 河流分类
        self.river_group = CollapsibleGroup("河流")
        self._setup_river_buttons()
        scroll_layout.addWidget(self.river_group)

        # 山川分类
        self.mountain_group = CollapsibleGroup("山川")
        self._setup_mountain_buttons()
        scroll_layout.addWidget(self.mountain_group)

        # 矿场分类
        self.mine_group = CollapsibleGroup("矿场")
        self._setup_mine_buttons()
        scroll_layout.addWidget(self.mine_group)

        # 自定义元素分类
        self.custom_group = CollapsibleGroup("自定义")
        self._setup_custom_buttons()
        scroll_layout.addWidget(self.custom_group)

        # 添加弹性空间
        scroll_layout.addStretch(1)

        scroll_area.setWidget(scroll_content)
        left_layout.addWidget(scroll_area)

        # 删除和取消放置按钮
        button_layout = QHBoxLayout()
        
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        
        # self.btn_cancel_placement = QPushButton("取消放置")
        # self.btn_cancel_placement.clicked.connect(self._cancel_placement)
        # self.btn_cancel_placement.setEnabled(False)
        # self.btn_cancel_placement.setStyleSheet("""
        #     QPushButton {
        #         padding: 8px;
        #         background-color: #6c757d;
        #         color: white;
        #         border: none;
        #         border-radius: 4px;
        #     }
        #     QPushButton:hover {
        #         background-color: #5a6268;
        #     }
        # """)
        
        button_layout.addWidget(self.btn_delete)
        # button_layout.addWidget(self.btn_cancel_placement)
        left_layout.addLayout(button_layout)
        
        # 状态标签
        self.lbl_placement_status = QLabel("就绪")
        self.lbl_placement_status.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.lbl_placement_status)

        left_layout.addWidget(QLabel("层级（示例）：国家 → 城市 → 村庄"))
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["名称", "类型"])
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        left_layout.addWidget(self.tree, 1)

        left.setLayout(left_layout)
        left.setFixedWidth(320)

        # 中：画布
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setBackgroundBrush(QColor("#101010"))
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        # 连接鼠标点击事件
        self.view.mousePressEvent = self._on_view_mouse_press

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
        
        # 添加图片导入按钮
        self.btn_import_image = QPushButton("导入图片...")
        self.btn_import_image.clicked.connect(self.import_image)
        self.btn_import_image.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        prop_layout.addWidget(self.btn_import_image)

        self.settings_table = QTableWidget(0, 2)
        self.settings_table.setHorizontalHeaderLabels(["字段", "值"])
        self.settings_table.horizontalHeader().setStretchLastSection(True)
        self.settings_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.settings_table.itemChanged.connect(self.on_setting_item_changed)
        self.settings_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
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

    def _setup_house_buttons(self):
        """设置房屋分类按钮"""
        # 加载本地图片作为图标
        house_small_icon = self._load_image_icon("house_small.png")
        house_large_icon = self._load_image_icon("house_large.png")
        house_fancy_icon = self._load_image_icon("house_fancy.png")
        
        self.btn_house_small = IconButton(house_small_icon, "小屋")
        self.btn_house_small.clicked.connect(lambda: self._prepare_place_element(ElementType.HOUSE_SMALL))
        
        self.btn_house_large = IconButton(house_large_icon, "大屋")
        self.btn_house_large.clicked.connect(lambda: self._prepare_place_element(ElementType.HOUSE_LARGE))
        
        self.btn_house_fancy = IconButton(house_fancy_icon, "豪宅")
        self.btn_house_fancy.clicked.connect(lambda: self._prepare_place_element(ElementType.HOUSE_FANCY))
        
        # 水平排列，一行三个
        self.house_group.add_widget(self.btn_house_small, 0, 0)
        self.house_group.add_widget(self.btn_house_large, 0, 1)
        self.house_group.add_widget(self.btn_house_fancy, 0, 2)

    def _setup_village_buttons(self):
        """设置村庄分类按钮"""
        village_small_icon = self._load_image_icon("village_small.png")
        village_medium_icon = self._load_image_icon("village_medium.png")
        village_large_icon = self._load_image_icon("village_large.png")
        
        self.btn_village_small = IconButton(village_small_icon, "小村庄")
        self.btn_village_small.clicked.connect(lambda: self._prepare_place_element(ElementType.VILLAGE_SMALL))
        
        self.btn_village_medium = IconButton(village_medium_icon, "中村庄")
        self.btn_village_medium.clicked.connect(lambda: self._prepare_place_element(ElementType.VILLAGE_MEDIUM))
        
        self.btn_village_large = IconButton(village_large_icon, "大村庄")
        self.btn_village_large.clicked.connect(lambda: self._prepare_place_element(ElementType.VILLAGE_LARGE))
        
        # 水平排列，一行三个
        self.village_group.add_widget(self.btn_village_small, 0, 0)
        self.village_group.add_widget(self.btn_village_medium, 0, 1)
        self.village_group.add_widget(self.btn_village_large, 0, 2)

    def _setup_city_buttons(self):
        """设置城市分类按钮"""
        city_small_icon = self._load_image_icon("city_small.png")
        city_medium_icon = self._load_image_icon("city_medium.png")
        city_large_icon = self._load_image_icon("city_large.png")
        
        self.btn_city_small = IconButton(city_small_icon, "小城")
        self.btn_city_small.clicked.connect(lambda: self._prepare_place_element(ElementType.CITY_SMALL))
        
        self.btn_city_medium = IconButton(city_medium_icon, "中城")
        self.btn_city_medium.clicked.connect(lambda: self._prepare_place_element(ElementType.CITY_MEDIUM))
        
        self.btn_city_large = IconButton(city_large_icon, "大城")
        self.btn_city_large.clicked.connect(lambda: self._prepare_place_element(ElementType.CITY_LARGE))
        
        # 水平排列，一行三个
        self.city_group.add_widget(self.btn_city_small, 0, 0)
        self.city_group.add_widget(self.btn_city_medium, 0, 1)
        self.city_group.add_widget(self.btn_city_large, 0, 2)

    def _setup_country_buttons(self):
        """设置国家分类按钮"""
        country_small_icon = self._load_image_icon("country_small.png")
        country_medium_icon = self._load_image_icon("country_medium.png")
        country_large_icon = self._load_image_icon("country_large.png")
        
        self.btn_country_small = IconButton(country_small_icon, "小国")
        self.btn_country_small.clicked.connect(lambda: self._prepare_place_element(ElementType.COUNTRY_SMALL))
        
        self.btn_country_medium = IconButton(country_medium_icon, "中国")
        self.btn_country_medium.clicked.connect(lambda: self._prepare_place_element(ElementType.COUNTRY_MEDIUM))
        
        self.btn_country_large = IconButton(country_large_icon, "大国")
        self.btn_country_large.clicked.connect(lambda: self._prepare_place_element(ElementType.COUNTRY_LARGE))
        
        # 水平排列，一行三个
        self.country_group.add_widget(self.btn_country_small, 0, 0)
        self.country_group.add_widget(self.btn_country_medium, 0, 1)
        self.country_group.add_widget(self.btn_country_large, 0, 2)

    def _setup_river_buttons(self):
        """设置河流分类按钮"""
        river_small_icon = self._load_image_icon("river_small.png")
        river_medium_icon = self._load_image_icon("river_medium.png")
        river_large_icon = self._load_image_icon("river_large.png")
        
        self.btn_river_small = IconButton(river_small_icon, "小溪")
        self.btn_river_small.clicked.connect(lambda: self._prepare_place_element(ElementType.RIVER_SMALL))
        
        self.btn_river_medium = IconButton(river_medium_icon, "中河")
        self.btn_river_medium.clicked.connect(lambda: self._prepare_place_element(ElementType.RIVER_MEDIUM))
        
        self.btn_river_large = IconButton(river_large_icon, "大河")
        self.btn_river_large.clicked.connect(lambda: self._prepare_place_element(ElementType.RIVER_LARGE))
        
        # 水平排列，一行三个
        self.river_group.add_widget(self.btn_river_small, 0, 0)
        self.river_group.add_widget(self.btn_river_medium, 0, 1)
        self.river_group.add_widget(self.btn_river_large, 0, 2)

    def _setup_mountain_buttons(self):
        """设置山川分类按钮"""
        mountain_small_icon = self._load_image_icon("mountain_small.png")
        mountain_medium_icon = self._load_image_icon("mountain_medium.png")
        mountain_large_icon = self._load_image_icon("mountain_large.png")
        
        self.btn_mountain_small = IconButton(mountain_small_icon, "小山")
        self.btn_mountain_small.clicked.connect(lambda: self._prepare_place_element(ElementType.MOUNTAIN_SMALL))
        
        self.btn_mountain_medium = IconButton(mountain_medium_icon, "中山")
        self.btn_mountain_medium.clicked.connect(lambda: self._prepare_place_element(ElementType.MOUNTAIN_MEDIUM))
        
        self.btn_mountain_large = IconButton(mountain_large_icon, "大山")
        self.btn_mountain_large.clicked.connect(lambda: self._prepare_place_element(ElementType.MOUNTAIN_LARGE))
        
        # 水平排列，一行三个
        self.mountain_group.add_widget(self.btn_mountain_small, 0, 0)
        self.mountain_group.add_widget(self.btn_mountain_medium, 0, 1)
        self.mountain_group.add_widget(self.btn_mountain_large, 0, 2)

    def _setup_mine_buttons(self):
        """设置矿场分类按钮"""
        mine_coal_icon = self._load_image_icon("mine_coal.png")
        mine_iron_icon = self._load_image_icon("mine_iron.png")
        mine_gold_icon = self._load_image_icon("mine_gold.png")
        mine_gem_icon = self._load_image_icon("mine_gem.png")
        
        self.btn_mine_coal = IconButton(mine_coal_icon, "煤矿")
        self.btn_mine_coal.clicked.connect(lambda: self._prepare_place_element(ElementType.MINE_COAL))
        
        self.btn_mine_iron = IconButton(mine_iron_icon, "铁矿")
        self.btn_mine_iron.clicked.connect(lambda: self._prepare_place_element(ElementType.MINE_IRON))
        
        self.btn_mine_gold = IconButton(mine_gold_icon, "金矿")
        self.btn_mine_gold.clicked.connect(lambda: self._prepare_place_element(ElementType.MINE_GOLD))
        
        self.btn_mine_gem = IconButton(mine_gem_icon, "宝石矿")
        self.btn_mine_gem.clicked.connect(lambda: self._prepare_place_element(ElementType.MINE_GEM))
        
        # 水平排列，一行四个
        self.mine_group.add_widget(self.btn_mine_coal, 0, 0)
        self.mine_group.add_widget(self.btn_mine_iron, 0, 1)
        self.mine_group.add_widget(self.btn_mine_gold, 0, 2)
        self.mine_group.add_widget(self.btn_mine_gem, 0, 3)

    def _setup_custom_buttons(self):
        """设置自定义分类按钮"""
        self.btn_custom = QPushButton("添加自定义元素")
        self.btn_custom.clicked.connect(self.add_custom_element)
        self.btn_custom.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.custom_group.add_widget(self.btn_custom, 0, 0)

    def _load_image_icon(self, image_name):
        """加载本地图片作为图标"""
        img_path = self.img_dir / image_name
        if img_path.exists():
            return QIcon(str(img_path))
        else:
            # 如果图片不存在，返回默认图标
            print(f"提示：系统图片不存在: {img_path}，将使用默认图标")
            return self._create_default_icon(image_name)

    def _create_default_icon(self, image_name):
        """创建默认图标（当图片不存在时使用）"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#e0e0e0"))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("#808080"), 1))
        painter.drawRect(2, 2, 28, 28)
        
        # 根据图片名显示简写
        short_name = "默认"
        if "house" in image_name:
            short_name = "房"
        elif "village" in image_name:
            short_name = "村"
        elif "city" in image_name:
            short_name = "城"
        elif "country" in image_name:
            short_name = "国"
        elif "river" in image_name:
            short_name = "河"
        elif "mountain" in image_name:
            short_name = "山"
        elif "mine" in image_name:
            short_name = "矿"
            
        painter.drawText(QRect(0, 0, 32, 32), Qt.AlignCenter, short_name)
        painter.end()
        return QIcon(pixmap)

    def import_image(self):
        """导入图片功能"""
        # 获取当前选中的元素
        e = self.state.get(self.state.selected_id)
        if not e:
            QMessageBox.warning(self, "警告", "请先选择一个元素")
            return
        
        # 打开文件对话框选择图片
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        # 获取文件扩展名
        file_ext = Path(file_path).suffix.lower()
        
        # 为元素创建专门的图片文件名
        img_filename = f"{e.id}{file_ext}"
        dest_path = self.custom_img_dir / img_filename
        
        try:
            # 复制图片到自定义图片目录
            shutil.copy2(file_path, dest_path)
            
            # 保存相对于项目根目录的路径，确保格式正确
            # 路径格式应该是: imgs/custom/{element_id}.{ext}
            relative_path = f"imgs/custom/{img_filename}"
            
            print(f"保存图片路径: {relative_path}")  # 调试信息
            print(f"完整目标路径: {dest_path}")  # 调试信息
            print(f"文件是否存在: {dest_path.exists()}")  # 调试信息
            
            self.state.update_setting(e.id, "图片路径", relative_path)
            
            # 刷新属性面板
            self._refresh_property_panel()
            
            # 重新创建元素项以显示新图片
            self._recreate_element_item(e.id)
            
            QMessageBox.information(self, "成功", f"图片已导入并设置为元素图标")
            
        except Exception as ex:
            QMessageBox.critical(self, "错误", f"导入图片失败: {str(ex)}")

    # 添加新的辅助方法
    def _recreate_element_item(self, element_id: str):
        """重新创建元素项（用于更新图片显示）"""
        if element_id in self._element_items:
            item = self._element_items[element_id]
            self.scene.removeItem(item)
            
            e = self.state.get(element_id)
            if e:
                new_item = ElementItem(e)
                new_item.clicked.connect(self.select_element)
                if "RIVER" in e.type.name or "MOUNTAIN" in e.type.name:
                    new_item.set_polyline_from_element(e)
                self.scene.addItem(new_item)
                self._element_items[element_id] = new_item
                
                # 重新选中该元素
                self.select_element(element_id)


    def add_custom_element(self):
        """添加自定义元素"""
        # 询问自定义元素的名称
        name, ok = QInputDialog.getText(
            self, "自定义元素", "请输入元素名称:"
        )
        
        if ok and name:
            # 在场景中心位置创建自定义元素
            x, y = self._get_scene_center()
            
            e = self.state.create_element(
                t=ElementType.CUSTOM,
                name=name,
                parent_id=None,
                x=x,
                y=y
            )
            
            self._add_item_for_element(e)
            self._rebuild_tree()
            self.select_element(e.id)
            
            QMessageBox.information(
                self,
                "提示",
                f"自定义元素 '{name}' 已添加。\n\n请选中该元素，然后点击'导入图片'按钮为其添加图标。"
            )

    def _get_scene_center(self):
        """获取场景中心位置"""
        center = self.view.mapToScene(self.view.viewport().rect().center())
        return center.x(), center.y()

    def _update_element_display(self, element_id: str):
        """更新地图上元素的显示"""
        if element_id in self._element_items:
            item = self._element_items[element_id]
            if hasattr(item, 'update_display_size'):
                item.update_display_size()
            else:
                # 备用方案：重新创建元素
                self.scene.removeItem(item)
                e = self.state.get(element_id)
                if e:
                    new_item = ElementItem(e)
                    new_item.clicked.connect(self.select_element)
                    if "RIVER" in e.type.name or "MOUNTAIN" in e.type.name:
                        new_item.set_polyline_from_element(e)
                    self.scene.addItem(new_item)
                    self._element_items[element_id] = new_item
                    
                    # 重新选中该元素
                    self.select_element(element_id)


    def _prepare_place_element(self, element_type: ElementType) -> None:
        """准备放置元素：选择类型后等待用户点击画布"""
        self._selected_element_type = element_type
        self._is_placing = True
        self.lbl_placement_status.setText(f"准备放置: {element_type.value} - 请在地图上点击放置位置")
        self.btn_cancel_placement.setEnabled(True)
        # 改变鼠标光标
        self.view.setCursor(Qt.CrossCursor)

    def _cancel_placement(self) -> None:
        """取消放置模式"""
        self._selected_element_type = None
        self._is_placing = False
        self.lbl_placement_status.setText("就绪")
        self.btn_cancel_placement.setEnabled(False)
        # 恢复默认鼠标光标
        self.view.setCursor(Qt.ArrowCursor)

    def _on_view_mouse_press(self, event):
        """处理画布上的鼠标点击事件"""
        if self._is_placing and self._selected_element_type:
            # 如果处于放置模式，添加元素
            scene_pos = self.view.mapToScene(event.pos())
            self._place_element_at(scene_pos.x(), scene_pos.y())
            event.accept()
        else:
            # 否则调用原始事件处理
            QGraphicsView.mousePressEvent(self.view, event)

    def _place_element_at(self, x: float, y: float) -> None:
        """在指定位置放置元素"""
        if not self._is_placing or not self._selected_element_type:
            return
            
        parent_id = None
        sel = self.state.get(self.state.selected_id)
        
        # 确定父元素
        if sel:
            if "COUNTRY" in sel.type.name and "COUNTRY" not in self._selected_element_type.name:
                parent_id = sel.id
            elif "CITY" in sel.type.name and "CITY" not in self._selected_element_type.name:
                parent_id = sel.id
            elif "TOWN" in sel.type.name and "TOWN" not in self._selected_element_type.name:
                parent_id = sel.id
                
        # 创建元素
        if "RIVER" in self._selected_element_type.name or "MOUNTAIN" in self._selected_element_type.name:
            e = self.state.create_element(t=self._selected_element_type, parent_id=parent_id, x=x, y=y)
            # 为线状元素添加默认折线
            poly = [(-60, -10), (-20, 10), (30, -5), (70, 15)]
            e.polyline = [(x + px, y + py) for px, py in poly]
        else:
            e = self.state.create_element(t=self._selected_element_type, parent_id=parent_id, x=x, y=y)
            
        self._add_item_for_element(e)
        self._rebuild_tree()
        self.select_element(e.id)
        
        # 退出放置模式
        self._cancel_placement()

    def generate_and_draw(self) -> None:
        # 纯色底图（满足"不要烟熏"的诉求）
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

    def delete_selected(self) -> None:
        eid = self.state.selected_id
        if not eid:
            return
        self.state.delete_element_recursive(eid)
        self.generate_and_draw()

    def _add_item_for_element(self, e) -> None:
        if e.id in self._element_items:
            return
        item = ElementItem(e)
        item.clicked.connect(self.select_element)
        if "RIVER" in e.type.name or "MOUNTAIN" in e.type.name:
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
        key = key_item.text()
        value = item.text()
        self.state.update_setting(e.id, key, value)
        
        # 如果修改了图片尺寸，立即更新显示
        if key in ["图片宽度", "图片高度"]:
            self._update_element_display(e.id)

    def on_zoom_changed(self, value: int) -> None:
        # 重置再按比例缩放，避免积累
        self.view.resetTransform()
        scale = value / 100.0
        self.view.scale(scale, scale)
        self.zoom_label.setText(f"{value}%")