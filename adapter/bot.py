'''Go-cqhttp 机器人定义。
WindowsSov8 Anon Bot 自用 Adapter
'''
# -*- coding: utf-8 -*-
# !/usr/bin/python3
import os
from typing import Optional, Literal, Union, Any

from .adapter import Adapter
from .utils import MyJson, Logging
from .message import Message, MessageSegment
from .event import Event, MessageEvent, PokeEvent

# 获取当前文件所在父目录
CURRENT_DIR = os.path.dirname(os.path.dirname(__file__))

# 检查消息中存在的回复
def _check_reply(event: MessageEvent) -> int:
    '''检查消息中存在的回复，返回回复的 message_id

    :param bot: Bot 对象
    :type bot: Bot
    :param event: MessageEvent 对象
    :type event: MessageEvent
    '''
    try:
        index = [x.type == 'reply' for x in event.message].index(True)
    except ValueError:
        return -1
    
    msg_seg = event.message[index]
    message_id = int(msg_seg.data['id'])
    return message_id

# 检查消息是否存在 @机器人
def _check_at_me(bot: 'Bot', event: MessageEvent) -> bool:
    '''检查消息是否存在 @机器人

    :param bot: Bot 对象
    :type bot: Bot
    :param event: MessageEvent 对象
    :type event: MessageEvent
    :return: 是否存在 @机器人
    :rtype: bool
    '''
    if not isinstance(event, MessageEvent):
        return False
    
    if event.message_type == 'private':
        return True
    else:
        for segment in event.message:
            if segment.type == 'at' and segment.data.get('qq', '') == str(event.self_id):
                return True
            
    return False

# Bot 基类
class Bot:
    '''Bot 基类'''
    # 创建一个 Bot 基类
    def __init__(self, self_id: int, host_id: int, adapter: Adapter) -> None:
        '''Bot 基类

        :param self_id: 机器人 ID
        :type self_id: int
        :param host_id: 主人 ID
        :type host_id: int
        :param adapter: 适配器对象
        :type adapter: Adapter
        '''
        self.adapter = adapter
        '''适配器对象'''
        self.self_id = self_id
        '''机器人 ID'''
        self.host_id = host_id
        '''主人 ID'''
        self.admin = self.Admin(host_id)
        '''管理员操作方法'''
        self.block_list = self.BlockList()
        '''黑名单操作方法'''
    
    # POST 数据转换为事件对象
    def post2event(self, data: dict[str, Any]) -> Optional[Event]:
        '''POST 数据转换为事件对象

        :param data: 接收到的 POST 数据
        :type data: dict[str, Any]
        :raises exception: 事件转换失败
        :return: 事件对象
        :rtype: Optional[Event]
        '''
        try: # 尝试转换事件对象
            event = self.adapter.data_to_event(data)
            
            # 记录事件
            if isinstance(event, MessageEvent): # 如果是消息事件
                print(event)
                Logging.info(str(event))
            elif isinstance(event, PokeEvent): # 如果是戳一戳事件
                print_poke = f'(来自群组{event.group_id}){event.user_id} -戳一戳-> {event.target_id}'
                print(print_poke)
                Logging.info(print_poke)
                
            return event
        except Exception as exception:
            raise exception
        
    # 默认回复消息处理函数
    def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        at_sender: bool=False,
        reply_message: bool=False,
        message_type: Optional[Literal['private', 'group']]=None,
        target_id: Optional[int]=None
    ) -> int:
        '''默认回复消息处理函数

        :param event: `adapter.event.Event` 事件对象
        :type event: Event
        :param message: 消息段
        :type message: Union[str, Message, MessageSegment]
        :param at_sender: 是否 @ 事件主体
        :type at_sender: bool, optional
        :param reply_message: 是否回复事件
        :type reply_message: bool, optional
        :param message_type: 指定消息发送类型
        :type message_type: Optional[Literal[&#39;private&#39;, &#39;group&#39;]], optional
        :param target_id: 指定消息发送目标
        :type target_id: Optional[int], optional
        :raises ValueError: 不合法的目标 ID
        :raises ValueError: 不合法的消息 ID
        :raises TypeError: 无法指定消息发送对象
        :raises TypeError: 错误的消息类型指定
        :raises TypeError: 错误的消息类型指定
        :return: 消息 ID
        :rtype: int
        '''
        # 预处理消息
        if at_sender: # @ 事件主体为前置 @
            at_id = getattr(event, 'user_id', target_id)
            if not isinstance(at_id, int):
                raise ValueError('不合法的目标 ID')
            if isinstance(message, str):
                message = Message(message)
            message = MessageSegment.at(at_id) + message
        if reply_message: # 回复事件为前置回复
            reply_id = getattr(event, 'message_id', None)
            if not isinstance(reply_id, int):
                raise ValueError('不合法的消息 ID')
            if isinstance(message, str):
                message = Message(message)
            message = MessageSegment.reply(reply_id) + message
            
        if message_type is None: # 如果没有指定消息类型
            # 如果是群聊消息
            if (
                hasattr(event, 'group_id') and
                (group_id := getattr(event, 'group_id')) is not None
            ):
                # 如果有 group_id 字段且字段值不为 None
                message_id = self.adapter.send_msg(
                    'group',
                    group_id,
                    message
                )
                return message_id
            else: # 是私聊消息
                if (
                    hasattr(event, 'user_id') and
                    (user_id := getattr(event, 'user_id')) is not None
                ):
                    # 如果有 user_id 字段且字段值不为 None
                    message_id = self.adapter.send_msg(
                        'private',
                        user_id,
                        message
                    )
                    return message_id
                else:
                    raise TypeError('无法指定消息发送对象')
        else: # 指定了消息类型
            if target_id is not None: # 指定了目标 ID
                message_id = self.adapter.send_msg(
                    message_type,
                    target_id,
                    message
                )
                return message_id
            else: # 没有指定目标 ID
                if message_type == 'group':
                    if (
                        hasattr(event, 'group_id') and
                        (group_id := getattr(event, 'group_id')) is not None
                    ):
                        # 如果有 group_id 字段且字段值不为 None
                        message_id = self.adapter.send_msg(
                            'group',
                            group_id,
                            message
                        )
                        return message_id
                    else:
                        raise TypeError('错误的消息类型指定')
                elif message_type == 'private':
                    if (
                        hasattr(event, 'user_id') and
                        (user_id := getattr(event, 'user_id')) is not None
                    ):
                        # 如果有 user_id 字段且字段值不为 None
                        message_id = self.adapter.send_msg(
                            'private',
                            user_id,
                            message
                        )
                        return message_id
                    else:
                        raise TypeError('错误的消息类型指定')
    
    # 管理员操作类
    class Admin:
        '''管理员操作类'''
        # 创建一个管理员操作类
        def __init__(self, host_id: int) -> None:
            '''管理员操作类

            :param host_id: 主人 ID
            :type host_id: int
            '''
            self.host_id = host_id
            '''适配器对象'''
            
        # 获取管理员列表
        @classmethod
        def get_list(cls) -> list[int]:
            '''获取管理员列表

            :return: 管理员 ID 列表
            :rtype: list[int]
            '''
            # 获取 Bot 信息
            bot_info = MyJson.read_to_dict(CURRENT_DIR + '/resources/bot_info.json')
            # 检测并获取管理员列表
            if bot_info.get('admin_list') is None: # 管理员列表未被记录
                bot_info['admin_list'] = []
                MyJson.write(CURRENT_DIR + '/resources/bot_info.json', bot_info)
                return []
            else:
                return bot_info['admin_list']
            
        # 保存管理员列表
        @staticmethod
        def admin_list_save(admin_list: list) -> None:
            '''保存管理员列表

            :param admin_list: 将要保存的管理员列表
            :type admin_list: list
            '''
            # 获取 bot 信息
            bot_info = MyJson.read_to_dict(CURRENT_DIR + '/resources/bot_info.json')
            # 保存列表
            bot_info['admin_list'] = admin_list
            try:
                MyJson.write(CURRENT_DIR + '/resources/bot_info.json', bot_info)
            except Exception as exception:
                print(f'保存管理员列表时出现错误：{exception}')
                raise exception
            
        # 检测是否为管理员
        def is_admin(self, user_id: int) -> bool:
            '''检测是否为管理员

            :param user_id: 要检测的 ID
            :type user_id: int
            :return: 是否为管理员
            :rtype: bool
            '''
            # 如果是 HOST_ID 直接返回 True
            if user_id ==  self.host_id:
                return True
            
            # 获取管理员列表
            admin_list = self.get_list()
            #判断是否在列表里面
            return user_id in admin_list
        
        # 添加管理员
        def add(self, user_id: int) -> Literal['Already Admin', 'Add Successfully']:
            '''添加管理员

            :param user_id: 要添加的 ID
            :type user_id: int
            :raises exception: 添加状况
            :return: _description_
            :rtype: str
            '''
            # 判断是否已是管理员
            if self.is_admin(user_id):
                return 'Already Admin'
            else:
                # 添加管理员并保存
                admin_list = self.get_list()
                admin_list.append(user_id)
                try:
                    self.admin_list_save(admin_list)
                    return 'Add Successfully'
                except Exception as exception:
                    raise exception
                
        # 移除管理员
        def remove(self, user_id: int) -> Literal['Not Admin', 'Remove Successfully']:
            '''移除管理员

            :param user_id: 要移除的 ID
            :type user_id: int
            :return: 移除状况
            :rtype: str
            '''
            # 判断是否已是管理员
            if not self.is_admin(user_id):
                return 'Not Admin'
            else:
                # 删除管理员并保存
                admin_list = self.get_list()
                admin_list.remove(user_id)
                try:
                    self.admin_list_save(admin_list)
                    return 'Remove Successfully'
                except Exception as exception:
                    raise exception

    # 黑名单操作类
    class BlockList:
        '''黑名单操作类'''
        # 获取黑名单
        @staticmethod
        def get_list(group_id: int) -> list[str]:
            '''获取黑名单

            :param group_id: 群号
            :type group_id: int
            :return: 黑名单列表
            :rtype: list[str]
            '''
            # 获取 Bot 信息
            bot_info = MyJson.read_to_dict(CURRENT_DIR + '/resources/bot_info.json')
            # 检测并获取黑名单列表
            if bot_info.get('group_block_list') is None: # 没有黑名单被记录
                bot_info['group_block_list'] = {}
                bot_info['group_block_list'][str(group_id)] = []
                MyJson.write(CURRENT_DIR + '/resources/bot_info.json', bot_info)
                return []
            else:
                if bot_info['group_block_list'].get(str(group_id)) is None: # 该群没有黑名单被记录
                    bot_info['group_block_list'][str(group_id)] = []
                    MyJson.write(CURRENT_DIR + '/resources/bot_info.json', bot_info)
                    return []
                else:
                    return bot_info['group_block_list'][str(group_id)]
            
        # 保存黑名单列表
        @staticmethod
        def block_list_save(block_list: list[str], group_id: int) -> None:
            '''_summary_

            :param block_list: 将要保存的黑名单列表
            :type block_list: list[str]
            :param group_id: 将要保存的群号
            :type group_id: int
            '''
            # 获取 bot 信息
            bot_info = MyJson.read_to_dict(CURRENT_DIR + '/resources/bot_info.json')
            # 保存列表
            bot_info['group_block_list'][str(group_id)] = block_list
            try:
                MyJson.write(CURRENT_DIR + '/resources/bot_info.json', bot_info)
            except Exception as exception:
                print(f'保存管理员列表时出现错误：{exception}')
                raise exception
            
        # 检测是否被屏蔽
        @classmethod
        def is_blocked(cls, group_id: int, plugin_name: str) -> bool:
            '''检测是否被屏蔽

            :param group_id: 要检测的群号
            :type group_id: int
            :param plugin_name: 要检测的插件名
            :type plugin_name: str
            :return: 是否被屏蔽
            :rtype: bool
            '''
            # 获取黑名单列表
            block_list = cls.get_list(group_id)
            #判断是否在列表里面
            return plugin_name in block_list
        
        # 屏蔽插件
        @classmethod
        def block(
            cls,
            group_id: int,
            plugin_name: str
        ) -> Literal['Already Blocked', 'Block Successfully']:
            '''屏蔽插件

            :param group_id: 要进行屏蔽的群号
            :type group_id: int
            :param plugin_name: 要被屏蔽的插件
            :type plugin_name: str
            :return: 处理结果
            :rtype: str
            '''
            # 判断是否已被屏蔽
            if cls.is_blocked(group_id, plugin_name):
                return 'Already Blocked'
            else:
                # 加入黑名单并保存
                block_list = cls.get_list(group_id)
                block_list.append(plugin_name)
                try:
                    cls.block_list_save(block_list, group_id)
                    return 'Block Successfully'
                except Exception as exception:
                    raise exception
                
        # 取消屏蔽插件
        @classmethod
        def allow(
            cls,
            group_id: int,
            plugin_name: str
        ) -> Literal['Not Blocked', 'Allow Successfully']:
            '''取消屏蔽插件

            :param group_id: 要进行处理的群号
            :type group_id: int
            :param plugin_name: 要被取消屏蔽的插件
            :type plugin_name: str
            :return: 处理结果
            :rtype: str
            '''
            # 判断是否已被屏蔽
            if not cls.is_blocked(group_id, plugin_name):
                return 'Not Blocked'
            else:
                # 移出黑名单并保存
                block_list = cls.get_list(group_id)
                block_list.remove(plugin_name)
                try:
                    cls.block_list_save(block_list, group_id)
                    return 'Allow Successfully'
                except Exception as exception:
                    raise exception
