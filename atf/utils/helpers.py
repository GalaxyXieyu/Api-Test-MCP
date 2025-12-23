# 自定义工具模块
def demo_get_id():
	return 111

def demo_func(a=None, b=None, c=None):
	if a and b and c:
		return a+b+c
	elif a and b:
		return a+b
	elif a and c:
		return a+c
	elif b and c:
		return b+c
	else:
		return 0