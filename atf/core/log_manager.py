# @time:    2024-08-01
# @author:  xiaoqq

import os
from datetime import datetime
from loguru import logger

class LogManager:
    '''
    日志记录器封装
    '''
    
    @staticmethod
    def setup_logging():
        root_path = os.path.dirname(os.path.abspath(__file__))  # 根目录
        log_dir = os.path.join(root_path, "../logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_name = datetime.now().strftime("%Y-%m-%d")  # 日志文件名命名格式为“年-月-日”
        sink = os.path.join(log_dir, "{}.log".format(log_name))  # 日志文件路径
        level = "DEBUG"  # 记录的最低日志级别为DEBUG
        encoding = "utf-8"  # 写入日志文件时编码格式为utf-8
        enqueue = True  # 多线程多进程时保证线程安全
        rotation = "500MB"  # 日志文件最大为500MB，超过则新建文件记录日志
        retention = "1 week"  # 日志保留时长为1星期，超时则清除
        
        logger.add(
            sink=sink,
            level=level,
            encoding=encoding,
            enqueue=enqueue,
            rotation=rotation,
            retention=retention
        )
    
    @staticmethod
    def get_logger():
        return logger

# 在工程开始时初始化设置日志记录器
LogManager.setup_logging()

# 获取日志记录器实例，用于其他模块调用
log = LogManager.get_logger()


if __name__ == '__main__':
    log.debug("debug消息")
    log.info("info消息")
    log.warning("warning消息")
    log.error("error消息")