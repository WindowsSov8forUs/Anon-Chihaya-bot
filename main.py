# -*- coding: utf-8 -*-
# !/usr/bin/python3
import asyncio
from flask import Flask, request

from distributer import message_hand_out

from adapter.bot import Bot
from adapter.event import Event
from adapter.utils import Logging
from adapter.adapter import Adapter

# 反向监听端口
PORT = 12365

# 生成 Flask 类的 app 实例
app = Flask(__name__)
# 创建一个 bot 实例
bot = Bot(
    1953421488, # 机器人 ID
    1242954863, # 主人 ID
    Adapter(port_send=12312) # 监听端口
)

# 收取消息处理
@app.route('/', methods=["POST"]) # 限制触发URL
def get_post() -> str:
    '''收取消息处理，若获取成功将输出获取消息，并返回 `OK`'''
    # 从 go-cqhttp 获取消息并尝试转换为事件对象
    try:
        event = bot.post2event(request.get_json())
    except Exception as exception:
        Logging.info(f'事件转换失败：{exception}')
        print(f'事件转换失败：{exception}')
        return 'None'
    
    # 尝试分发事件上报
    if isinstance(event, Event):
        try:
            asyncio.run(message_hand_out(bot, event))
        except Exception as exception:
            Logging.error(exception)
        
    return 'OK'

# 使应用运行于服务器
if __name__ == '__main__': # 限制运行条件
    app.run(host='0.0.0.0', port=PORT)