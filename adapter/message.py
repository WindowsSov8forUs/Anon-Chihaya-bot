'''Go-cqhttp 消息类型。
WindowsSov8 Anon Bot 自用 Adapter
'''
# -*- coding: utf-8 -*-
# !/usr/bin/python3
import re
from io import BytesIO
from pathlib import Path
from copy import deepcopy
from pydantic import BaseModel
from collections.abc import Iterable
from typing import Iterable, Optional, Literal, Union, Any

from .utils import f2s, escape, unescape

# 消息段类
class MessageSegment(BaseModel):
    '''消息段类'''
    type: str
    '''消息段类型'''
    data: dict[str, Any]
    '''消息段数据'''
    # 将消息段转换为 CQ 码字符串
    def __str__(self) -> str:
        '''将消息段转换为 CQ 码字符串'''
        if self.is_text():
            return escape(self.data.get('text', ''), escape_comma=False)
        
        params = ','.join(
            [f'{key}={str(value)}' for key, value in self.data.items() if value is not None]
        )
        return f"[{self.type}{',' if params else ''}{params}]"
    
    # 定义加法行为
    def __add__(
        self, other: Union[str, 'MessageSegment', Iterable['MessageSegment']]
    ) -> 'Message':
        return Message(self) + (
            MessageSegment.text(other) if isinstance(other, str) else other
        )
        
    # 定义反向加法行为
    def __radd__(
        self, other: Union[str, 'MessageSegment', Iterable['MessageSegment']]
    ) -> 'Message':
        return (
            MessageSegment.text(other) if isinstance(other, str) else Message(other)
        ) + self
    
    # 返回消息段是否为字符串
    def is_text(self) -> bool:
        '''返回消息段是否为字符串'''
        return self.type == 'text'
    
    # 文本
    @staticmethod
    def text(text: str) -> 'MessageSegment':
        '''文本

        :param text: 文本值
        :type text: str
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='text',
            data={'text': text}
        )
    
    # QQ 表情
    @staticmethod
    def face(id_: int) -> 'MessageSegment':
        '''QQ 表情

        :param id_: QQ 表情 ID
        :type id_: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='face',
            data={'id': id_}
        )
    
    # 语音
    @staticmethod
    def record(
        file: Union[str, bytes, BytesIO, Path],
        magic: Optional[Literal[0, 1]]=None,
        cache: Optional[Literal[0, 1]]=None,
        proxy: Optional[Literal[0, 1]]=None,
        timeout: Optional[int]=None
    ) -> 'MessageSegment':
        '''语音

        :param file: 语音文件名
        :type file: Union[str, bytes, BytesIO, Path]
        :param magic: 发送时可选, 默认 `0`, 设置为 `1` 表示变声
        :type magic: Optional[Literal[0, 1]], optional
        :param cache: 只在通过网络 URL 发送时有效, 表示是否使用已缓存的文件, 默认 `1`
        :type cache: Optional[Literal[0, 1]], optional
        :param proxy: 只在通过网络 URL 发送时有效, 表示是否通过代理下载文件 ( 需通过环境变量或配置文件配置代理 ) , 默认 `1`
        :type proxy: Optional[Literal[0, 1]], optional
        :param timeout: 只在通过网络 URL 发送时有效, 单位秒, 表示下载网络文件的超时时间 , 默认不超时
        :type timeout: Optional[int], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='record',
            data={
                'file': f2s(file),
                'magic': magic,
                'cache': cache,
                'proxy': proxy,
                'timeout': timeout
            }
        )
    
    # 短视频
    @staticmethod
    def video(
        file: Union[str, Path],
        cover: Union[str, bytes, BytesIO, Path],
        c: Optional[Literal[2, 3]]=None
    ) -> 'MessageSegment':
        '''短视频

        :param file: 视频地址, 支持http和file发送
        :type file: Union[str, Path]
        :param cover: 视频封面, 支持http, file和base64发送, 格式必须为jpg
        :type cover: Union[str, bytes, BytesIO, Path]
        :param c: 通过网络下载视频时的线程数, 默认单线程. (在资源不支持并发时会自动处理)
        :type c: Optional[Literal[2, 3]], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='video',
            data={
                'file': f2s(file),
                'cover': f2s(cover),
                'c': c
            }
        )
    
    # @某人
    @staticmethod
    def at(qq: Union[int, str], name: Optional[str]=None) -> 'MessageSegment':
        '''@某人

        :param qq: @的 QQ 号, `all` 表示全体成员
        :type qq: Union[int, str]
        :param name: 当在群中找不到此QQ号的名称时才会生效
        :type name: Optional[str], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='at',
            data={
                'qq': qq,
                'name': name
            }
        )
    
    # 链接分享
    @staticmethod
    def share(
        url: str,
        title: str,
        content: Optional[str]=None,
        image: Optional[str]=None
    ) -> 'MessageSegment':
        '''链接分享

        :param url: URL
        :type url: str
        :param title: 标题
        :type title: str
        :param content: 发送时可选, 内容描述
        :type content: Optional[str], optional
        :param image: 发送时可选, 图片 URL
        :type image: Optional[str], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='share',
            data={
                'url': url,
                'title': title,
                'content': content,
                'image': image
            }
        )
    
    # 音乐分享
    @staticmethod
    def music(type_: Literal['qq', '163', 'xm'], id_: int) -> 'MessageSegment':
        '''音乐分享

        :param type_: 分别表示使用 QQ 音乐、网易云音乐、虾米音乐
        :type type_: Literal[&#39;qq&#39;, &#39;163&#39;, &#39;xm&#39;]
        :param id_: 歌曲 ID
        :type id_: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='music',
            data={
                'type': type_,
                'id': id_
            }
        )
    
    # 音乐自定义分享
    @staticmethod
    def music_custom(
        url: str,
        audio: str,
        title: str,
        content: Optional[str]=None,
        image: Optional[str]=None
    ) -> 'MessageSegment':
        '''音乐自定义分享

        :param url: 点击后跳转目标 URL
        :type url: str
        :param audio: 音乐 URL
        :type audio: str
        :param title: 标题
        :type title: str
        :param content: 发送时可选, 内容描述
        :type content: Optional[str], optional
        :param image: 发送时可选, 图片 URL
        :type image: Optional[str], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='music',
            data={
                'type': 'custom',
                'url': url,
                'audio': audio,
                'title': title,
                'content': content,
                'image': image
            }
        )
    
    # 图片
    @staticmethod
    def image(
        file: Union[str, bytes, BytesIO, Path],
        type_: Optional[Literal['flash', 'show']]=None,
        subType: Optional[int]=None,
        url: Optional[str]=None,
        cache: Optional[Literal[0, 1]]=None,
        id_: Optional[int]=None,
        c: Optional[Literal[2, 3]]=None
    ) -> 'MessageSegment':
        '''图片

        :param file: 图片文件名
        :type file: Union[str, bytes, BytesIO, Path]
        :param type_: 图片类型, `flash` 表示闪照, `show` 表示秀图, 默认普通图片
        :type type_: Optional[Literal[&#39;flash&#39;, &#39;show&#39;]], optional
        :param subType: 图片子类型, 只出现在群聊.
        :type subType: Optional[int], optional
        :param url: 图片 URL
        :type url: Optional[str], optional
        :param cache: 只在通过网络 URL 发送时有效, 表示是否使用已缓存的文件, 默认 `1`
        :type cache: Optional[Literal[0, 1]], optional
        :param id_: 发送秀图时的特效id, 默认为40000
        :type id_: Optional[int], optional
        :param c: 通过网络下载图片时的线程数, 默认单线程. (在资源不支持并发时会自动处理)
        :type c: Optional[Literal[2, 3]], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='image',
            data={
                'file': f2s(file),
                'type': type_,
                'subType': subType,
                'url': url,
                'cache': cache,
                'id': id_,
                'c': c
            }
        )
    
    # 回复
    @staticmethod
    def reply(id_: int) -> 'MessageSegment':
        '''回复

        :param id_: 回复时所引用的消息id, 必须为本群消息.
        :type id_: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='reply',
            data={'id': id_}
        )
    
    # 自定义回复
    @staticmethod
    def reply_custom(
        text: str,
        qq: int,
        time: int,
        seq: int
    ) -> 'MessageSegment':
        '''自定义回复

        :param text: 自定义回复的信息
        :type text: str
        :param qq: 自定义回复时的自定义QQ, 如果使用自定义信息必须指定.
        :type qq: int
        :param time: 自定义回复时的时间, 格式为Unix时间
        :type time: int
        :param seq: 起始消息序号, 可通过 `get_msg` 获得
        :type seq: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='reply',
            data={
                'text': text,
                'qq': qq,
                'time': time,
                'seq': seq
            }
        )
    
    # 戳一戳
    @staticmethod
    def poke(qq: int) -> 'MessageSegment':
        '''戳一戳

        :param qq: 需要戳的成员
        :type qq: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='poke',
            data={'qq': qq}
        )
    
    # 礼物
    @staticmethod
    def gift(qq: int, id_: int) -> 'MessageSegment':
        '''礼物

        :param qq: 接收礼物的成员
        :type qq: int
        :param id_: 礼物的类型
        :type id_: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='gift',
            data={'qq': qq, 'id': id_}
        )
        
    # 合并转发消息节点
    @staticmethod
    def node(id_: int) -> 'MessageSegment':
        '''合并转发消息节点

        :param id_: 转发消息id
        :type id_: int
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='node',
            data={'id': id_}
        )
    
    # 自定义合并转发消息节点
    @staticmethod
    def node_custom(
        name: str,
        uin: int,
        content: Union[str, 'MessageSegment'],
        seq: Optional[int]=None
    ) -> 'MessageSegment':
        '''自定义合并转发消息节点

        :param name: 发送者显示名字
        :type name: str
        :param uin: 发送者QQ号
        :type uin: int
        :param content: 具体消息
        :type content: Union[str, &#39;MessageSegment&#39;]
        :param seq: 具体消息
        :type seq: Optional[int], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='node',
            data={
                'name': name,
                'uin': uin,
                'content': content,
                'seq': seq
            }
        )
    
    # XML 消息
    @staticmethod
    def xml(data: str, resid: Optional[int]=None) -> 'MessageSegment':
        '''XML 消息

        :param data: xml内容, xml中的value部分, 记得实体化处理
        :type data: str
        :param resid: 可能为空, 或空字符串
        :type resid: Optional[int], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='xml',
            data={'data': data, 'resid': resid}
        )
    
    # JSON 消息
    @staticmethod
    def json(data: str, resid: Optional[int]=None) -> 'MessageSegment':
        '''JSON 消息

        :param data: json内容, json的所有字符串记得实体化处理
        :type data: str
        :param resid: 可能为空, 或空字符串
        :type resid: Optional[int], optional
        :return: 消息段对象
        :rtype: MessageSegment
        '''
        return MessageSegment(
            type='json',
            data={'data': escape(data), 'resid': resid}
        )
    
# 消息数组类
class Message(list[MessageSegment]):
    '''消息数组'''
    # 初始化方法
    def __init__(self, message: Union[str, None, Iterable[MessageSegment], MessageSegment]=None):
        '''消息数组

        :param message: 消息内容
        :type message: Union[str, None, Iterable[MessageSegment], MessageSegment], optional
        '''
        super().__init__()
        if message is None: # 如果没有
            return
        elif isinstance(message, str): # 如果是字符串
            self.extend(self._construct(message))
        elif isinstance(message, MessageSegment): # 如果是消息段
            self.append(message)
        elif isinstance(message, Iterable): # 如果是可迭代的消息段对象
            self.extend(message)
        else: # 其他对象
            self.extend(self._construct(message))
    
    # 将消息段转换为 CQ 码字符串
    def __str__(self) -> str:
        '''将消息段转换为 CQ 码字符串'''
        return ''.join(str(seg) for seg in self)
    
    # 定义加法行为
    def __add__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> 'Message':
        result = self.copy()
        other = MessageSegment.text(other) if isinstance(other, str) else other
        result += other
        return result
    
    # 定义反向加法行为
    def __radd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> 'Message':
        other = MessageSegment.text(other) if isinstance(other, str) else other
        result = self.__class__(other)
        return result + self
    
    # 定义原地加法行为
    def __iadd__(
        self, other: Union[str, MessageSegment, Iterable[MessageSegment]]
    ) -> 'Message':
        if isinstance(other, str):
            self.extend(self._construct(other))
        elif isinstance(other, MessageSegment):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)
        else:
            raise TypeError(f'不支持的类型：{type(other)!r}')
        return self
    
    # 定义 list 属性
    @property
    def __list__(self) -> list[dict[str, Any]]:
        '''`list` 属性'''
        return [seg.model_dump() for seg in self]
    
    # 是否为纯文本消息
    def is_text(self) -> bool:
        '''返回是否为纯文本消息'''
        for seg in self:
            if not seg.is_text():
                return False
        
        return True
    
    # 是否为合并转发消息
    def is_forward(self) -> bool:
        '''返回是否为合并转发消息，该类消息只允许 node 类型消息段'''
        for seg in self:
            if seg.type != 'node':
                return False
        
        return True
    
    # 构造消息数组
    @staticmethod
    def _construct(message: str) -> Iterable[MessageSegment]:
        '''构造消息数组

        :param message: 原始消息字符串
        :type message: str
        :return: 可迭代消息段对象
        :rtype: Iterable[MessageSegment]
        '''
        # 迭代原始消息字符串
        def _iter_message(message:str) -> Iterable[tuple[str, str]]:
            '''迭代原始消息字符串

            :param message: 原始消息字符串
            :type message: str
            :return: 处理后的可迭代字符串元组，包含消息段类型与非处理的消息段数据
            :rtype: Iterable[tuple[str, str]]
            '''
            text_begin = 0
            for cq_code in re.finditer(
                r"\[CQ:(?P<type>[a-zA-Z0-9-_.]+)"
                r"(?P<params>"
                r"(?:,[a-zA-Z0-9-_.]+=[^,\]]*)*"
                r"),?\]",
                message
            ):
                yield 'text', message[text_begin: cq_code.pos + cq_code.start()]
                text_begin = cq_code.pos + cq_code.end()
                yield cq_code.group('type'), cq_code.group('params').lstrip(',')
            yield 'text', message[text_begin:]
            
        for type_, data_ in _iter_message(message):
            if type_ == 'text':
                if data_ != '': # 只会处理非空字符串
                    yield MessageSegment(
                        type=type_,
                        data={'text': unescape(data_)}
                    )
            else:
                data_ = {
                    key: unescape(value) for key, value in map(
                        lambda x: x.split('=', maxsplit=1),
                        filter(lambda x: x, (x.lstrip() for x in data_.split(',')))
                    )
                }
                yield MessageSegment(
                    type=type_,
                    data=data_
                )
    
    # 添加一个消息段到消息数组末尾
    def append(self, obj: Union[str, MessageSegment]) -> 'Message':
        '''添加一个消息段到消息数组末尾

        :param obj: 要添加的消息段
        :type obj: Union[str, MessageSegment]
        :raises ValueError: 消息段类型不合法
        :return: 添加后的消息数组
        :rtype: Message
        '''        
        if isinstance(obj, MessageSegment): # 如果是消息段
            super().append(obj)
        elif isinstance(obj, str): # 如果是字符串
            self.extend(self._construct(obj))
        else:
            raise ValueError(f'不合法的对象类型：{type(obj)}: {obj}')
        return self
    
    # 拼接消息数组或多个消息段到消息数组末尾
    def extend(self, obj: Union['Message', Iterable[MessageSegment]]) -> 'Message':
        '''拼接消息数组或多个消息段到消息数组末尾

        :param obj: 要添加的消息数组
        :type obj: Union[Message, Iterable[MessageSegment]]
        :return: 拼接后的消息数组
        :rtype: Message
        '''
        for segment in obj:
            self.append(segment)
        return self
    
    # 重写拷贝方法
    def copy(self) -> 'Message':
        '''返回对象的深拷贝对象'''
        return deepcopy(self)
    