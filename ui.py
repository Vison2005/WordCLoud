#ui.py
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QScrollArea, QLabel, QComboBox, QListWidget,
                             QLineEdit, QGridLayout, QSizePolicy, QSlider)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon


class WordCloudUI:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        main_window = self.main_window
        main_window.setWindowTitle('词云生成器')
        main_window.setGeometry(100, 100, 1800, 800)
        if os.path.exists('WordCloudIcon.png'):
            main_window.setWindowIcon(QIcon('WordCloudIcon.png'))

        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        main_window.setCentralWidget(central_widget)

        # 左侧区域
        self.setup_left_area(main_layout)
        # 中间区域
        self.setup_center_area(main_layout)
        # 右侧区域
        self.setup_right_area(main_layout)

    def setup_left_area(self, main_layout):
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: grey;")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(1)

        top_buttons = QHBoxLayout()
        self.btn_select_image = QPushButton('选择缩略图(底图)')
        self.btn_select_text = QPushButton('选择文本文件')
        self.btn_select_font = QPushButton('选择字体')
        top_buttons.addWidget(self.btn_select_image)
        top_buttons.addWidget(self.btn_select_text)
        top_buttons.addWidget(self.btn_select_font)
        left_layout.addLayout(top_buttons)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.thumbnail_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        left_layout.addWidget(scroll_area)

        main_layout.addWidget(left_widget, 3)

    def setup_center_area(self, main_layout):
        center_widget = QWidget()
        center_widget.setStyleSheet("background-color: white;")
        center_layout = QVBoxLayout(center_widget)

        self.wordcloud_label = QLabel('词云图将显示在这里')
        self.wordcloud_label.setAlignment(Qt.AlignCenter)
        self.wordcloud_label.setStyleSheet("background-color: #4e5181; color: white;")
        self.wordcloud_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        btn_layout = QHBoxLayout()
        self.btn_update = QPushButton('更新词云图')
        self.btn_export = QPushButton('导出到同目录下文件夹')
        self.btn_save_as = QPushButton('另存为')
        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_save_as)

        center_layout.addWidget(self.wordcloud_label)
        center_layout.addLayout(btn_layout)
        main_layout.addWidget(center_widget, 10)

    def setup_right_area(self, main_layout):
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)

        # 字体选择区域
        font_widget = QWidget()
        font_layout = QVBoxLayout(font_widget)
        self.font_combobox = QComboBox()
        self.font_combobox.addItems(['SimHei', 'Arial', 'Times New Roman'])

        # 颜色选择区域
        color_grid = QGridLayout()
        btn_size = QSize(120, 30)

        self.btn_base_color = QPushButton("选择基础字体颜色")
        self.btn_base_color.setFixedSize(btn_size)
        self.lbl_base_color = QLabel()
        self.lbl_base_color.setFixedSize(20, 20)

        self.btn_add_similar = QPushButton("添加相近颜色")
        self.btn_add_similar.setFixedSize(btn_size)
        self.similar_container = QWidget()
        self.similar_layout = QHBoxLayout(self.similar_container)

        self.btn_add_contrast = QPushButton("添加对比颜色")
        self.btn_add_contrast.setFixedSize(btn_size)
        self.contrast_container = QWidget()
        self.contrast_layout = QHBoxLayout(self.contrast_container)

        self.btn_bg_color = QPushButton("选择背景颜色")
        self.btn_bg_color.setFixedSize(btn_size)
        self.lbl_bg_color = QLabel()
        self.lbl_bg_color.setFixedSize(20, 20)

        # 布局颜色选择区域
        color_grid.addWidget(self.btn_base_color, 0, 0)
        color_grid.addWidget(self.lbl_base_color, 0, 1)
        color_grid.addWidget(self.btn_add_similar, 1, 0)
        color_grid.addWidget(self.similar_container, 1, 1)
        color_grid.addWidget(self.btn_add_contrast, 2, 0)
        color_grid.addWidget(self.contrast_container, 2, 1)
        color_grid.addWidget(self.btn_bg_color, 3, 0)
        color_grid.addWidget(self.lbl_bg_color, 3, 1)

        # 分辨率设置区域
        # resolution_widget = QWidget()
        # res_layout = QHBoxLayout(resolution_widget)
        # self.line_width = QLineEdit("2000")
        # self.line_height = QLineEdit("1600")
        # self.btn_apply_res = QPushButton("应用分辨率")
        # res_layout.addWidget(QLabel("分辨率:"))
        # res_layout.addWidget(self.line_width)
        # res_layout.addWidget(QLabel("×"))
        # res_layout.addWidget(self.line_height)
        # res_layout.addWidget(self.btn_apply_res)

        # Scale 设置区域
        scale_widget = QWidget()
        scale_layout = QHBoxLayout(scale_widget)
        scale_layout.addWidget(QLabel("Scale (2^n):"))
        # self.scale_slider = QSlider(Qt.Horizontal)
        # self.scale_slider.setRange(0, 5)  # 2^1=2   2^5=32
        # self.scale_slider.setTickInterval(1)    # 设置刻度间隔为1
        # self.scale_slider.setTickPosition(QSlider.TicksBelow)    # 设置刻度显示在下方
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["1","2", "4", "8", "16", "32"])  # 对应2^n的值
        self.scale_combo.setCurrentIndex(0)  # 默认选第一个 (1)
        scale_layout.addWidget(self.scale_combo)
        self.scale_value_label = QLabel("1")  # 默认显示1
        scale_layout.addWidget(QLabel("Scale (2^n):"))  # 添加标签
        # scale_layout.addWidget(self.scale_slider)    # 添加滑块
        scale_layout.addWidget(self.scale_value_label)  # 添加显示当前值的标签
        # 在 font_layout 中添加滑块 (替代原来的分辨率设置)
        font_layout.addWidget(self.font_combobox)
        font_layout.addLayout(color_grid)
        font_layout.addWidget(scale_widget)  # 添加这一行替代分辨率设置

        # 添加到字体布局
        font_layout.addWidget(self.font_combobox)
        font_layout.addLayout(color_grid)
        font_layout.addWidget(scale_widget)

        # 文本列表区域
        self.text_list = QListWidget()

        # 数据库操作按钮区域
        db_btn_widget = QWidget()
        db_btn_layout = QVBoxLayout(db_btn_widget)

        self.btn_add_text = QPushButton('添加文本到数据库')
        self.btn_add_image = QPushButton('添加图片到数据库')
        # self.btn_add_both = QPushButton('同时添加图片和文本')

        db_btn_layout.addWidget(self.btn_add_text)
        db_btn_layout.addWidget(self.btn_add_image)
        # db_btn_layout.addWidget(self.btn_add_both)

        # 将各部分添加到右侧主布局
        self.right_layout.addWidget(font_widget)
        self.right_layout.addWidget(self.text_list)
        self.right_layout.addWidget(db_btn_widget)

        main_layout.addWidget(right_widget, 2)
