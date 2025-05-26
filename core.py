#core.py
import os
import jieba
import imageio
from wordcloud import WordCloud
import random
import pyodbc
from datetime import datetime


class WordCloudCore:
    def __init__(self):
        self.image_path = ''
        self.font_path = ''
        self.text_file_path = ''
        self.base_color = '#000000'
        self.similar_colors = []
        self.contrast_colors = []
        self.bg_color = '#ffffff'
        self.scale = 4  # 默认scale值

        # 初始化数据库连接
        self.conn = self._init_database()
        self._create_tables()

    def _init_database(self):
        """初始化数据库连接"""  #需要填写自己的数据库连接信息
        connection_string = (
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=.;'
            'DATABASE=WordCloudDB;'
            'UID=sa;'
            'PWD=PASSWORD;'
            'Charset=UTF8;'
        )
        return pyodbc.connect(connection_string)

    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()

        # 检查表是否存在
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='WordCloudData' AND xtype='U')
        CREATE TABLE WordCloudData (
            ID INT PRIMARY KEY IDENTITY(1,1),
            ImageName NVARCHAR(255) NULL,
            ImageData VARBINARY(MAX) NULL,
            TextFileName NVARCHAR(255) NULL,
            TextData NVARCHAR(MAX) NULL,
            CreatedDate DATETIME DEFAULT GETDATE()
        )
        """)
        self.conn.commit()

    # 数据库操作方法
    def add_to_database(self, image_path=None, text_path=None):
        """通用添加方法，可单独或同时添加图片和文本"""
        if image_path and not os.path.exists(image_path):
            return False, f"图片文件不存在: {image_path}"
        if text_path and not os.path.exists(text_path):
            return False, f"文本文件不存在: {text_path}"

        try:
            cursor = self.conn.cursor()
            params = {}

            if image_path:
                with open(image_path, 'rb') as f:
                    params['ImageName'] = os.path.basename(image_path)
                    params['ImageData'] = f.read()

            if text_path:
                with open(text_path, 'r', encoding='utf-8') as f:
                    params['TextFileName'] = os.path.basename(text_path)
                    params['TextData'] = f.read()

            columns = ', '.join(params.keys())
            values = ', '.join(['?'] * len(params))

            cursor.execute(f"INSERT INTO WordCloudData ({columns}) VALUES ({values})",
                           tuple(params.values()))
            self.conn.commit()

            return True, "文件已成功添加到数据库"
        except Exception as e:
            return False, f"添加失败: {str(e)}"


    def delete_from_database(self, image_name=None, text_name=None):
        """从数据库删除图片或文本"""
        try:
            cursor = self.conn.cursor()
            if image_name and text_name:
                cursor.execute("DELETE FROM WordCloudData WHERE ImageName=? AND TextFileName=?",
                               (image_name, text_name))
            elif image_name:
                cursor.execute("DELETE FROM WordCloudData WHERE ImageName=?", (image_name,))
            elif text_name:
                cursor.execute("DELETE FROM WordCloudData WHERE TextFileName=?", (text_name,))
            else:
                return False, "必须提供图片名或文本名"
            self.conn.commit()
            return cursor.rowcount > 0, "删除成功"
        except Exception as e:
            self.conn.rollback()
            return False, f"数据库操作失败: {str(e)}"



    def set_colors(self, base, similar, contrast, bg):
        self.base_color = base
        self.similar_colors = similar
        self.contrast_colors = contrast
        self.bg_color = bg

    def set_font(self, font_name):
        font_map = {
            'SimHei': 'simhei.ttf',
            'Arial': 'arial.ttf',
            'Times New Roman': 'times.ttf'
        }
        font_file = font_map.get(font_name, 'simhei.ttf')
        self.font_path = os.path.join('C:/Windows/Fonts', font_file)

    def generate_wordcloud(self):
        if not all([self.image_path, self.text_file_path]):
            return False, "请先选择底图和文本文件"

        try:
            text = self.read_text_file()
            words = self.process_text(text)
            mask = imageio.imread(self.image_path)
            wordcloud = self.create_wordcloud(mask, words)
            wordcloud.to_file('./wordcloud.png')
            return True, "生成成功"
        except Exception as e:
            return False, f"生成失败: {str(e)}"

    def create_wordcloud(self, mask, words):
        color_func = self.get_color_func()
        return WordCloud(
            font_path=self.font_path,
            background_color=self.bg_color,
            scale=self.scale,  # 使用scale参数
            max_words=1000,
            mask=mask,
            color_func=color_func
        ).generate_from_frequencies(words)

    def read_text_file(self):
        if os.path.exists(self.text_file_path):
            with open(self.text_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"文件不存在: {self.text_file_path}")
            return ""

    def process_text(self, text):
        rp_str = ['，', '。', '！', '？', '、', '：', '；', '（', '）', '《', '》',
                  '“', '”', '‘', '’', '【', '】', '—', '…', '·', '～', ' ']
        for char in rp_str:
            text = text.replace(char, '')
        words = jieba.lcut(text)
        stopwords = self.load_stopwords()
        return {w: cnt for w, cnt in self.count_words(words) if w not in stopwords and len(w) > 1}

    def count_words(self, words):
        from collections import Counter
        return Counter(words).most_common()

    def load_stopwords(self):
        if os.path.exists('stopwords.txt'):
            with open('stopwords.txt', 'r', encoding='utf-8') as f:
                return set(f.read().splitlines())
        return set()


    def get_color_func(self):
        colors = [self.base_color] + self.similar_colors + self.contrast_colors
        return lambda *args, **kwargs: random.choice(colors) if colors else '#000000'
