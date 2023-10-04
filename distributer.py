# -*- coding: utf-8 -*-
# !/usr/bin/python3
import os
import sys
import types
import asyncio
import importlib
from typing import Any

from adapter.bot import Bot
from adapter.utils import Logging
from adapter.message import Message, MessageSegment
from adapter.event import Event, MessageEvent, GroupMessageEvent

from utils import text_to_image

# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(__file__)

# 添加插件所在目录
sys.path.append(CURRENT_DIR + '/plugin')

# 插件字典
global plugin_dict
plugin_dict: dict[str, dict[str, Any]] = {}

# 消息分发转交
async def message_hand_out(bot: Bot, event: Event) -> str:
    '''消息分发转交

    :param bot: Bot 实例
    :type bot: Bot
    :param event: 收到的 Event 实例
    :type event: Event
    :return: 处理结果
    :rtype: str
    '''
    global plugin_dict # 插件字典
    # 判断是否为初次运行（插件字典为空）
    if len(plugin_dict) == 0:
        try:
            plugin_dict = refresh_plugin()
        except Exception as exception:
            print(f'导入插件时出错：{exception}')
            Logging.info(f'导入插件时出错：{exception}')
            Logging.error(exception)
            return 'None'
    
    if isinstance(event, MessageEvent): # 如果是消息
        # 判断是否为管理语句
        if (
            (message_string := str(event.message)).startswith('>> ') and
            bot.admin.is_admin(event.user_id)
        ): # 如果以固定字符组开头且来自主人id或管理员
            # 管理语句提取
            admin_message = message_string[3:]
            
            # 如果是管理员操作语句且来自主人id
            if admin_message.startswith('管理员') and event.user_id == bot.host_id:
                admin_message = admin_message[3:]
                # 提取第一个@对象为操作目标 ID
                target_id = -1
                for segment in event.message:
                    if segment.type == 'at':
                        try:
                            target_id = int(segment.data['qq'])
                            break
                        except:
                            return 'None'
                
                # 如果是添加管理员
                if admin_message.startswith('添加'):
                    # 添加管理员
                    try:
                        result = bot.admin.add(target_id)
                        if result == 'Add Successfully':
                            message = Message([
                                MessageSegment.text('<√> '),
                                MessageSegment.at(target_id),
                                MessageSegment.text(' 已被设置为管理员。')
                            ])
                            bot.send(event, message)
                            return 'OK'
                        elif result == 'Already Admin':
                            message = Message([
                                MessageSegment.text('<!> '),
                                MessageSegment.at(target_id),
                                MessageSegment.text(' 已经是管理员了。')
                            ])
                            bot.send(event, message)
                            return 'OK'
                    except Exception as exception:
                        bot.send(event, '<×> 啊嘞？好像哪里有点问题？')
                        Logging.error(exception)
                        return 'OK'
                    
                # 如果是移除管理员
                if admin_message.startswith('移除'):
                    # 删除管理员
                    try:
                        result = bot.admin.remove(target_id)
                        if result == 'Remove Successfully':
                            message = Message([
                                MessageSegment.text('<√> '),
                                MessageSegment.at(target_id),
                                MessageSegment.text(' 不再是管理员了。')
                            ])
                            bot.send(event, message)
                            return 'OK'
                        elif result == 'Not Admin':
                            
                            message = Message([
                                MessageSegment.text('<!> '),
                                MessageSegment.at(target_id),
                                MessageSegment.text(' 不是管理员。')
                            ])
                            bot.send(event, message)
                            return 'OK'
                    except Exception as exception:
                        bot.send(event, '<×> 啊嘞？好像哪里有点问题？')
                        Logging.error(exception)
                        return 'OK'

                # 如果是查看管理员列表
                if admin_message == '查看':
                    admin_list = bot.admin.get_list() # 获取管理员列表
                    
                    if len(admin_list) < 1: # 如果没有
                        bot.send(event, '现在没有管理员！')
                        return 'OK'
                    else: # 有管理员
                        reply = 'Bot 管理员有：'
                        for admin_id in admin_list: # 遍历添加输出
                            reply += '\n' + str(admin_id)
                        bot.send(event, reply)
                        return 'OK'
            
            # 如果是要求更新插件且来自主人id
            if admin_message == '插件更新' and event.user_id == bot.host_id:
                try:
                    plugin_dict = refresh_plugin()
                    bot.send(event, '<√> 插件已更新')
                    Logging.info('插件更新成功')
                    return 'OK'
                except Exception as exception:
                    print(f'{exception}')
                    Logging.info(f'导入插件时出错：{exception}')
                    Logging.error(exception)
                    bot.send(event, '<!> 插件更新失败')
                    return 'None'
                
            # 如果是要求黑名单插件且是群组消息
            if admin_message.startswith('屏蔽 ') and isinstance(event, GroupMessageEvent):
                block_name = admin_message[3:].strip()
                block_target = ''
                
                # 查找要进行操作的插件名或函数名
                for plugin_name, plugin_info in plugin_dict.items():
                    if block_name == plugin_name or block_name == plugin_info['name']: # 如果是插件包名或是插件名
                        block_target = plugin_name
                        if plugin_info['level'] == 'ADMIN': # 管理员等级插件无法黑名单
                            bot.send(event, '<!> 不能屏蔽管理员插件！')
                            return 'OK'
                        break
                    else:
                        for function_info in plugin_info['function_list']:
                            if block_name == function_info['function'] or block_name == function_info['name']: # 如果是子函数名或是功能名
                                block_target = function_info['function']
                                if plugin_info['level'] == 'ADMIN': # 管理员等级插件无法黑名单
                                    bot.send(event, '<!> 不能屏蔽管理员插件！')
                                    return 'OK'
                                break
                
                # 如果没有找到
                if block_target == '':
                    bot.send(event, f'<?> 没有找到 {block_name} 呢。')
                    return 'OK'
                    
                # 尝试屏蔽目标插件或功能
                try:
                    match bot.block_list.block(event.group_id, block_target):
                        case 'Block Successfully': # 屏蔽成功
                            bot.send(event, f'<√> {block_name} 已被屏蔽。')
                            return 'OK'
                        case 'Already Blocked': # 已被屏蔽
                            bot.send(event, f'<×> {block_name} 已经被屏蔽了哦。')
                            return 'OK'
                        case _:
                            return 'None'
                except Exception as exception:
                    bot.send(event, f'<!> 插件屏蔽时出错：{exception}')
                    Logging.info(f'屏蔽插件时出错：{exception}')
                    Logging.error(exception)
                    return 'OK'
                
            # 如果是要求取消黑名单插件且是群组消息
            elif admin_message.startswith('允许 ') and isinstance(event, GroupMessageEvent):
                allow_name = admin_message[3:].strip()
                allow_target = ''
                
                # 查找要进行操作的插件名或函数名
                for plugin_name, plugin_info in plugin_dict.items():
                    if any([
                        allow_name == plugin_name,
                        allow_name == plugin_info['name']
                    ]): # 如果是插件包名或是插件名
                        allow_target = plugin_name
                        break
                    else:
                        for function_info in plugin_info['function_list']:
                            if any([
                                allow_name == function_info['function'],
                                allow_name == function_info['name']
                            ]): # 如果是子函数名或是功能名
                                allow_target = function_info['function']
                                break
                
                # 如果没有找到
                if allow_target == '':
                    bot.send(event, f'<?> 没有找到 {allow_name} 呢。')
                    return 'OK'
                    
                # 尝试屏蔽目标插件或功能
                try:
                    match bot.block_list.allow(event.group_id, allow_target):
                        case 'Allow Successfully': # 解除屏蔽成功
                            bot.send(event, f'<√> {allow_name} 已解除屏蔽。')
                            return 'OK'
                        case 'Not Blocked': # 已被屏蔽
                            bot.send(event, f'<×> {allow_name} 没有被屏蔽哦。')
                            return 'OK'
                        case _:
                            return 'None'
                except Exception as exception:
                    bot.send(event, f'<!> 插件解除屏蔽时出错：{exception}')
                    Logging.info(f'解除屏蔽插件时出错：{exception}')
                    Logging.error(exception)
                    return 'OK'
                
        # 判断是否为帮助请求语句
        if event.raw_message.startswith('help'):
            # 提取请求信息
            help_message = event.raw_message[4:].strip()
            # 获取黑名单列表
            if isinstance(event, GroupMessageEvent):
                block_list = bot.block_list.get_list(event.group_id)
            else:
                block_list = []
            
            # 根据请求信息构建回应
            if help_message == '': # 如果请求信息为空
                help_reply = '本Bot由 WindowsSov8 编写，一切异常状况请向本人汇报。\n目前可用的功能有：\n'
                for plugin_name, plugin_info in plugin_dict.items(): # 遍历插件字典获取名称
                    if plugin_dict[plugin_name]['level'] == 'ADMIN': # 管理员等级插件无法被非管理员查看
                        # 判断发起者是否为 host 或管理员
                        if bot.admin.is_admin(event.user_id):
                            help_reply += '>>[ADMIN] ' + plugin_dict[plugin_name]['name'] + '\n'
                        continue
                    help_reply += '>>'
                    # 获取插件屏蔽信息
                    if plugin_name in block_list: # 如果有黑名单记录且在黑名单内
                        help_reply += '[BLOCKED] '
                    help_reply += plugin_dict[plugin_name]['name'] + '\n'
                help_reply += '获取指定功能帮助请发送 help + 功能名'
                # 发送回复
                bot.send(
                    event,
                    MessageSegment.image(
                        text_to_image(Message(help_reply))
                    )
                )
                return 'OK'
            
            else:
                # 请求不为空
                for plugin_name, plugin_info in plugin_dict.items():
                    if any([
                        help_message == plugin_name,
                        help_message == plugin_info['name']
                    ]): # 如果请求信息是功能名
                        event.message = Message('>> help') # 伪造信息
                        if (help_reply := await plugin_info['plugin'].help(bot, event)) != 'None': # 有帮助返回
                            if len(help_reply) >= 1000: # 如果帮助较长
                                help_reply = MessageSegment.image(
                                    text_to_image(Message(help_reply))
                                )
                            bot.send(event, help_reply)
                            return 'OK'
                        
                event.message = Message('>> ' + help_message) # 伪造信息
                help_tasks = [] # 创建任务列表
                for plugin_name in plugin_dict: # 遍历插件，此时将会无视黑名单群发
                    help_tasks.append(asyncio.create_task(plugin_dict[plugin_name]['plugin'].help(bot, event)))
                for help_task in help_tasks: # 执行任务列表
                    if (help_reply := (await asyncio.gather(help_task))[0]) != 'None': # 有帮助返回
                        if len(help_reply) >= 1000: # 如果帮助较长
                            help_reply = MessageSegment.image(
                                text_to_image(Message(help_reply))
                            )
                        bot.send(event, help_reply)
                        return 'OK'
                return 'None'
                
    # 将消息进行分发
    # 建立插件任务列表
    handle_tasks = []
    # 获取黑名单列表
    if not (group_id := getattr(event, 'group_id', None)) is None:
        block_list = bot.block_list.get_list(group_id)
    else:
        block_list: list[str] = []
    # 构建任务列表
    for plugin_name, plugin_info in plugin_dict.items():
        if not plugin_name in block_list:
            handle_tasks.append(asyncio.create_task(plugin_info['plugin'].main(bot, event))) # 创建并添加任务
        
    # 遍历执行插件任务
    for handle_task in handle_tasks:
        if (await asyncio.gather(handle_task))[0] == 'OK':
            return 'OK'
        
    return 'None'

# 插件初始化与更新
def refresh_plugin() -> dict:
    '''插件初始化与更新函数，遍历`plugin`文件夹内文件并导入，返回插件字典'''
    # 使用栈来迭代地重新加载所有子模块或子包
    def _reload_recursive_in_iter(plugin: types.ModuleType) -> None:
        '''使用栈来迭代地重新加载所有子模块或子包

        :param plugin: 要进行重新加载的模块
        :type plugin: types.ModuleType
        '''
        # 定义插件包所在的文件夹的路径
        fn_dir = os.path.dirname(os.path.abspath(__file__))
    
        pre_stack = [plugin] # 模块预存放栈
        stack = [] # 模块存放栈
        while pre_stack: # 迭代存放
            module = pre_stack.pop() # 取出栈中第一个模块
            stack.append(module)
            for attribute_name in dir(module): # 遍历查找模块内对象
                attribute = getattr(module, attribute_name) # 获取对象
                if isinstance(attribute, types.ModuleType): # 如果对象为模块
                    fn_child = getattr(attribute, '__file__', None) # 获取对象路径
                    if isinstance(fn_child, str): # 如果存在路径且为程序所在路径
                        if os.path.normcase(fn_child).startswith(os.path.normcase(fn_dir)):
                            pre_stack.append(attribute) # 放入栈中
        while stack: # 迭代重新加载
            module = stack.pop(-1)
            importlib.reload(module)
    
    plugin_dict = {}
    
    # 导入 plugin 包
    for plugin_name in os.listdir(CURRENT_DIR + '/plugin'):
        # 过滤不合法名称（不以 plugin_ 开头）
        if not plugin_name.startswith('plugin_'):
            continue
        try:
            plugin = importlib.import_module(f'{plugin_name}')
            _reload_recursive_in_iter(plugin)
        except Exception as exception:
            print(f'导入插件 {plugin_name} 时出错：{exception}')
            continue
        
        plugin_dict[plugin_name] = {'plugin': plugin}
        # 尝试获取插件名
        try:
            name = getattr(plugin, 'NAME')
            plugin_dict[plugin_name]['name'] = name
        except AttributeError:
            plugin_dict[plugin_name]['name'] = plugin_name
        # 尝试获取子功能列表
        try:
            function_list = getattr(plugin, 'FUNCTION_LIST')
            plugin_dict[plugin_name]['function_list'] = function_list
        except AttributeError:
            plugin_dict[plugin_name]['function_list'] = []
        # 尝试获取插件等级
        try:
            level = getattr(plugin, 'LEVEL')
            plugin_dict[plugin_name]['level'] = level
        except AttributeError:
            plugin_dict[plugin_name]['level'] = 'normal'
            
    return plugin_dict