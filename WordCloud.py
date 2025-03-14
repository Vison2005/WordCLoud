import os
import sys
import shutil
import random
from functools import partial

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QFileDialog, QComboBox, QListWidget, QScrollArea,
                             QSizePolicy, QColorDialog, QLineEdit, QGridLayout)
from PyQt5.QtGui import QPixmap, QIcon, QColor, QIntValidator
from PyQt5.QtCore import Qt, QSize

import jieba
import imageio
from wordcloud import WordCloud

class WordCloudApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('词云生成器')
        self.setGeometry(100, 100, 1800, 800)
        if os.path.exists('WordCloudIcon.png'):
            self.setWindowIcon(QIcon('WordCloudIcon.png'))

        # 允许拖拽
        self.setAcceptDrops(True)

        # ========== 关键变量 ==========
        self.image_path = ''       # 当前选中的底图
        self.font_path = ''        # 当前选中的字体
        self.text_file_path = ''   # 当前选中的文本文件

        # 颜色相关
        self.base_text_color = '#000000'   # 基础颜色
        self.similar_text_colors = []      # 相近颜色列表
        self.contrast_text_colors = []     # 对比颜色列表
        self.bg_color = '#ffffff'          # 背景颜色

        # 默认分辨率
        self.image_width = 2000
        self.image_height = 1600

        # ========== 整体布局 ==========
        main_layout = QHBoxLayout()

        # ========== 左侧(灰色)区域：缩略图 + 3 个按钮 ==========
        self.left_widget = QWidget()
        self.left_widget.setStyleSheet("background-color: grey;")
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(1)

        # 顶部三个按钮
        top_buttons_layout = QHBoxLayout()
        self.btn_select_image = QPushButton('选择缩略图(底图)')
        self.btn_select_image.setStyleSheet("background-color: white;")
        self.btn_select_image.clicked.connect(lambda: self.select_file('image'))
        top_buttons_layout.addWidget(self.btn_select_image)

        self.btn_select_text = QPushButton('选择文本文件')
        self.btn_select_text.setStyleSheet("background-color: white;")
        self.btn_select_text.clicked.connect(lambda: self.select_file('text'))
        top_buttons_layout.addWidget(self.btn_select_text)

        self.btn_select_font = QPushButton('选择字体')
        self.btn_select_font.setStyleSheet("background-color: white;")
        self.btn_select_font.clicked.connect(lambda: self.select_file('font'))
        top_buttons_layout.addWidget(self.btn_select_font)
        left_layout.addLayout(top_buttons_layout)

        # 缩略图滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.thumbnail_layout = QVBoxLayout(scroll_content)
        self.thumbnail_layout.setContentsMargins(5, 5, 5, 5)
        self.thumbnail_layout.setSpacing(0)

        if not os.path.exists('./thumbnail'):
            os.mkdir('./thumbnail')
        for fname in os.listdir('./thumbnail'):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                path = os.path.join('./thumbnail', fname)
                btn_thumb = QPushButton()
                btn_thumb.setText(fname)
                btn_thumb.setIcon(QIcon(path))
                btn_thumb.setIconSize(QSize(180, 120))
                btn_thumb.setStyleSheet("background-color: white;")
                btn_thumb.clicked.connect(partial(self.thumbnail_clicked, path))
                self.thumbnail_layout.addWidget(btn_thumb)

        self.scroll_area.setWidget(scroll_content)
        left_layout.addWidget(self.scroll_area)

        # ========== 中间(白色)区域：显示词云 + 3 个按钮 ==========
        self.center_widget = QWidget()
        self.center_widget.setStyleSheet("background-color: white;")
        center_layout = QVBoxLayout(self.center_widget)
        center_layout.setContentsMargins(5, 5, 5, 5)
        center_layout.setSpacing(5)

        self.wordcloud_label = QLabel('词云图将显示在这里')
        self.wordcloud_label.setAlignment(Qt.AlignCenter)
        self.wordcloud_label.setStyleSheet("background-color: #4e5181; color: white;")
        self.wordcloud_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout.addWidget(self.wordcloud_label)

        center_button_layout = QHBoxLayout()
        self.btn_update = QPushButton('更新词云图')
        self.btn_update.setStyleSheet("background-color: grey; color: white;")
        self.btn_update.clicked.connect(self.update_wordcloud)
        center_button_layout.addWidget(self.btn_update)

        self.btn_export = QPushButton('导出到同目录下文件夹')
        self.btn_export.setStyleSheet("background-color: grey; color: white;")
        self.btn_export.clicked.connect(self.export_wordcloud)
        center_button_layout.addWidget(self.btn_export)

        self.btn_save_as = QPushButton('另存为')
        self.btn_save_as.setStyleSheet("background-color: grey; color: white;")
        self.btn_save_as.clicked.connect(self.save_as_wordcloud)
        center_button_layout.addWidget(self.btn_save_as)

        center_layout.addLayout(center_button_layout)

        # ========== 右侧(白色)区域：字体 & 颜色设置 & 分辨率 & 文本列表 ==========
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        # 上方区域：字体下拉及颜色设置
        font_widget = QWidget()
        font_layout = QVBoxLayout(font_widget)
        font_layout.setContentsMargins(5, 5, 5, 5)
        font_layout.setSpacing(5)

        self.font_combobox = QComboBox()
        self.font_combobox.addItems(['SimHei', 'Arial', 'Times New Roman'])
        font_layout.addWidget(self.font_combobox)

        # 统一按钮大小
        btn_size = QSize(120, 30)

        # 使用 QGridLayout 让颜色设置按钮和色块对齐
        color_layout = QGridLayout()
        color_layout.setContentsMargins(0,0,0,0)
        color_layout.setSpacing(5)
        row = 0

        # 基础字体颜色
        self.btn_base_text_color = QPushButton("选择基础字体颜色")
        self.btn_base_text_color.setFixedSize(btn_size)
        self.btn_base_text_color.clicked.connect(self.choose_base_text_color)
        color_layout.addWidget(self.btn_base_text_color, row, 0, alignment=Qt.AlignLeft)
        self.lbl_base_color = QLabel()
        self.lbl_base_color.setFixedSize(20, 20)
        self.lbl_base_color.setStyleSheet("background-color: {};".format(self.base_text_color))
        color_layout.addWidget(self.lbl_base_color, row, 1, alignment=Qt.AlignLeft)
        row += 1

        # 添加相近颜色
        self.btn_add_similar = QPushButton("添加相近颜色")
        self.btn_add_similar.setFixedSize(btn_size)
        self.btn_add_similar.clicked.connect(self.choose_similar_text_color)
        color_layout.addWidget(self.btn_add_similar, row, 0, alignment=Qt.AlignLeft)
        self.similar_color_container = QWidget()
        self.similar_color_container_layout = QHBoxLayout(self.similar_color_container)
        self.similar_color_container_layout.setContentsMargins(0,0,0,0)
        self.similar_color_container_layout.setSpacing(2)
        color_layout.addWidget(self.similar_color_container, row, 1, alignment=Qt.AlignLeft)
        row += 1

        # 添加对比颜色
        self.btn_add_contrast = QPushButton("添加对比颜色")
        self.btn_add_contrast.setFixedSize(btn_size)
        self.btn_add_contrast.clicked.connect(self.choose_contrast_text_color)
        color_layout.addWidget(self.btn_add_contrast, row, 0, alignment=Qt.AlignLeft)
        self.contrast_color_container = QWidget()
        self.contrast_color_container_layout = QHBoxLayout(self.contrast_color_container)
        self.contrast_color_container_layout.setContentsMargins(0,0,0,0)
        self.contrast_color_container_layout.setSpacing(2)
        color_layout.addWidget(self.contrast_color_container, row, 1, alignment=Qt.AlignLeft)
        row += 1

        # 选择背景颜色
        self.btn_bg_color = QPushButton("选择背景颜色")
        self.btn_bg_color.setFixedSize(btn_size)
        self.btn_bg_color.clicked.connect(self.choose_bg_color)
        color_layout.addWidget(self.btn_bg_color, row, 0, alignment=Qt.AlignLeft)
        self.lbl_bg_color = QLabel()
        self.lbl_bg_color.setFixedSize(20, 20)
        self.lbl_bg_color.setStyleSheet("background-color: {};".format(self.bg_color))
        color_layout.addWidget(self.lbl_bg_color, row, 1, alignment=Qt.AlignLeft)
        row += 1

        font_layout.addLayout(color_layout)

        # 分辨率设置区域
        resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(resolution_widget)
        resolution_layout.setContentsMargins(5,5,5,5)
        resolution_layout.setSpacing(5)
        lbl_resolution = QLabel("分辨率:")
        resolution_layout.addWidget(lbl_resolution)
        self.line_edit_width = QLineEdit(str(self.image_width))
        self.line_edit_width.setValidator(QIntValidator(100, 10000, self))
        self.line_edit_width.setFixedWidth(60)
        resolution_layout.addWidget(self.line_edit_width)
        lbl_x = QLabel("×")
        resolution_layout.addWidget(lbl_x)
        self.line_edit_height = QLineEdit(str(self.image_height))
        self.line_edit_height.setValidator(QIntValidator(100, 10000, self))
        self.line_edit_height.setFixedWidth(60)
        resolution_layout.addWidget(self.line_edit_height)
        self.btn_apply_resolution = QPushButton("应用分辨率")
        self.btn_apply_resolution.setFixedSize(btn_size)
        self.btn_apply_resolution.clicked.connect(self.apply_resolution)
        resolution_layout.addWidget(self.btn_apply_resolution)
        font_layout.addWidget(resolution_widget)

        right_layout.addWidget(font_widget)

        # 下方区域：文本文件列表
        text_list_widget = QWidget()
        text_list_layout = QVBoxLayout(text_list_widget)
        text_list_layout.setContentsMargins(5, 5, 5, 5)
        text_list_layout.setSpacing(5)
        self.text_list = QListWidget()
        text_list_layout.addWidget(self.text_list)
        right_layout.addWidget(text_list_widget)
        self.right_widget.setLayout(right_layout)

        main_layout.addWidget(self.left_widget, 3)
        main_layout.addWidget(self.center_widget, 10)
        main_layout.addWidget(self.right_widget, 2)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.load_text_files()

    # ==================== 拖拽支持 ====================
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile().strip()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.image_path = file_path
                if self.text_file_path:
                    self.update_wordcloud()
            elif file_path.lower().endswith('.txt'):
                self.text_file_path = file_path
                if self.image_path:
                    self.update_wordcloud()
            elif file_path.lower().endswith('.ttf'):
                self.font_path = file_path
                if self.text_file_path and self.image_path:
                    self.update_wordcloud()

    # ==================== 左侧缩略图点击 ====================
    def thumbnail_clicked(self, path):
        self.image_path = path
        print(f"选中的底图: {path}")
        if self.text_file_path:
            self.update_wordcloud()

    # ==================== 文本文件列表 ====================
    def load_text_files(self):
        if not os.path.exists('./texts'):
            os.mkdir('./texts')
        for fname in os.listdir('./texts'):
            if fname.lower().endswith('.txt'):
                self.text_list.addItem(fname)
        self.text_list.currentTextChanged.connect(self.on_text_file_selected)

    def on_text_file_selected(self, filename):
        self.text_file_path = os.path.join('./texts', filename)
        print(f"选中的文本文件: {self.text_file_path}")
        if self.image_path:
            self.update_wordcloud()

    # ==================== “选择文件”按钮 ====================
    def select_file(self, file_type):
        file_path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type.capitalize()}文件")
        if file_path:
            if file_type == 'image':
                self.image_path = file_path
                if self.text_file_path:
                    self.update_wordcloud()
            elif file_type == 'font':
                self.font_path = file_path
                if self.text_file_path and self.image_path:
                    self.update_wordcloud()
            elif file_type == 'text':
                self.text_file_path = file_path
                if self.image_path:
                    self.update_wordcloud()

    # ==================== 颜色选择相关 ====================
    def choose_base_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.base_text_color = color.name()
            self.lbl_base_color.setStyleSheet("background-color: {};".format(self.base_text_color))
            if self.text_file_path and self.image_path:
                self.update_wordcloud()

    def choose_similar_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.similar_text_colors.append(color.name())
            lbl = QLabel()
            lbl.setFixedSize(20, 20)
            lbl.setStyleSheet("background-color: {};".format(color.name()))
            self.similar_color_container_layout.addWidget(lbl)
            if self.text_file_path and self.image_path:
                self.update_wordcloud()

    def choose_contrast_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.contrast_text_colors.append(color.name())
            lbl = QLabel()
            lbl.setFixedSize(20, 20)
            lbl.setStyleSheet("background-color: {};".format(color.name()))
            self.contrast_color_container_layout.addWidget(lbl)
            if self.text_file_path and self.image_path:
                self.update_wordcloud()

    def choose_bg_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.bg_color = color.name()
            self.lbl_bg_color.setStyleSheet("background-color: {};".format(self.bg_color))
            if self.text_file_path and self.image_path:
                self.update_wordcloud()

    # ==================== 分辨率应用 ====================
    def apply_resolution(self):
        try:
            width = int(self.line_edit_width.text())
            height = int(self.line_edit_height.text())
            self.image_width = width
            self.image_height = height
            self.update_wordcloud()
        except ValueError:
            pass

    # ==================== 自定义多颜色函数 ====================
    def multi_color_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        colors = []
        if self.base_text_color:
            colors.append(self.base_text_color)
        colors.extend(self.similar_text_colors)
        colors.extend(self.contrast_text_colors)
        if colors:
            return random.choice(colors)
        else:
            return "#000000"

    # ==================== 生成 & 显示词云图 ====================
    def update_wordcloud(self):
        if not self.text_file_path:
            self.wordcloud_label.setText("请先选择文本文件！")
            return
        if not self.image_path:
            self.wordcloud_label.setText("请先选择底图(缩略图)！")
            return
        if not self.font_path:
            selected_font_name = self.font_combobox.currentText()
            if selected_font_name == 'SimHei':
                self.font_path = 'C:/Windows/Fonts/simhei.ttf'
            elif selected_font_name == 'Arial':
                self.font_path = 'C:/Windows/Fonts/arial.ttf'
            else:
                self.font_path = 'C:/Windows/Fonts/times.ttf'
        try:
            self.generate_wordcloud()
            self.display_wordcloud()
        except Exception as e:
            self.wordcloud_label.setText("生成词云图失败: " + str(e))
            print("Error in generate_wordcloud:", e)

    def generate_wordcloud(self):
        # 1) 读取文本
        with open(self.text_file_path, 'r', encoding='utf-8') as f:
            s = f.read()
        # 2) 去除标点及多余空白
        rp_str = ['，', '。', '！', '？', '、', '：', '；', '（', '）', '《', '》',
                  '“', '”', '‘', '’', '【', '】', '—', '…', '·', '～', ' ']
        for i in rp_str:
            s = s.replace(i, '')
        s = s.strip()
        # 3) 分词（不加载大文本作为用户词典）
        words = jieba.lcut(s)
        # 4) 加载停用词（若存在 stopwords.txt）
        stopwords_list = []
        if os.path.exists('stopwords.txt'):
            with open('stopwords.txt', 'r', encoding='utf-8') as f_stop:
                stopwords_list = f_stop.read().splitlines()
        # 5) 统计词频
        words_dict = {}
        for w in words:
            if len(w) <= 1:
                continue
            if w not in stopwords_list:
                words_dict[w] = words_dict.get(w, 0) + 1
        words_list = sorted(words_dict.items(), key=lambda x: x[1], reverse=True)

        # 6) 写入统计文件到 ./counts 目录，文件名为原文件名+Count.txt
        if not os.path.exists('./counts'):
            os.mkdir('./counts')
        text_basename = os.path.splitext(os.path.basename(self.text_file_path))[0]
        count_filename = f"{text_basename}Count.txt"
        count_filepath = os.path.join('./counts', count_filename)
        with open(count_filepath, 'w', encoding='utf-8') as f_out:
            for k, v in words_list:
                f_out.write('{:<8}{:>2}\n'.format(k, v))
        # 7) 生成词云图
        mask_image = imageio.imread(self.image_path)
        w = WordCloud(
            font_path=self.font_path,
            background_color=self.bg_color,
            width=self.image_width,
            height=self.image_height,
            scale=2,
            max_words=1000,
            mask=mask_image,
            color_func=self.multi_color_func
        )
        w.generate_from_frequencies(dict(words_list))
        w.to_file('./wordcloud.png')

    def display_wordcloud(self):
        if os.path.exists('./wordcloud.png'):
            pixmap = QPixmap('./wordcloud.png')
            self.wordcloud_label.setPixmap(pixmap.scaled(
                self.wordcloud_label.width(),
                self.wordcloud_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        else:
            self.wordcloud_label.setText("未找到词云图，请先点击更新词云图。")

    # ==================== 导出 & 另存为 ====================
    def export_wordcloud(self):
        if not os.path.exists('./wordcloud.png'):
            self.wordcloud_label.setText("还没有生成词云图，无法导出。")
            return
        if not os.path.exists('./export'):
            os.mkdir('./export')
        export_path = os.path.join('./export', 'wordcloud_export.png')
        shutil.copy('./wordcloud.png', export_path)
        self.wordcloud_label.setText(f"已导出到: {export_path}")

    def save_as_wordcloud(self):
        if not os.path.exists('./wordcloud.png'):
            self.wordcloud_label.setText("还没有生成词云图，无法另存为。")
            return
        save_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "wordcloud.png",
            "PNG Files (*.png);;All Files (*)"
        )
        if save_path:
            shutil.copy('./wordcloud.png', save_path)
            self.wordcloud_label.setText(f"已另存为: {save_path}")

def main():
    app = QApplication(sys.argv)
    ex = WordCloudApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
