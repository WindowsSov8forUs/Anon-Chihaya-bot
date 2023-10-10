'''Go-cqhttp 杂项。
WindowsSov8 Anon Bot 自用 Adapter
'''
# -*- coding: utf-8 -*-
# !/usr/bin/python3
import os
import json
import inspect
import threading
import traceback
from io import BytesIO
from pathlib import Path
from base64 import b64encode
from typing import Union, Any
from datetime import datetime

# 获取当前文件所在父目录
CURRENT_DIR = os.path.dirname(os.path.dirname(__file__))

# json 文件读写类
class MyJson:
    '''json 文件读写类'''
    locks: dict[str, threading.Lock] = {}
    '''文件锁字典'''
    
    # json 文件读取为字典
    @classmethod
    def read_to_dict(cls, file_name: str) -> dict[str, Any]:
        '''json 文件读取为字典

        :param file_name: 要读取的文件路径
        :type file_name: str
        :return: 文件内容
        :rtype: dict
        '''
        # 判断文件是否已有线程锁对象，如果没有则创建一个
        if not file_name in list(cls.locks.keys()):
            cls.locks[file_name] = threading.Lock()
            
        # 获取对应的线程锁对象
        lock = cls.locks[file_name]
        # 尝试获取线程锁
        lock.acquire()
        
        # 检测文件是否存在
        if not os.path.exists(file_name):
            data = {}
            with open(file_name, 'w+', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            return data
        
        # 尝试进行文件操作
        try:
            with open(file_name, 'r+', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as exception:
            raise exception
        else:
            return data
        finally:
            # 释放线程锁
            lock.release()
            
    # json 文件读取为列表
    @classmethod
    def read_to_list(cls, file_name: str) -> list[Any]:
        '''json 文件读取为列表

        :param file_name: 要读取的文件路径
        :type file_name: str
        :return: 文件内容
        :rtype: list
        '''
        # 判断文件是否已有线程锁对象，如果没有则创建一个
        if not file_name in list(cls.locks.keys()):
            cls.locks[file_name] = threading.Lock()
            
        # 获取对应的线程锁对象
        lock = cls.locks[file_name]
        # 尝试获取线程锁
        lock.acquire()
        
        # 检测文件是否存在
        if not os.path.exists(file_name):
            data = []
            with open(file_name, 'w+', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            return data
        
        # 尝试进行文件操作
        try:
            with open(file_name, 'r+', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as exception:
            raise exception
        else:
            return data
        finally:
            # 释放线程锁
            lock.release()
            
    # json 文件写入
    @classmethod
    def write(cls, file_name: str, data: Union[dict[str, Any], list[Any]]) -> None:
        '''json 文件写入

        :param file_name: 要写入的文件路径
        :type file_name: str
        :param data: 要写入的内容
        :type data: Union[dict[str, Any], list[Any]]
        '''
        # 判断文件是否已有线程锁对象，如果没有则创建一个
        if not file_name in list(cls.locks.keys()):
            cls.locks[file_name] = threading.Lock()
            
        # 获取对应的线程锁对象
        lock = cls.locks[file_name]
        # 尝试获取线程锁
        lock.acquire()
        
        # 尝试进行文件操作
        try:
            with open(file_name, 'w+', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as exception:
            raise exception
        else:
            return None
        finally:
            # 释放线程锁
            lock.release()

# 日志记录类
class Logging:
    '''日志记录类'''
    lock = threading.Lock() # 创建线程锁对象
    
    # 输出日志记录方法
    @classmethod
    def info(cls, info: str) -> None:
        '''输出日志记录方法

        :param info: 记录的日志内容
        :type info: str
        '''
        # 获取当前日期
        now = datetime.now()
        date_now = now.strftime('%Y-%m-%d')
        # 获取引用模块名称
        module = inspect.getmodule(inspect.stack()[1][0])
        if not module is None:
            name = module.__name__
        else:
            name = ''
        
        # 拼接完整日志内容
        log_message = '[{time}] INFO in {name}: {info}\n'.format(
            time = now.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
            name = name,
            info = info
        )
        
        # 获取线程锁
        cls.lock.acquire()
        # 检测日志路径是否存在
        if not os.path.exists(CURRENT_DIR + '/log'):
            os.mkdir(CURRENT_DIR + '/log')
        # 创建并写入日志文件
        with open(CURRENT_DIR + f'/log/{date_now}.log', 'a+', encoding='utf-8') as log_file:
            log_file.write(log_message)
        # 释放线程锁
        cls.lock.release()
        
    # 错误信息日志记录方法
    @classmethod
    def error(cls, exception: Exception) -> None:
        '''输出日志记录方法

        :param exception: 记录的错误信息
        :type exception: Exception
        '''
        # 获取当前日期
        now = datetime.now()
        date_now = now.strftime('%Y-%m-%d')
        # 获取引用模块名称
        module = inspect.getmodule(inspect.stack()[1][0])
        if not module is None:
            name = module.__name__
        else:
            name = ''
            
        # 获取错误追踪信息
        error = '\n' + ''.join(traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__
            ))
        # 拼接完整日志内容
        log_message = '[{time}] ERROR in {name}: {error}\n'.format(
            time = now.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3],
            name = name,
            error = error
            )
        
        # 获取线程锁
        cls.lock.acquire()
        # 检测日志路径是否存在
        if not os.path.exists(CURRENT_DIR + '/log'):
            os.mkdir(CURRENT_DIR + '/log')
        # 创建并写入日志文件
        with open(CURRENT_DIR + f'/log/{date_now}.log', 'a+', encoding='utf-8') as log_file:
            log_file.write(log_message)
        # 释放线程锁
        cls.lock.release()

# 将文件转换为字符串
def f2s(file: Union[str, bytes, BytesIO, Path]) -> str:
    '''将文件转换为字符串

    :param file: 文件对象
    :type file: Union[str, bytes, BytesIO, Path]
    :return: 转换后的文件字符串
    :rtype: str
    '''
    if isinstance(file, BytesIO): # 如果是 BytesIO 对象
        file = file.getvalue()
    if isinstance(file, bytes): # 如果是字节对象
        file = f'base64://{b64encode(file).decode()}'
    elif isinstance(file, Path): # 如果是路径对象
        file = file.resolve().as_uri()
    return file

# 对字符串进行转义
def escape(string: str, *, escape_comma: bool=False) -> str:
    '''对字符串进行转义

    :param string: 需要转义的字符串
    :type string: str
    :param escape_comma: 是否转义逗号 `,`
    :type escape_comma: bool, optional
    :return: 转义后的字符串
    :rtype: str
    '''
    string = string.replace('&', '&amp;').replace('[', '&#91;').replace(']', '&#93;')
    if escape_comma:
        string = string.replace(',', '&#44;')
    return string

# 对字符串进行去转义
def unescape(string: str) -> str:
    '''对字符串进行转义

    :param string: 需要去转义的字符串
    :type string: str
    :return: 去转义后的字符串
    :rtype: str
    '''
    return (
        string.replace('&#44;', ',')
        .replace('&#91;', '[')
        .replace('&#93;', ']')
        .replace('&amp;', '&')
    )
