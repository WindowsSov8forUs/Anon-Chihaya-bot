# -*- coding: utf-8 -*-
# !/usr/bin/python3
import os
import re
import math
import requests
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

from adapter.message import Message

# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(__file__)

# 以指定字符串为始终点切割字符串
def str_cut_out(
    str: str,
    str_begin: str='',
    str_end: str='',
    type_: bool=True
) -> str:
    '''以指定字符串为始终点切割字符串

    :param str: 要切割的字符串
    :type str: str
    :param str_begin: 起始标志字符串。若留空则表示从字符串的开头开始切割
    :type str_begin: str, optional
    :param str_end: 终止标志字符串。若留空则表示从字符串的结尾开始切割
    :type str_end: str, optional
    :param type_: 切割方式标识。True 表示保留标志字符串，False 表示不保留标志字符串，默认为 True
    :type type_: bool, optional
    :return: 得到的字符串，若没有要提取的字符串则返回一个空字符串
    :rtype: str
    '''
    # 检测起始点
    if str_begin != '':
        begin_index = str.find(str_begin)
        if begin_index == -1: # 如果没找到则视为未指定
            str_begin = ''
            begin_index = 0
    else:
        begin_index = 0
    # 检测终点
    if str_end != '':
        end_index = str.find(str_end,begin_index + len(str_begin))
        if end_index == -1: # 如果没找到则视为未指定
            str_end = ''
            end_index = len(str)
    else:
        end_index = len(str)
    # 切割
    if type_:
        str_print = str[begin_index:end_index + len(str_end)]
    else:
        str_print = str[begin_index + len(str_begin):end_index]

    # 返回切割结果
    return str_print

# 以指定字符串为始终点从字符串中切除
def str_remove(
    str: str,
    str_begin: str='',
    str_end: str='',
    type_: bool=True
) -> str:
    '''以指定字符串为始终点切除字符串

    :param str: 要切除的字符串
    :type str: str
    :param str_begin: 起始标志字符串。若留空则表示从字符串的开头开始切除
    :type str_begin: str, optional
    :param str_end: 终止标志字符串。若留空则表示切除到字符串的结尾
    :type str_end: str, optional
    :param type_: 切割方式标识。True 表示保留标志字符串，False 表示不保留标志字符串，默认为 True
    :type type_: bool, optional
    :raises ValueError: 要切除的字符串不存在
    :return: 得到的字符串
    :rtype: str
    '''
    # 检测起始点
    if str_begin != '':
        begin_index = str.find(str_begin)
    else:
        begin_index = 0
    # 检测终点
    if str_end != '':
        end_index = str.find(str_end,begin_index + len(str_begin))
    else:
        end_index = len(str)
    # 检测是否存在
    if begin_index == -1 or end_index == -1:
        # 要切除的字符串不存在
        raise ValueError('要切除的字符串不存在。')
    # 切除
    if type_:
        str_print = str[:begin_index + len(str_begin)] + str[end_index:]
    else:
        str_print = str[:begin_index] + str[end_index + len(str_end):]

    # 返回切割结果
    return str_print

# 换行切割字符串
def break_line(line_get: str, width_limit: int, font: ImageFont.FreeTypeFont) -> str:
    '''换行切割字符串，输入需要切割的字符串及每行限制长度，返回切割后的字符串

    :param line_get: 需要切割的字符串
    :type line_get: str
    :param width_limit: 每行限制像素长度
    :type width_limit: int
    :param font: 使用的字体 `PIL.ImageFont.FreeTypeFont`
    :type font: ImageFont.FreeTypeFont
    :return: 切割后的字符串
    :rtype: str
    '''
    TABLE_WIDTH = 4
    result = ''
    width = 0
    for chr in line_get:
        if chr == '️': # 不可见字符
            chr = ''
        elif chr == '⃣': # 占位字符
            chr = ''
        elif chr == '\n': # 换行字符
            width = 0
            result += ' ' + chr
        elif chr == '\t': # 制表符字符
            width += TABLE_WIDTH * font.getlength(' ')
            result += chr
        else: # 其他字符
            font_width = font.getlength(chr)
            if (width + font_width) > width_limit: # 剩余宽度不够
                width = font_width
                result += '\n' + chr
            else:
                width += font_width
                result += chr
        if width >= width_limit:
            result += '\n'
            width = 0
            
    if result.endswith('\n'):
        return result
    return result + '\n'

# 文字转图片函数
def text_to_image(message: Message) -> BytesIO:
    '''文字转图片函数

    :param message: 要转换的文字
    :type message: Message
    :return: 转换成的图片对象的 `BytesIO` 对象
    :rtype: BytesIO
    '''
    # 绘制背景
    def paper_background(size: tuple[int, int]) -> Image.Image:
        '''绘制背景

        :param size: 背景大小
        :type size: tuple[int, int]
        :return: 绘制出的背景
        :rtype: Image.Image
        '''
        raw_paper = Image.open(CURRENT_DIR + '/resources/asset/paper_back.png').convert('RGBA')
        # 计算图片大小
        width = raw_paper.size[0]
        height = int(size[1] / size[0] * width)
        
        paper = Image.new('RGBA', (width, height))
        paper.paste(raw_paper, (0, 0), raw_paper) # 预粘贴
        
        # 构建纸张背景
        if height > raw_paper.size[1]: # 如果要求的高度大于素材高度
            y_cor = 964
            while True: # 开始粘贴
                raw_paper = raw_paper.transpose(Image.FLIP_TOP_BOTTOM) # 对素材进行上下翻转
                paper.paste(raw_paper, (0, y_cor), raw_paper) # 粘贴
                y_cor += 1017 # 增加 y 坐标
                if y_cor >= height: # 如果已经超过指定高度
                    break
                raw_paper = raw_paper.transpose(Image.FLIP_TOP_BOTTOM) # 对素材进行上下翻转
                paper.paste(raw_paper, (0, y_cor), raw_paper) # 粘贴
                y_cor += 964 # 增加 y 坐标
                if y_cor >= height: # 如果已经超过指定高度
                    break
            
        paper = paper.resize(size) # 修改大小至要求的大小
        
        return paper

    # 将文本中可能出现的对象码进行转换提取，并处理文本
    def text_process(message: Message) -> tuple[list[str], list[Image.Image]]:
        '''将文本中可能出现的对象码进行转换提取，并处理文本

        :param message: 要转换提取的文本
        :type message: Message
        :return: 提取后的文本片段列表和图片列表
        :rtype: tuple[list[str], list[Image.Image]]
        '''
        # 图片提取
        def get_message_image(url: str) -> Image.Image:
            '''_summary_

            :param url: 图片 URL
            :type url: str
            :raises FileNotFoundError: 图片未找到
            :return: `Image` 格式的图片
            :rtype: Image.Image
            '''
            # 检测图片 URL 是否存在
            def image_url_check(image_url: str) -> bool:
                '''检测图片 URL 是否存在

                :param image_url: 需要检测的图片 URL
                :type image_url: str
                :return: 图片 URL 是否存在
                :rtype: bool
                '''
                image_formats = ('image/png', 'image/jpeg', 'image/jpg', 'image/gif')
                response = requests.head(image_url)

                #检测是否符合格式
                return response.headers['content-type'] in image_formats

            # 判断、打开并返回图片
            if image_url_check(url):
                response = requests.get(url)
                image_data = response.content
                image_get = Image.open(BytesIO(image_data)).convert('RGBA')
                
                return image_get
            else:
                raise FileNotFoundError('Image Not Found')

        text_list: list[str] = [] # 结果列表
        image_list: list[Image.Image] = [] # 图片列表
        # 遍历初始列表并处理
        for segment in message:
            match segment.type: # 比对消息片段类型
                case 'at': # @某人
                    text_list.append('![at]({})'.format(segment.data['qq']))
                case 'image': # 图片
                    try: # 尝试获取图片
                        if not (image_url := segment.data.get('url')) is None:
                            image = get_message_image(image_url)
                        else:
                            image = Image.open(segment.data['file'][8:]).convert('RGBA')
                        if image.size[0] > 200: # 缩放
                            image = image.resize((200, int(image.size[1] / image.size[0] * 200)))
                        image_list.append(image)
                        text_list.append('![image]()'.format(len(image_list)))
                    except: # 图片失效
                        text_list.append('![image](图片失效)')
                case 'text': # 纯文本
                    frags = re.split(r'(\n)', segment.data['text']) # 切片
                    for frag in frags:
                        if frag == '\n': # 如果是换行符
                            text_list.append('![newline]')
                        else:
                            text_list.append(frag)
                case _: # 其他种类不会计入
                    continue
                    
        return text_list, image_list

    WIDTH = 800
    LINE_SPACE = 38
    text_font = ImageFont.truetype(CURRENT_DIR + '/resources/asset/fonts/AaKaiSong.ttf', 20)
    raw_text_list, image_list = text_process(message)
    text_list: list[list[str]] = []
    # 再次处理
    single_line_text: list[str] = []
    line_length = 0
    for frag in raw_text_list:
        if frag == '![newline]': # 如果是换行
            if len(single_line_text) > 0:
                text_list.append(single_line_text)
                single_line_text = []
                line_length = 0
            continue
        
        # 计算图片宽度
        if frag.startswith('![image]') and not frag.startswith('![image](图片失效)'):
            image_index = int(str_cut_out(frag, '![image](', ')', False)) - 1 # 提取图片序号
            image_width = image_list[image_index].size[0] + 10 # 获取图片宽度
            if line_length + image_width > WIDTH: # 如果超过了宽度
                if len(single_line_text) > 0:
                    text_list.append(single_line_text)
                    single_line_text = []
                    line_length = 0
            single_line_text.append(frag)
            line_length += image_width
            continue
            
        # 计算文本宽度
        frag_width = text_font.getlength(frag) # 获取片段宽度
        if line_length + frag_width > WIDTH: # 如果超过了宽度
            # 分割该片段
            frag_list = break_line(frag, WIDTH - int(line_length), text_font).rstrip('\n').split('\n')
            for index, frag_elem in enumerate(frag_list):
                if index == 0: # 如果是第一项
                    single_line_text.append(frag_elem)
                    text_list.append(single_line_text)
                    single_line_text = []
                    line_length = 0
                elif (index + 1) == len(frag_list): # 如果是最后一项
                    single_line_text.append(frag_elem)
                    line_length += text_font.getlength(frag_elem)
                else: # 如果不止两项
                    text_list.append([frag_elem])
        else:
            single_line_text.append(frag)
            line_length += text_font.getlength(frag)
    
    # 计算大小并获取背景
    height = 18
    height_list: list[int] = []
    for frag_list in text_list: # 遍历计算高度
        frag_height_list: list[int] = []
        for frag in frag_list: # 遍历统计高度
            if frag.startswith('![image]') and not frag.startswith('![image](图片失效)'):
                # 如果是图片则添加图片高度
                image_index = int(str_cut_out(frag, '![image](', ')', False)) - 1 # 提取图片序号
                image_height = image_list[image_index].size[1] # 获取图片高度
                # 获取绘制高度
                line_num = math.ceil(image_height / LINE_SPACE)
                frag_height_list.append(LINE_SPACE * line_num)
            else:
                frag_height_list.append(LINE_SPACE)
        height_list.append(max(frag_height_list))
        height += max(frag_height_list)
    height += 20
    image = paper_background((WIDTH + 40, height))
    draw = ImageDraw.Draw(image)
    
    # 遍历绘制文本
    x_cor = 20
    y_cor = 50 - LINE_SPACE
    for index, frag_list in enumerate(text_list): # 遍历多行列表
        x_cor = 20
        y_cor += height_list[index]
        for frag in frag_list: # 遍历绘制单行
            if frag.startswith('![image]') and not frag.startswith('![image](图片失效)'):
                # 如果是图片则绘制图片
                image_index = int(str_cut_out(frag, '![image](', ')', False)) - 1 # 提取图片序号
                frag_image = image_list[image_index] # 获取图片
                image.paste(frag_image, (x_cor + 5, y_cor - frag_image.size[1]), frag_image) # 粘贴图片
                x_cor += frag_image.size[0] + 10 # 计算绘制后 x 坐标
            else:
                bbox = draw.textbbox((x_cor, y_cor), frag, text_font, 'lb')
                draw.text((bbox[0], bbox[1]), frag, 'black', text_font)
                x_cor = bbox[2]
                
    # 保存为 BytesIO 对象
    image_buffer = BytesIO()
    image.save(image_buffer, format='PNG')
        
    return image_buffer
