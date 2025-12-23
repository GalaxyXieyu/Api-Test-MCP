# @time:    2024-08-01
# @author:  xiaoqq

import requests
from atf.core.log_manager import log

class RequestHandler:
	@staticmethod
	def send_request(method, url, headers=None, data=None, params=None, files=None, timeout=10):
		log.info(f"正在发送 {method} 请求至 {url} ，headers={headers}, data={data}, params={params}, files={files}")
		
		if method.lower() == 'get':
			_params = params
			if not _params:
				_params = data
			response = requests.get(url, headers=headers, params=_params, timeout=timeout)
		elif method.lower() == 'post':
			if files:
				response = requests.post(url, headers=headers, files=files, timeout=timeout)
			elif headers and 'Content-Type' in headers and headers['Content-Type'] == 'application/x-www-form-urlencoded':
				response = requests.post(url, headers=headers, data=data, timeout=timeout)
			else:
				response = requests.post(url, headers=headers, json=data, timeout=timeout)
		elif method.lower() in ['put', 'delete']:
			response = requests.request(method, url, headers=headers, json=data, timeout=timeout)
		else:
			log.error(f"不支持的方法: {method}")
			raise ValueError(f"不支持的方法: {method}")
		
		try:
			response_json = response.json()
			log.info("返回参数：{}".format(response_json))
			return response_json
		except ValueError:
			log.error("非JSON响应：{}".format(response.text))
			response.raise_for_status()
		
		if not response.ok:
			log.error("请求失败：状态码 {}".format(response.status_code))
			response.raise_for_status()