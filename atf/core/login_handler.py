# @time:    2024-09-20
# @author:  xiaoqq

from atf.core.config_manager import ConfigManager
from atf.auth import Auth
from atf.core.globals import Globals
from atf.core.log_manager import log

class LoginHandler:
	"""
	用于处理项目登录的管理类，提供登录判断和登录操作。
	"""

	def __init__(self):
		self.config_manager = ConfigManager()

	def login_if_needed(self, project_name, project_config, env):
		"""
		判断项目是否需要登录，如果需要则进行登录
		:param project_name: 项目名称
		:param project_config: 项目配置
		:param env: 环境名称
		:return: 登录成功返回 token，失败返回 None
		"""
		if project_config and project_config.get('is_need_login'):
			auth_class = Auth()
			# 获取 auth_class 中指定名称的方法，如果找不到该方法（例如 project_name_login），则使用默认的 login 方法。
			login_function = getattr(auth_class, f'{project_name}_login', auth_class.login)
			log.info(f"正在登录 {project_name}, 登录参数为：{project_config['login']}")
			try:
				token = login_function(project_name, project_config['login'], env)
				log.info(f"{project_name} 登录成功并获取到 token: {token}。")
				return token
			except Exception as e:
				log.error(f"{project_name} 登录失败：{e}")
				return None
		return None

	def check_and_login_project(self, project_name, env):
		"""
		检查并登录指定项目，如果 Globals 中没有 token，则执行登录操作
		:param project_name: 项目名称
		:param env: 环境名称
		"""
		project_info = Globals.get(project_name)
		if project_info is None or not project_info.get("token"):
			project_env_config = self.config_manager.get_project_env_config(project_name, env)
			if project_env_config is not None:
				log.info(f"project_name, project_env_config, env：{project_name}, {project_env_config}, {env}")
				token = self.login_if_needed(project_name, project_env_config.get(project_name), env)
				if token:
					# 将 token 存入全局变量
					Globals.update(project_name, "token", token)
					# log.info(f"{project_name} 登录成功并获取 token。")
				else:
					log.error(f"{project_name} 登录失败。")
			else:
				log.warning(f"未找到项目 {project_name} 的配置，跳过登录。")
		else:
			log.info(f"{project_name} 已经登录，跳过登录操作。")
