# @time:    2024-09-10
# @author:  xiaoqq

import mysql.connector
import threading
import requests
from utils.log_manager import log


class TeardownHandler:
	"""测试用例后置操作处理器"""
	def __init__(self):
		self.connection = None
		self.lock = threading.Lock()
	
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.connection:
			self.connection.close()
	
	def handle_teardown(self, teardown_step, db_config=None):
		"""
		处理 teardown 步骤，根据 operation_type 区分处理方式
		:param teardown_step: teardown 中带数据库操作步骤
		:param db_config: 数据库配置字典，包含 host, user, password, database 等信息
		"""
		if db_config is None:
			raise ValueError("数据库配置 db_config 不能为空，因为有数据库相关操作")
		self._handle_db_operation(teardown_step, db_config)
	
	def _handle_api_request(self, step):
		"""
		处理 API 请求类型的 teardown 步骤
		:param step: 单个 teardown 步骤，包含 API 请求的详细信息
		"""
		path = step.get('path')
		method = step.get('method', 'GET').upper()
		headers = step.get('headers', {})
		data = step.get('data', {})

		log.info(f"执行 API 请求: {method} {path} 数据: {data}")

		# 执行 API 请求
		if method == 'POST':
			response = requests.post(path, json=data, headers=headers)
		elif method == 'GET':
			response = requests.get(path, headers=headers, params=data)
		else:
			raise ValueError(f"不支持的 HTTP 方法: {method}")

		log.info(f"API 响应状态码: {response.status_code}")
		response.raise_for_status()  # 如果请求失败则抛出异常
	
	def _handle_db_operation(self, step, db_config):
		"""
		处理数据库操作类型的 teardown 步骤
		:param step: 单个 teardown 步骤，包含数据库操作的详细信息
		:param db_config: 数据库配置字典，包含 host, user, password, database 等信息
		"""
		query = step.get('query')
		expected = step.get('expected')
		
		log.info(f"执行数据库操作: {query}")
		
		# 建立数据库连接（如果还没有连接的话）
		if not self.connection:
			self.connection = mysql.connector.connect(**db_config)
		
		with self.lock:
			cursor = self.connection.cursor()
			
			# 检查是否是查询语句
			if query.strip().lower().startswith("select"):
				cursor.execute(query)
				result = cursor.fetchone()
				
				if expected is not None:
					assert result[0] == expected, f"Expected {expected}, but got {result[0]}"
				else:
					log.info(f"查询结果: {result}")
			else:
				# 非查询操作 (如 DELETE, UPDATE, INSERT)
				cursor.execute(query)
				affected_rows = cursor.rowcount
				log.info(f"受影响的行数: {affected_rows}")
				
				# 对于非查询操作，验证是否有行受影响 (expected 为 True 表示至少一行被影响)
				if expected is not None:
					assert (affected_rows > 0) == expected, f"Expected operation to affect rows: {expected}, but got {affected_rows > 0}"
			
			cursor.close()
	
	def _execute_query(self, query):
		"""
		执行 MySQL 查询并返回结果
		:param query: 要执行的 MySQL 查询
		:return: 查询结果
		"""
		with self.lock:
			cursor = self.connection.cursor()
			cursor.execute(query)
			result = cursor.fetchone()
			cursor.close()
			return result[0] if result else None