# @time:    2024-08-01
# @author:  xiaoqq

import os
import yaml
from utils.globals import Globals
from utils.log_manager import log


class ConfigManager:
	"""
	用于处理 config.yaml 的配置管理类
	"""
	_config = None  # 类变量，用于存储加载的配置
	
	@classmethod
	def load_config(cls):
		if cls._config is not None:
			return cls._config  # 如果已加载，则直接返回
		
		config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config.yaml")
		try:
			with open(config_path, 'r') as file:
				cls._config = yaml.safe_load(file)
			if cls._config is None:
				log.error(f"{config_path} 未找到配置信息")
				raise ValueError(f"{config_path} 未找到配置信息")
			log.info("读取工程配置信息成功")
			
			# 将DingTalk配置信息存入Globals
			dingtalk_config = cls._config.get('notifications').get("dingtalk")
			Globals.set("dingtalk", dingtalk_config)
			
			return cls._config
		except FileNotFoundError:
			log.error(f"未找到配置文件: {config_path}")
			raise FileNotFoundError(f"未找到配置文件: {config_path}")
		except yaml.YAMLError as e:
			log.error(f"YAML 配置文件解析错误: {e}")
			raise ValueError(f"YAML 配置文件解析失败: {e}")
	
	@classmethod
	def get_project_env_config(cls, project_name, env):
		"""
		获取指定项目和环境的配置信息
		:param project_name: 项目名称
		:param env: 环境名称 (如 test, pre, online)
		:return: 项目的环境配置字典或 None
		"""
		config = cls.load_config()
		project_config = config["projects"].get(project_name, None)
		
		if project_config is None:
			return None
		
		final_config = {}
		
		if "is_scene" in project_config and project_config["is_scene"]:
			for sub_project in project_config.get("sub_projects", []):
				sub_project_config = config["projects"].get(sub_project, None)
				if sub_project_config is None:
					log.warning(f"子项目{sub_project}在配置文件中不存在")
					continue
				
				sub_project_env_config = sub_project_config.get(env, None)
				if sub_project_env_config:
					cls.validate_config(sub_project_env_config)
					final_config[sub_project] = sub_project_env_config
				else:
					log.warning(f"子项目 {sub_project} 中未找到环境 {env} 的配置信息，返回 None")
					final_config[sub_project] = None
				# 存储子项目配置信息到Globals中
				Globals.set(sub_project, sub_project_env_config)
		else:
			project_env_config = project_config.get(env, None)
			if project_env_config:
				cls.validate_config(project_env_config)
				final_config[project_name] = project_env_config
			else:
				log.warning(f"项目 {project_name} 中未找到环境 {env} 的配置信息，返回 None")
				final_config[project_name] = None
			# 存储项目配置信息到Globals中
			Globals.set(project_name, project_env_config)
		
		return final_config
	
	@staticmethod
	def validate_config(project_env_config):
		"""
		验证配置文件的项目环境配置中是否有必需字段
		:param project_env_config: 项目的环境配置字典
		"""
		required_keys = ['host', 'is_need_login']  # 需要验证的关键字段
		for key in required_keys:
			if key not in project_env_config:
				log.error(f"{project_env_config} 中缺少必需配置项 {key}")
				raise ValueError(f"{project_env_config} 中缺少必需配置项 {key}")
		
		if project_env_config['is_need_login']:
			login_config = project_env_config.get('login', {})
			required_login_keys = ['url', 'method', 'data']
			for key in required_login_keys:
				if key not in login_config:
					log.error(f"{project_env_config} 中登录配置缺失或不完整")
					raise ValueError(f"{project_env_config} 中登录配置缺失或不完整")
			
			
if __name__ == '__main__':
	conf = ConfigManager.get_project_env_config(project_name="merchant", env="pre")
	print(conf)