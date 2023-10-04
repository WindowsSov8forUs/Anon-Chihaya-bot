'''Go-cqhttp 适配器。
WindowsSov8 Anon Bot 自用 Adapter
'''
# -*- coding: utf-8 -*-
# !/usr/bin/python3
import json
import time
import requests
from pydantic import BaseModel
from typing import Optional, Union, Literal, Any

from . import event
from .utils import Logging
from .message import Message, MessageSegment

# 获取到的消息对象
class MsgGet(BaseModel):
    '''通过 `/get_msg` 终结点获取到的消息对象'''
    group: bool
    '''是否是群消息'''
    group_id: Optional[int]=None
    '''是群消息时的群号(否则不存在此字段)'''
    message_id: int
    '''消息id'''
    real_id: int
    '''消息真实id'''
    message_type: Literal['group', 'private']
    '''群消息时为 `group`, 私聊消息为 `private`'''
    sender: 'Sender'
    '''发送者'''
    time: int
    '''发送时间'''
    message: Message
    '''消息内容'''
    raw_message: str
    '''原始消息内容'''
    
    # 定义配置
    class Config:
        arbitrary_types_allowed = True
    
    # 发送者
    class Sender(BaseModel):
        '''发送者'''
        nickname: str
        '''发送者昵称'''
        user_id: int
        '''	发送者 QQ 号'''
    
    # 重定义转换字符串方法
    def __str__(self) -> str:
        '''重定义转换字符串方法'''
        message_string = '获取到的消息: [{}]'.format(time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(self.time)))
        if self.group: # 是群消息
            message_string += '(GROUP)[{}]'.format(self.group_id)
        else: # 是私聊消息
            message_string += '(PRIVATE)'
        message_string += '{}({}): '.format(self.sender.nickname, self.sender.user_id)
        message_string += str(self.message)
        return message_string

# 获取到的陌生人信息
class StrangerInfo(BaseModel):
    '''通过 `/get_stranger_info` 终结点获取到的陌生人信息'''
    user_id: int
    '''QQ 号'''
    nickname: str
    '''昵称'''
    sex: Literal['male', 'female', 'unknown']
    '''性别, `male` 或 `female` 或 `unknown`'''
    age: int
    '''年龄'''
    qid: str
    '''qid ID身份卡'''
    level: int
    '''等级'''
    login_days: int
    '''登录天数'''

# 获取到的群成员信息
class GroupMemberInfo(BaseModel):
    '''通过 `/get_group_member_info` 终结点获取到的群成员信息'''
    group_id: int
    '''群号'''
    user_id: int
    '''QQ 号'''
    nickname: str
    '''昵称'''
    card: str
    '''群名片／备注'''
    sex: Literal['male', 'female', 'unknown']
    '''性别, `male` 或 `female` 或 `unknown`'''
    age: int
    '''年龄'''
    area: str
    '''地区'''
    join_time: int
    '''加群时间戳'''
    last_sent_time: int
    '''最后发言时间戳'''
    level: str
    '''成员等级'''
    role: Literal['owner', 'admin', 'member']
    '''角色, `owner` 或 `admin` 或 `member`'''
    unfriendly: bool
    '''是否不良记录成员'''
    title: str
    '''专属头衔'''
    title_expire_time: int
    '''专属头衔过期时间戳'''
    card_changeable: bool
    '''是否允许修改群名片'''
    shut_up_timestamp: int
    '''禁言到期时间'''
    
    # 判断是否拥有管理权限
    @property
    def is_admin(self) -> bool:
        '''是否拥有管理权限'''
        return any((self.role == 'admin', self.role == 'owner'))

# 适配器对象
class Adapter(BaseModel):
    '''适配器对象'''
    port_send: int
    '''监听端口'''
    http_url: Optional[str]='http://127.0.0.1'
    '''监听地址，默认为本地'''
    
    # 上报数据转事件
    @staticmethod
    def data_to_event(data: dict[str, Any]) -> Optional[event.Event]:
        '''上报数据转事件

        :param data: 接收到的上报数据
        :type data: dict[str, Any]
        :return: 事件对象
        :rtype: Optional[Event]
        '''
        # 匹配上报数据的 post_type
        match data['post_type']:
            case 'message'|'message_sent': # 消息上报
                data['message'] = Message(data['message'])
                match data['message_type']:
                    case 'private': # 私聊消息
                        return event.PrivateMessageEvent.model_validate(data)
                    case 'group': # 群消息
                        return event.GroupMessageEvent.model_validate(data)
                    case _: # 其他不支持的消息类型
                        raise TypeError('不支持的消息类型：{}'.format(data['message_type']))
            
            case 'request': # 请求上报
                match data['request_type']:
                    case 'friend': # 好友请求
                        return event.FriendRequestEvent.model_validate(data)
                    case 'group': # 群请求
                        return event.GroupRequestEvent.model_validate(data)
                    case _: # 其他不支持的请求类型
                        raise TypeError('不支持的请求类型：{}'.format(data['request_type']))
                    
            case 'notice': # 通知上报
                match data['notice_type']:
                    case 'group_upload': # 群文件上传
                        return event.GroupUploadEvent.model_validate(data)
                    case 'group_admin': # 群管理员变更
                        return event.GroupAdminEvent.model_validate(data)
                    case 'group_decrease': # 群成员减少
                        return event.GroupDecreaseEvent.model_validate(data)
                    case 'group_increase': # 群成员增加
                        return event.GroupIncreaseEvent.model_validate(data)
                    case 'group_ban': # 群成员禁言
                        return event.GroupBanEvent.model_validate(data)
                    case 'friend_add': # 好友添加
                        return event.FriendAddEvent.model_validate(data)
                    case 'group_recall': # 群消息撤回
                        return event.GroupRecallEvent.model_validate(data)
                    case 'friend_recall': # 好友消息撤回
                        return event.FriendRecallEvent.model_validate(data)
                    case 'offline_file': # 离线文件上传
                        return event.OfflineFileEvent.model_validate(data)
                    case 'notify': # 系统通知上报
                        match data['sub_type']:
                            case 'poke': # 戳一戳
                                return event.PokeEvent.model_validate(data)
                            case _: # 其他不支持的系统通知类型
                                raise TypeError('不支持的系统通知类型：{}'.format(data['sub_type']))
                    case _: # 其他不支持的通知类型
                        raise TypeError('不支持的通知类型：{}'.format(data['notice_type']))
            
            case 'meta_event': # 元事件上报
                match data['meta_event_type']:
                    case 'lifecycle': # 生命周期
                        return event.LifecycleEvent.model_validate(data)
                    case 'heartbeat': # 心跳包
                        return event.HeartbeatEvent.model_validate(data)
                    case _: # 其他不支持的元事件类型
                        raise TypeError('不支持的元事件类型：{}'.format(data['meta_event_type']))
                    
            case _: # 其他不支持的上报类型
                raise TypeError('不支持的上报类型：{}'.format(data['post_type']))
    
    # go-cqhttp API
    # Bot 账号 API
    
    # 设置登录号资料
    def set_qq_profile(self, profile: dict[str, Any]) -> None:
        '''设置登录号资料

        :param profile: 要设置的资料字典
        :type profile: dict[str, Any]
        '''
        url = f'{self.http_url}:{self.port_send}/set_qq_profile' # 请求发送URL
        response = requests.post(url, data=profile) # 获取返回值
        if response.status_code == 200: # 设置请求发送成功
            print_stat = f'设置请求发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'设置请求发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        
    # 好友信息 API
    
    # 获取陌生人信息
    def get_stranger_info(self, user_id: int) -> StrangerInfo:
        '''获取陌生人信息

        :param user_id: QQ 号
        :type user_id: int
        :return: 获取到的陌生人信息
        :rtype: StrangerInfo
        '''
        url = f'{self.http_url}:{self.port_send}/get_stranger_info' # 请求发送URL
        
        response = requests.post(url, data={'user_id': user_id}) # 获取返回值
        if response.status_code == 200: # 陌生人信息获取成功
            print_stat = f'陌生人信息获取成功，返回码：{response.status_code}'
        else:
            print_stat = f'陌生人信息获取失败，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        data = response.json()['data']
        
        return StrangerInfo.model_validate(data)
    
    # 消息 API
    
    # 发送消息
    def send_msg(
        self,
        message_type: Literal['private', 'group'],
        id_: int,
        message: Union[str, Message, MessageSegment]
    ) -> int:
        '''发送消息

        :param message_type: 消息类型, 支持 `private` 、 `group` ，分别对应私聊、群组
        :type message_type: Literal['private', 'group']
        :param id_: 对方 QQ 号 ( 消息类型为 `private` 时需要 ) 或群号 ( 消息类型为 `group` 时需要 )
        :type user_id: int
        :param message: 要发送的内容
        :type message: Union[str, Message, MessageSegment]
        :return: 消息 ID
        :rtype: dict
        '''
        url = f'{self.http_url}:{self.port_send}/send_msg' # 消息发送URL
        
        # 将 message 转换为 Message 对象
        if isinstance(message, str):
            message = MessageSegment.text(message)
        if isinstance(message, MessageSegment):
            message = Message(message)
            
        if message_type == 'group': # 发送的为群聊消息
            data = {
                'message_type': message_type,
                'group_id': id_,
                'message': json.dumps(message.__list__)
            }
        elif message_type == 'private': # 发送的为私聊消息
            data = {
                'message_type': message_type,
                'user_id': id_,
                'message': json.dumps(message.__list__)
            }
        else:
            raise TypeError(f'不合法的消息类型：{message_type}')
        
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 消息发送成功
            print_stat = f'消息发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'消息发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        
        return response.json()['data']['message_id']
        
    # 获取消息
    def get_msg(self, message_id: int) -> MsgGet:
        '''获取消息

        :param message_id: 消息id
        :type message_id: int
        :return: 获取到的消息对象
        :rtype: MsgGet
        '''
        url = f'{self.http_url}:{self.port_send}/get_msg' # 请求发送URL
        
        response = requests.post(url, data={'message_id': message_id}) # 获取返回值
        if response.status_code == 200: # 文件获取成功
            print_stat = f'消息获取成功，返回码：{response.status_code}'
        else:
            print_stat = f'消息获取成功，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        data = response.json()['data']
        message = MsgGet.model_validate(data)
        Logging.info(str(message))
        
        return message

    # 撤回消息
    def delete_msg(self, message_id: int) -> None:
        '''撤回消息

        :param message_id: 消息 ID
        :type message_id: int
        '''
        url = f'{self.http_url}:{self.port_send}/delete_msg' # 请求发送URL
        
        response = requests.post(url, data={'message_id': message_id}) # 获取返回值
        if response.status_code == 200: # 消息撤回成功
            print_stat = f'消息撤回成功，返回码：{response.status_code}'
        else:
            print_stat = f'消息撤回失败，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        
        return
    
    # 发送合并转发
    def send_forward_msg(
        self,
        message_type: Literal['private', 'group'],
        id_: int,
        messages: Message
    ) -> tuple[int, str]:
        '''发送合并转发

        :param message_type: 消息类型, 支持 `private` 、 `group` , 分别对应私聊、群组
        :type message_type: Literal[&#39;private&#39;, &#39;group&#39;]
        :param id_: 好友 QQ 号或群号
        :type id_: int
        :param messages: 自定义转发消息
        :type messages: Message
        :raises TypeError: 发送消息有误
        :return: 响应数据: Tuple[消息 ID, 转发消息 ID]
        :rtype: tuple[int, str]
        '''
        # 判断内容是否为合并转发
        if not messages.is_forward():
            raise TypeError('不是合并转发消息')
        # 判断群聊转发或好友转发
        data = {}
        if message_type == 'group':
            data['group_id'] = id_
            url = f'{self.http_url}:{self.port_send}/send_group_forward_msg' # 消息发送URL
        elif message_type == 'private':
            data['user_id'] = id_
            url = f'{self.http_url}:{self.port_send}/send_private_forward_msg' # 消息发送URL
        
        data['messages'] = json.dumps(messages)
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 消息发送成功
            print_stat = f'消息发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'消息发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        data = response.json()['data']
        
        return data['message_id'], data['forward_id']

    # 处理 API
    
    # 处理加好友请求
    def set_friend_add_request(self, flag: str, approve: bool=True) -> None:
        '''加好友请求处理

        :param flag: 加好友请求的 flag（需从上报的数据中获得）
        :type flag: str
        :param approve: 是否同意请求，默认为 True
        :type approve: bool, optional
        '''   
        url = f'{self.http_url}:{self.port_send}/set_friend_add_request' # 请求发送URL
        
        data = {'flag': flag, 'approve': approve} # 请求发送参数
        response = requests.post(url, data=data) # 发送请求
        if response.status_code == 200: # 请求处理成功
            print_stat = f'请求处理成功，返回码：{response.status_code}'
        else:
            print_stat = f'请求处理错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 处理加群请求 / 邀请
    def set_group_add_request(
        self,
        flag: str,
        sub_type: str,
        approve: bool=True,
        reason: str=''
    ) -> None:
        '''处理加群请求 / 邀请

        :param flag: 加群请求的 flag（需从上报的数据中获得）
        :type flag: str
        :param sub_type: `add` 或 `invite`, 请求类型（需要和上报消息中的 `sub_type` 字段相符）
        :type sub_type: str
        :param approve: 是否同意请求/邀请默认为 True
        :type approve: bool, optional
        :param reason: 拒绝理由（仅在拒绝时有效），默认为空
        :type reason: str, optional
        '''      
        url = f'{self.http_url}:{self.port_send}/set_group_add_request' # 请求发送URL
        
        data = {'flag': flag, 'sub_type': sub_type, 'approve': approve} # 请求发送参数
        if not approve: # 如果拒绝
            data['reason'] = reason
        response = requests.post(url, data=data) # 发送请求
        if response.status_code == 200: # 请求处理成功
            print_stat = f'请求处理成功，返回码：{response.status_code}'
        else:
            print_stat = f'请求处理错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 群信息 API
    
    # 获取群成员信息
    def get_group_member_info(
        self,
        group_id: int,
        user_id: int
    ) -> GroupMemberInfo:
        '''_summary_

        :param group_id: 群号
        :type group_id: int
        :param user_id: QQ 号
        :type user_id: int
        :return: 获取到的群成员信息
        :rtype: GroupMemberInfo
        '''
        url = f'{self.http_url}:{self.port_send}/get_group_member_info' # 请求发送URL
        data = {'group_id': group_id, 'user_id': user_id, 'no_cache': True}
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 信息获取成功
            print_stat = f'群成员{user_id}信息获取成功，返回码：{response.status_code}'
        else:
            print_stat = f'群成员{user_id}信息获取错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
        
        return GroupMemberInfo.model_validate(response.json()['data'])

    # 群设置 API
    
    # 设置群名
    def set_group_name(self, group_id: int, group_name: str) -> None:
        '''设置群名

        :param group_id: 群号
        :type group_id: int
        :param group_name: 新群名
        :type group_name: str
        '''     
        url = f'{self.http_url}:{self.port_send}/set_group_name' # 请求发送URL
        data = {'group_id': group_id, 'group_name': group_name}
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 设置请求发送成功
            print_stat = f'群{group_id}设置群名为{group_name}请求发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'群{group_id}设置群名为{group_name}请求发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 设置群名片（群备注）
    def set_group_card(
        self,
        group_id: int,
        user_id: int,
        card: str=''
    ) -> None:
        '''设置群名片(群备注)

        :param group_id: 群号
        :type group_id: int
        :param user_id: 要设置的 QQ 号
        :type user_id: int
        :param card: 群名片内容, 不填或空字符串表示删除群名片，默认为空
        :type card: str, optional
        '''
        url = f'{self.http_url}:{self.port_send}/set_group_card' # 请求发送URL
        data = {'group_id': group_id, 'user_id': user_id, 'card': card}
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 设置请求发送成功
            print_stat = f'{user_id}群名片设置为{card}请求发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'{user_id}群名片设置为{card}请求发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 群操作 API
    
    # 群单人禁言
    def set_group_ban(
        self,
        group_id: int,
        user_id: int,
        duration: int=1800
    ) -> None:
        '''群单人禁言

        :param group_id: 群号
        :type group_id: int
        :param user_id: 要禁言的 QQ 号
        :type user_id: int
        :param duration: 禁言时长，单位秒，0 表示取消禁言，默认为1800秒（30小时）
        :type duration: int, optional
        '''
        url = f'{self.http_url}:{self.port_send}/set_group_ban' # 请求发送URL
        data = {'group_id': group_id, 'user_id': user_id, 'duration': abs(duration)}
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 设置请求发送成功
            print_stat = f'禁言{user_id}请求发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'禁言{user_id}请求发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 群组踢人
    def set_group_kick(
        self,
        group_id: int,
        user_id: int,
        reject_add_request: bool=False
    ) -> None:
        '''群组踢人

        :param group_id: 群号
        :type group_id: int
        :param user_id: 要踢的 QQ 号
        :type user_id: int
        :param reject_add_request: 拒绝此人的加群请求，默认为 False
        :type reject_add_request: bool, optional
        '''
        url = f'{self.http_url}:{self.port_send}/set_group_kick' # 请求发送URL
        data = {'group_id': group_id, 'user_id': user_id, 'reject_add_request': reject_add_request}
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 设置请求发送成功
            print_stat = f'将 {user_id} 踢出 {group_id} 请求发送成功，返回码：{response.status_code}'
        else:
            print_stat = f'将 {user_id} 踢出 {group_id} 请求发送错误，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)

    # 文件 API
    
    # 上传群 / 私聊文件
    def upload_file(
        self,
        upload_type: Literal['private', 'group'],
        id_: int,
        file: str,
        name: str,
        folder: Optional[str] = None
    ) -> None:
        '''上传群 / 私聊文件

        :param upload_type: 上传类型
        :type upload_type: Literal['private', 'group']
        :param id_: 群号 / 对方 QQ 号
        :type id_: int
        :param file: 本地文件路径
        :type file: str
        :param name: 储存名称
        :type name: str
        :param folder: 父目录ID，只在上传群文件时使用，不提供 `folder` 参数的情况下默认上传到根目录
        :type folder: str, optional
        '''
        data: dict[str, Union[str, int]] = {
            'file': file,
            'name': name
        }
        url = f'{self.http_url}:{self.port_send}/upload_{upload_type}_file' # 请求发送URL
        # 判断群文件或私聊文件
        if upload_type == 'group':
            data['group_id'] = id_
            if not folder is None:
                data['folder'] = folder
        elif upload_type == 'private':
            data['user_id'] = id_
        
        response = requests.post(url, data=data) # 获取返回值
        if response.status_code == 200: # 文件上传成功
            print_stat = f'文件上传成功，返回码：{response.status_code}'
        else:
            print_stat = f'文件上传成功，返回码：{response.status_code}'
        print(print_stat)
        Logging.info(print_stat)
