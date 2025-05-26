# main.py
import os
import sys
import shutil
from functools import partial
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QColorDialog,
                             QMessageBox, QPushButton, QLabel, QMenu)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from ui import WordCloudUI
from core import WordCloudCore


class WordCloudApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = WordCloudUI(self)
        self.core = WordCloudCore()
        self.setup_signals()
        self.init_resources()
        self.load_thumbnails()
        self.load_text_files()
        self.setup_context_menus()
        self.ui.scale_combo.currentTextChanged.connect(self.update_scale_value)
    def setup_context_menus(self):
        # 图片列表右键菜单
        self.thumbnail_area = self.ui.thumbnail_layout.parent().parent().parent()
        self.thumbnail_area.setContextMenuPolicy(Qt.CustomContextMenu)
        self.thumbnail_area.customContextMenuRequested.connect(self.show_image_context_menu)

        # 文本列表右键菜单
        self.ui.text_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.text_list.customContextMenuRequested.connect(self.show_text_context_menu)


    def update_scale_value(self, scale_text):
        """更新 scale 值"""
        try:
            scale_value = int(scale_text)  # 获取选择的 scale
            self.core.scale = scale_value
            if self.all_files_selected():
                self.update_wordcloud()
        except ValueError:
            print("无效的 Scale 值")

    def show_image_context_menu(self, pos):
        """显示图片右键菜单"""
        try:
            menu = QMenu()
            delete_action = menu.addAction("删除图片")
            action = menu.exec_(self.thumbnail_area.mapToGlobal(pos))
            if action == delete_action:
                # 找出点击的是哪个缩略图按钮
                widget = self.thumbnail_area.childAt(pos)
                if widget and isinstance(widget, QPushButton):
                    image_name = widget.text()
                    self.delete_image(image_name)
        except Exception as e:
            print(f"显示图片右键菜单时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")

    def show_text_context_menu(self, pos):
        """显示文本右键菜单"""
        menu = QMenu()
        delete_action = menu.addAction("删除文本")
        action = menu.exec_(self.ui.text_list.mapToGlobal(pos))

        if action == delete_action:
            item = self.ui.text_list.itemAt(pos)
            if item:
                text_name = item.text()
                self.delete_text(text_name)


    def delete_image(self, image_name):
        """从数据库和本地删除图片"""
        try:
            if not image_name:
                QMessageBox.warning(self, "警告", "无法确定要删除的图片")
                return
            # 从数据库删除
            success, msg = self.core.delete_from_database(image_name=image_name)
            if not success:
                QMessageBox.warning(self, "删除失败", msg)
                return
            # 从本地删除缩略图
            thumbnail_path = os.path.join('./thumbnail', image_name)
            if os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                except Exception as e:
                    print(f"删除本地文件失败: {str(e)}")
            # 从UI移除按钮
            layout = self.ui.thumbnail_layout
            found_widget = None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() and item.widget().text() == image_name:
                    found_widget = item.widget()
                    break
            if found_widget:
                layout.removeWidget(found_widget)
                found_widget.deleteLater()
                QMessageBox.information(self, "成功", f"图片'{image_name}'已删除")
            else:
                QMessageBox.warning(self, "警告", f"未找到图片'{image_name}'对应的UI元素")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除图片时出现错误: {str(e)}")
            print(f"删除图片时出错: {str(e)}")

    def delete_text(self, text_name):
        """从数据库和本地删除文本"""
        # 从数据库删除
        success, msg = self.core.delete_from_database(text_name=text_name)
        if success:
            # 从本地删除文本文件
            text_path = os.path.join('./texts', text_name)
            if os.path.exists(text_path):
                os.remove(text_path)

            # 从UI移除项
            for i in range(self.ui.text_list.count()):
                if self.ui.text_list.item(i).text() == text_name:
                    self.ui.text_list.takeItem(i)
                    break

            QMessageBox.information(self, "成功", "文本已删除")
        else:
            QMessageBox.warning(self, "失败", msg)


    def setup_signals(self):
        # 文件选择信号
        self.ui.btn_select_image.clicked.connect(lambda: self.select_file('image'))
        self.ui.btn_select_text.clicked.connect(lambda: self.select_file('text'))
        self.ui.btn_select_font.clicked.connect(lambda: self.select_file('font'))

        # 操作信号
        self.ui.btn_update.clicked.connect(self.update_wordcloud)
        self.ui.btn_export.clicked.connect(self.export_wordcloud)
        self.ui.btn_save_as.clicked.connect(self.save_as_wordcloud)

        # 颜色选择信号
        self.ui.btn_base_color.clicked.connect(self.choose_base_color)
        self.ui.btn_add_similar.clicked.connect(self.choose_similar_color)
        self.ui.btn_add_contrast.clicked.connect(self.choose_contrast_color)
        self.ui.btn_bg_color.clicked.connect(self.choose_bg_color)

        self.ui.scale_combo.currentTextChanged.connect(self.update_scale_value)
        self.ui.text_list.currentTextChanged.connect(self.on_text_selected)

        # 数据库操作信号
        self.ui.btn_add_text.clicked.connect(self.add_text_to_db)
        self.ui.btn_add_image.clicked.connect(self.add_image_to_db)


    def init_resources(self):
        self.image_path = ''
        self.font_path = ''
        self.text_file_path = ''
        self.ui.lbl_base_color.setStyleSheet(f"background-color: {self.core.base_color};")
        self.ui.lbl_bg_color.setStyleSheet(f"background-color: {self.core.bg_color};")
        # self.ui.line_width.setText(str(self.core.width))
        # self.ui.line_height.setText(str(self.core.height))

    # 文件操作方法
    def select_file(self, file_type):
        """选择文件"""
        path, _ = QFileDialog.getOpenFileName(self, f"选择{file_type}文件")
        if path:
            path = os.path.normpath(path)
            print(f"选择的 {file_type} 文件路径: {path}")

            if file_type == 'image':
                self.image_path = path
                self.core.image_path = path
                self.save_thumbnail(path)
            elif file_type == 'text':
                self.text_file_path = path
                self.core.text_file_path = path
                self.add_text_file(os.path.basename(path))
            elif file_type == 'font':
                self.core.font_path = path

            if self.all_files_selected():
                self.update_wordcloud()

    def all_files_selected(self):
        """检查是否已选择所有必需文件"""
        return all([self.image_path, self.text_file_path])


    def save_thumbnail(self, path):
        """保存缩略图"""
        try:
            thumbnail_dir = './thumbnail'
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)

            fname = os.path.basename(path)
            dest_path = os.path.join(thumbnail_dir, fname)

            if os.path.abspath(path) != os.path.abspath(dest_path):  # 避免相同文件
                if os.path.exists(dest_path):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    base, ext = os.path.splitext(fname)
                    new_name = f"{base}_{timestamp}{ext}"
                    dest_path = os.path.join(thumbnail_dir, new_name)

                shutil.copy2(path, dest_path)
                self.add_thumbnail(os.path.basename(dest_path), dest_path)
        except Exception as e:
            print(f"保存缩略图失败: {str(e)}")

    def add_thumbnail(self, name, path):
        """添加缩略图按钮"""
        btn = QPushButton(name)
        btn.setIcon(QIcon(path))
        btn.setIconSize(QSize(180, 120))
        btn.setStyleSheet("background-color: white;")
        btn.clicked.connect(partial(self.thumbnail_clicked, path))
        self.ui.thumbnail_layout.addWidget(btn)

    def load_thumbnails(self):
        """加载缩略图"""
        thumbnail_dir = './thumbnail'
        if not os.path.exists(thumbnail_dir):
            os.makedirs(thumbnail_dir)
        for fname in os.listdir(thumbnail_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.add_thumbnail(fname, os.path.join(thumbnail_dir, fname))

    def load_text_files(self):
        """加载文本文件列表"""
        texts_dir = './texts'
        if not os.path.exists(texts_dir):
            os.makedirs(texts_dir)
        self.ui.text_list.clear()
        for fname in os.listdir(texts_dir):
            if fname.lower().endswith('.txt'):
                self.ui.text_list.addItem(fname)

    def add_text_file(self, fname):
        """添加文本文件到列表"""
        if fname not in [self.ui.text_list.item(i).text()
                         for i in range(self.ui.text_list.count())]:
            self.ui.text_list.addItem(fname)

    def thumbnail_clicked(self, path):
        """缩略图点击事件"""
        self.image_path = path
        self.core.image_path = path
        print(f"选择的缩略图: {path}")
        if self.all_files_selected():
            self.update_wordcloud()

    def on_text_selected(self, text):
        """文本文件选择事件"""
        if text:
            path = os.path.join('./texts', text)
            self.text_file_path = path
            self.core.text_file_path = path
            print(f"选择的文本文件: {path}")
            if self.all_files_selected():
                self.update_wordcloud()

    # 颜色操作方法
    def choose_base_color(self):
        """选择基础颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            self.core.base_color = color_hex
            self.ui.lbl_base_color.setStyleSheet(f"background-color: {color_hex};")
            if self.all_files_selected():
                self.update_wordcloud()

    def choose_similar_color(self):
        """选择相似颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            self.core.similar_colors.append(color_hex)
            self.add_color_label(color_hex, self.ui.similar_layout)
            if self.all_files_selected():
                self.update_wordcloud()

    def choose_contrast_color(self):
        """选择对比颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            self.core.contrast_colors.append(color_hex)
            self.add_color_label(color_hex, self.ui.contrast_layout)
            if self.all_files_selected():
                self.update_wordcloud()

    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            color_hex = color.name()
            self.core.bg_color = color_hex
            self.ui.lbl_bg_color.setStyleSheet(f"background-color: {color_hex};")
            if self.all_files_selected():
                self.update_wordcloud()

    def add_color_label(self, color_hex, layout):
        """添加颜色标签"""
        lbl = QLabel()
        lbl.setFixedSize(20, 20)
        lbl.setStyleSheet(f"background-color: {color_hex};")
        layout.addWidget(lbl)

    # 词云操作方法
    def update_wordcloud(self):
        """更新词云图"""
        self.core.set_font(self.ui.font_combobox.currentText())
        success, message = self.core.generate_wordcloud()
        if success:
            self.show_wordcloud()
        else:
            QMessageBox.warning(self, "生成失败", message)

    def show_wordcloud(self):
        """显示词云图"""
        if os.path.exists('./wordcloud.png'):
            pixmap = QPixmap('./wordcloud.png')
            if pixmap.width() > self.ui.wordcloud_label.width():
                pixmap = pixmap.scaled(
                    self.ui.wordcloud_label.width(),
                    self.ui.wordcloud_label.height(),
                    Qt.KeepAspectRatio
                )
            self.ui.wordcloud_label.setPixmap(pixmap)

    def export_wordcloud(self):
        """导出词云图"""
        if os.path.exists('./wordcloud.png'):
            export_dir = './export'
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(export_dir, f'wordcloud_{timestamp}.png')
            shutil.copy2('./wordcloud.png', export_path)
            QMessageBox.information(self, "导出成功", f"文件已导出到: {export_path}")
        else:
            QMessageBox.warning(self, "导出失败", "没有可以导出的词云文件")

    def save_as_wordcloud(self):
        """另存为词云图"""
        if os.path.exists('./wordcloud.png'):
            path, _ = QFileDialog.getSaveFileName(
                self,
                "保存词云图",
                "",
                "PNG文件 (*.png);;JPEG文件 (*.jpg *.jpeg);;BMP文件 (*.bmp)"
            )
            if path:
                shutil.copy2('./wordcloud.png', path)
                QMessageBox.information(self, "保存成功", f"文件已保存到: {path}")
        else:
            QMessageBox.warning(self, "保存失败", "没有可以保存的词云文件")

    # 数据库操作方法
    def add_text_to_db(self):
        """添加文本到数据库"""
        path, _ = QFileDialog.getOpenFileName(self, "选择文本文件", "", "Text Files (*.txt)")
        if path:
            path = os.path.normpath(path)
            success, msg = self.core.add_to_database(text_path=path)
            if success:
                QMessageBox.information(self, "成功", msg)
                # 创建本地副本
                texts_dir = './texts'
                if not os.path.exists(texts_dir):
                    os.makedirs(texts_dir)
                dest_path = os.path.join(texts_dir, os.path.basename(path))
                if not os.path.exists(dest_path):
                    shutil.copy2(path, dest_path)
                # 更新文本列表
                text_name = os.path.basename(path)
                self.add_text_file(text_name)
            else:
                QMessageBox.warning(self, "失败", msg)

    def add_image_to_db(self):
        """添加图片到数据库"""
        path, _ = QFileDialog.getOpenFileName(self, "选择图片文件",
                                              "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if path:
            path = os.path.normpath(path)
            success, msg = self.core.add_to_database(image_path=path)
            if success:
                QMessageBox.information(self, "成功", msg)
                # 创建本地副本并添加缩略图
                self.save_thumbnail(path)
            else:
                QMessageBox.warning(self, "失败", msg)

    def add_both_to_db(self):
        """同时添加图片和文本到数据库"""
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图片文件",
                                                    "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if not image_path:
            return

        text_path, _ = QFileDialog.getOpenFileName(self, "选择文本文件",
                                                   "", "Text Files (*.txt)")
        if not text_path:
            return

        image_path = os.path.normpath(image_path)
        text_path = os.path.normpath(text_path)

        success, msg = self.core.add_to_database(image_path=image_path, text_path=text_path)
        if success:
            QMessageBox.information(self, "成功", msg)
            # 创建本地副本
            texts_dir = './texts'
            if not os.path.exists(texts_dir):
                os.makedirs(texts_dir)
            dest_text_path = os.path.join(texts_dir, os.path.basename(text_path))
            if not os.path.exists(dest_text_path):
                shutil.copy2(text_path, dest_text_path)
            # 更新UI
            self.save_thumbnail(image_path)
            self.add_text_file(os.path.basename(text_path))
        else:
            QMessageBox.warning(self, "失败", msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WordCloudApp()
    window.show()
    sys.exit(app.exec_())
