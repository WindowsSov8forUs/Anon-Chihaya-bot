'''Go-cqhttp 事件模型。
WindowsSov8 Anon Bot 自用 Adapter
'''
# -*- coding: utf-8 -*-
# !/usr/bin/python3
from pydantic import BaseModel
from typing import Optional, Literal

from .message import Message

# 所有事件上报的基类
class Event(BaseModel):
    '''所有事件上报的基类'''
    time: int
    '''事件发生的unix时间戳'''
    self_id: int
    '''收到事件的机器人的 QQ 号'''
    post_type: Literal[
        'message', # 消息, 例如, 群聊消息
        'message_sent', # 消息发送，例如，bot发送在群里的消息
        'request', # 请求, 例如, 好友申请
        'notice', # 通知, 例如, 群成员增加
        'meta_event' # 元事件, 例如, go-cqhttp 心跳包
    ]
    '''表示该上报的类型, 消息, 消息发送, 请求, 通知, 或元事件'''
    
# 消息上报的基类
class MessageEvent(Event):
    '''消息上报的基类'''
    message_type: Literal[
        'private', # 私聊消息
        'group' # 群消息
    ]
    '''消息类型'''
    sub_type: Literal[
        'friend', # 好友
        'normal', # 群聊
        'anonymous', # 匿名
        'group_self', # 群中自身发送
        'group', # 群临时会话
        'notice' # 系统提示
    ]
    '''表示消息的子类型'''
    message_id: int
    '''消息 ID'''
    user_id: int
    '''发送者 QQ 号'''
    message: Message
    '''一个消息链'''
    raw_message: str
    '''CQ 码格式的消息'''
    font: int = 0
    '''字体'''
    sender: 'Sender'
    '''发送者信息'''
    
    # 表示消息发送者的信息
    class Sender(BaseModel):
        '''表示消息发送者的信息'''
        # 以下是必定存在的信息
        user_id: int
        '''发送者 QQ 号'''
        nickname: str
        '''昵称'''
        sex: Literal[
            'male',
            'female',
            'unknown'
        ]
        '''性别, `male` 或 `female` 或 `unknown`'''
        age: int
        '''年龄'''
        
        # 当私聊类型为群临时会话时的额外字段
        group_id: Optional[int] = None
        '''临时群消息来源群号'''
        
        # 如果是群聊
        card: Optional[str] = None
        '''群名片／备注'''
        area: Optional[str] = None
        '''地区'''
        level: Optional[str] = None
        '''成员等级'''
        role: Optional[
            Literal[
                'owner',
                'admin',
                'member'
            ]
        ] = None
        '''角色, `owner` 或 `admin` 或 `member`'''
        title: Optional[str] = None
        '''专属头衔'''
        
        # 判断是否拥有管理权限
        @property
        def is_admin(self) -> bool:
            '''是否拥有管理权限'''
            return any((self.role == 'admin', self.role == 'owner'))
    
    # 重定义转换字符串方法
    def __str__(self) -> str:
        '''重定义转换字符串方法'''
        message_string = ''
        if self.message_type == 'group': # 群消息
            message_string += f'[{self.sender.role}]'
            if self.sender.title != '': # 如果有头衔
                message_string += f'[{self.sender.title}]'
            if self.sender.card != '': # 如果有群昵称
                message_string += f'{self.sender.card}({self.sender.nickname})'
            else:
                message_string += self.sender.nickname
            message_string += '(来自群组{})'.format(getattr(self, 'group_id', None))
        else: # 私聊消息
            message_string += f'[{self.sub_type}]{self.sender.nickname}'
        message_string += f'({self.user_id}): {self.raw_message}'
        
        return message_string
    
    # 定义配置
    class Config:
        arbitrary_types_allowed = True
    
# 请求上报的基类
class RequestEvent(Event):
    '''请求上报的基类'''
    request_type: Literal[
        'friend', # 好友请求
        'group' # 群请求
    ]
    '''请求类型'''
    
# 通知上报的基类
class NoticeEvent(Event):
    '''通知上报的基类'''
    notice_type: Literal[
        'group_upload', # 群文件上传
        'group_admin', # 群管理员变更
        'group_decrease', # 群成员减少
        'group_increase', # 群成员增加
        'group_ban', # 群成员禁言
        'friend_add', # 好友添加
        'group_recall', # 群消息撤回
        'friend_recall', # 好友消息撤回
        'group_card', # 群名片变更
        'offline_file', # 离线文件上传
        'client_status', # 客户端状态变更
        'essence', # 精华消息
        'notify' # 系统通知
    ]
    '''通知类型'''
    
# 元事件上报的基类
class MetaEvent(Event):
    '''元事件上报的基类'''
    meta_event_type: Literal[
        'lifecycle', # 生命周期
        'heartbeat' # 心跳包
    ]
    '''元事件类型'''
    
# 私聊消息
class PrivateMessageEvent(MessageEvent):
    '''私聊消息'''
    target_id: int
    '''接收者 QQ 号'''
    temp_source: Optional[int] = None
    '''临时会话来源'''
    
# 群消息
class GroupMessageEvent(MessageEvent):
    '''群消息'''
    group_id: int
    '''群号'''
    anonymous: Optional['Anonymous']
    '''匿名信息, 如果不是匿名消息则为 null'''
    
    # 匿名信息
    class Anonymous(BaseModel):
        '''匿名信息'''
        id: int
        '''匿名用户 ID'''
        name: str
        '''匿名用户名称'''
        flag: str
        '''匿名用户 flag, 在调用禁言 API 时需要传入'''
    
# 私聊消息撤回
class FriendRecallEvent(NoticeEvent):
    '''私聊消息撤回'''
    user_id: int
    '''好友 QQ 号'''
    message_id: int
    '''被撤回的消息 ID'''
    
# 群消息撤回
class GroupRecallEvent(NoticeEvent):
    '''群消息撤回'''
    group_id: int
    '''群号'''
    user_id: int
    '''消息发送者 QQ 号'''
    operator_id: int
    '''操作者 QQ 号'''
    message_id: int
    '''被撤回的消息 ID'''
    
# 群成员增加
class GroupIncreaseEvent(NoticeEvent):
    '''群成员增加'''
    sub_type: Literal[
        'approve',
        'invite'
    ]
    '''事件子类型, 分别表示管理员已同意入群、管理员邀请入群'''
    group_id: int
    '''群号'''
    operator_id: int
    '''操作者 QQ 号'''
    user_id: int
    '''加入者 QQ 号'''
    
# 群成员减少
class GroupDecreaseEvent(NoticeEvent):
    '''群成员减少'''
    sub_type: Literal[
        'leave',
        'kick',
        'kick_me'
    ]
    '''事件子类型, 分别表示主动退群、成员被踢、登录号被踢'''
    group_id: int
    '''群号'''
    operator_id: int
    '''操作者 QQ 号 ( 如果是主动退群, 则和 `user_id` 相同 )'''
    user_id: int
    '''离开者 QQ 号'''
    
# 群管理员变动
class GroupAdminEvent(NoticeEvent):
    '''群管理员变动'''
    sub_type: Literal[
        'set',
        'unset'
    ]
    '''事件子类型, 分别表示设置和取消管理员'''
    group_id: int
    '''群号'''
    user_id: int
    '''管理员 QQ 号'''
    
# 群文件上传
class GroupUploadEvent(NoticeEvent):
    '''群文件上传'''
    group_id: int
    '''群号'''
    user_id: int
    '''发送者 QQ 号'''
    file: 'File'
    '''文件信息'''
    
    # 文件信息
    class File(BaseModel):
        '''文件信息'''
        id: str
        '''文件 ID'''
        name: str
        '''文件名'''
        size: int
        '''文件大小 ( 字节数 )'''
        busid: int
        '''busid ( 目前不清楚有什么作用 )'''
        
# 群禁言
class GroupBanEvent(NoticeEvent):
    '''群禁言'''
    sub_type: Literal[
        'ban',
        'lift_ban'
    ]
    '''事件子类型, 分别表示禁言、解除禁言'''
    group_id: int
    '''群号'''
    operator_id: int
    '''操作者 QQ 号'''
    user_id: int
    '''被禁言 QQ 号 (为全员禁言时为`0`)'''
    duration: int
    '''禁言时长, 单位秒 (为全员禁言时为`-1`)'''
    
# 好友添加
class FriendAddEvent(NoticeEvent):
    '''好友添加'''
    user_id: int
    '''新添加好友 QQ 号'''
    
# 系统通知上报
class NotifyEvent(NoticeEvent):
    '''系统通知上报'''
    sub_type: Literal[
        'poke'
    ]
    '''提示类型'''
    
# 戳一戳（双击头像）
class PokeEvent(NotifyEvent):
    '''戳一戳（双击头像）'''
    sender_id: Optional[int]
    '''发送者 QQ 号'''
    group_id: Optional[int]
    '''群号'''
    user_id: int
    '''发送者 QQ 号'''
    target_id: int
    '''被戳者 QQ 号'''
    
# 接收到离线文件
class OfflineFileEvent(NoticeEvent):
    '''接收到离线文件'''
    user_id: int
    '''发送者id'''
    file: 'File'
    '''文件数据'''
    
    # 文件数据
    class File(BaseModel):
        '''文件数据'''
        name: str
        '''文件名'''
        size: int
        '''文件大小'''
        url: str
        '''下载链接'''
        
# 加好友请求
class FriendRequestEvent(RequestEvent):
    '''加好友请求'''
    user_id: int
    '''发送请求的 QQ 号'''
    comment: str
    '''验证信息'''
    flag: str
    '''请求 flag, 在调用处理请求的 API 时需要传入'''
    
# 加群请求/邀请
class GroupRequestEvent(RequestEvent):
    '''加群请求/邀请'''
    sub_type: Literal[
        'add',
        'invite'
    ]
    '''请求子类型, 分别表示加群请求、邀请登录号入群'''
    group_id: int
    '''群号'''
    user_id: int
    '''发送请求的 QQ 号'''
    comment: str
    '''验证信息'''
    flag: str
    '''请求 flag, 在调用处理请求的 API 时需要传入'''
    
# 心跳包
class HeartbeatEvent(MetaEvent):
    '''心跳包'''
    status: 'Status'
    '''应用程序状态'''
    interval: int
    '''距离上一次心跳包的时间(单位是毫秒)'''
    
    # 应用程序状态
    class Status(BaseModel):
        '''应用程序状态'''
        app_initialized: bool
        '''程序是否初始化完毕'''
        app_enabled: bool
        '''程序是否可用'''
        plugins_good: Optional[bool]=None
        '''插件正常(可能为 null)'''
        app_good: bool
        '''程序正常'''
        online: bool
        '''是否在线'''
        stat: 'StatusStatistics'
        '''统计信息'''
        
        # 统计信息
        class StatusStatistics(BaseModel):
            '''统计信息'''
            packet_received: int
            '''收包数'''
            packet_sent: int
            '''发包数'''
            packet_lost: int
            '''丢包数'''
            message_received: int
            '''消息接收数'''
            message_sent: int
            '''消息发送数'''
            disconnect_times: int
            '''连接断开次数'''
            lost_times: int
            '''连接丢失次数'''
            last_message_time: int
            '''最后一次消息时间'''
            
# 生命周期
class LifecycleEvent(MetaEvent):
    '''生命周期'''
    sub_type: Literal[
        'enable', # 启用
        'disable', # 禁用
        'connect' # 连接
    ]
    '''子类型'''
