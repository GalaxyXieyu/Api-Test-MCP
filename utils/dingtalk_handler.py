# @time:    2024-08-27
# @author:  xiaoqq

from dingtalkchatbot.chatbot import DingtalkChatbot
from utils.log_manager import log


def set_color_and_size(text, color, size='14px'):
	colors = {
		"green": "#00CC00",  # 成功
		"blue": "#0000FF",  # 信息
		"yellow": "#FFCC00",  # 跳过
		"red": "#FF0000",  # 失败/错误
		"black": "#000000"  # 普通文本
	}
	# 使用 style 属性控制字体大小和加粗
	return f'<font color="{colors.get(color, "#000000")}" style="font-size:{size}; font-weight:bold;">{text}</font>'


def format_field(label, value, color='black', size='14px', icon=None):
	"""
	格式化消息字段，支持颜色、字体大小和图标
	"""
	label = set_color_and_size(label, color, size)
	if icon:
		return f"{icon} {label}: {value}"
	return f"{label}: {value}"


class DingTalkHandler:
	"""
	钉钉消息发送
	"""
	
	def __init__(self, webhook, secret, project=None):
		self.ding = DingtalkChatbot(webhook=webhook, secret=secret)
		self.project = project
	
	def _build_message(self, conclusion, total, passed, failed, error, skipped, start_time, duration):
		"""
		构建消息文本
		"""
		# 消息标题，字体加粗且字号更大
		header = "<strong><font size='24px'>📢 接口自动化测试监控通知</font></strong>"
		
		# 信息字段及其样式
		items = [
			('测试结果', conclusion, 'green' if conclusion == '执行通过' else 'red', '16px'),
			('开始时间', start_time, 'black', '14px'),
			('执行时长', f'{duration:.2f} 秒', 'black', '14px'),
			('用例总数', total, 'blue', '14px'),
			('成功用例', passed, 'green', '14px'),
			('失败用例', failed, 'red', '14px'),
			('错误用例', error, 'red', '14px'),
			('跳过用例', skipped, 'yellow', '14px')
		]
		
		# 定义 Unicode Emoji 图标
		icons = {
			'测试结果': '📝',
			'开始时间': '⏰',
			'执行时长': '⏱️',
			'用例总数': '📊',
			'成功用例': '✅',
			'失败用例': '❌',
			'错误用例': '💥',
			'跳过用例': '⚠️'
		}
		
		# 使用优化后的样式和图标构建消息体
		lines = [format_field(item[0], item[1], item[2], item[3], icon=icons.get(item[0])) for item in items]
		text = "\n\n".join(lines)
		return f"{header}\n\n{text}"
	
	def send_markdown_msg(self, conclusion, total, passed, failed, error, skipped, start_time, duration):
		"""
		发送测试用例执行结果
		"""
		# 构建钉钉消息内容
		text = self._build_message(conclusion, total, passed, failed, error, skipped, start_time, duration)
		title = "【接口自动化测试通知】"
		try:
			log.info("钉钉机器人正在发送结果......")
			self.ding.send_markdown(title=title, text=text, is_at_all=True)
			log.info("测试结果已发送至钉钉群")
		except Exception as e:
			log.error("钉钉机器人发送消息失败：%s", e)
			
if __name__ == '__main__':
	webhook = "https://oapi.dingtalk.com/robot/send?access_token=your_dingtalk_access_token"
	secret = "your_secret"
	DingTalkHandler(webhook, secret).send_markdown_msg(
		conclusion="执行通过",
		total = 100,
		passed = 95,
		failed = 2,
		error = 3,
		skipped = 0,
		start_time = "2024-9-14 11:44:43",
		duration = 1000.22
	)