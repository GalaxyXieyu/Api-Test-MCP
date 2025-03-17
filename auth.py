# @time:    2024-08-15
# @author:  xiaoqq

import requests
from utils.globals import Globals
from utils.log_manager import log
import base64


class EncryptionManager:
    """
    加密管理器，用于处理不同项目的加密逻辑。
    PS: 需要根据被测项目登录接口的加密方式进行定义，此处只是一个demo。
    """
    
    def __init__(self):
        self.public_keys = {
            "merchant": {
                "test": "test_public_key",
                "online": "online_public_key"
            },
            "user": {
                "test": "test_public_key",
                "online": "test_public_key"
            }
        }
    
    def encrypt(self, src_str, project_name, env="pre"):
        """
        根据给定的项目名称使用RSA加密并转换为Base64格式。

        :param src_str: 需要加密的原始字符串
        :param project_name: 项目名称（"merchant" 或 "user"）
        :param env: 环境名称（"test", "pre", 等），默认为 "pre"
        :return: 加密后的字符串
        """
        from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
        from Crypto.PublicKey import RSA
        
        if env == "pre": # 预发与线上的签名一样
            env = "online"
        public_key = self.public_keys[project_name].get(env)
        if not public_key:
            log.error(f"No public key found for project '{project_name}' in environment '{env}'")
            raise ValueError(f"No public key found for project '{project_name}' in environment '{env}'")

        public_key_str = '-----BEGIN PUBLIC KEY-----\n' + public_key + '\n-----END PUBLIC KEY-----'
        rsakey = RSA.importKey(public_key_str)
        cipher = Cipher_pksc1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(src_str.encode()))
        return cipher_text.decode()


class Auth:
    """
    项目登录
    PS: 需要根据被测项目登录接口的加密方式进行定义，此处只是一个demo。
    """
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
    
    def login(self, project_name, login_config, env='pre', timeout=10):
        url = login_config['url']
        method = login_config['method']
        headers = login_config.get('headers', {})
        data = login_config['data'].copy()
        
        # 加密用户名和密码
        if project_name in ["merchant", "user"]:
            data['account'] = self.encryption_manager.encrypt(data['account'], project_name, env)
            data['password'] = self.encryption_manager.encrypt(data['password'], project_name, env)
        
        # 执行登录请求
        response = requests.request(method, url, json=data, headers=headers, timeout=timeout)
        
        # 提取token
        token = response.json().get('data').get('token')
        return token
    
if __name__ == '__main__':
    # pass
    project_name = "user"
    login_config = {
  "url": "https://xxxxxx.com/login",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json"
  },
  "data": {
    "account": "13500000000",
    "password": "xxxxxx",
    "authorizationClientType": 2,
    "loginType": 3,
    "loginVersion": 2
  }
}
    
    print(Auth().login(project_name, login_config))