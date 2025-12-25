"""
测试数据工厂 - 提供常用的数据生成函数
用法: {{ tools.timestamp() }}, {{ tools.uuid() }}, {{ tools.random_int(1, 100) }}
"""

import random
import string
import time
import uuid as _uuid
from datetime import datetime, timedelta


# ==================== 时间相关 ====================

def timestamp():
    """当前时间戳（秒）"""
    return int(time.time())


def timestamp_ms():
    """当前时间戳（毫秒）"""
    return int(time.time() * 1000)


def datetime_now(fmt: str = "%Y-%m-%d %H:%M:%S"):
    """当前时间字符串"""
    return datetime.now().strftime(fmt)


def date_today(fmt: str = "%Y-%m-%d"):
    """今天日期"""
    return datetime.now().strftime(fmt)


def date_offset(days: int = 0, fmt: str = "%Y-%m-%d"):
    """偏移日期，days 可为负数"""
    return (datetime.now() + timedelta(days=days)).strftime(fmt)


# ==================== 随机数据 ====================

def uuid():
    """生成 UUID"""
    return str(_uuid.uuid4())


def uuid_short():
    """生成短 UUID（8位）"""
    return str(_uuid.uuid4())[:8]


def random_int(min_val: int = 1, max_val: int = 10000):
    """随机整数"""
    return random.randint(min_val, max_val)


def random_float(min_val: float = 0.0, max_val: float = 100.0, precision: int = 2):
    """随机浮点数"""
    return round(random.uniform(min_val, max_val), precision)


def random_str(length: int = 8):
    """随机字符串（字母+数字）"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_letters(length: int = 8):
    """随机字母"""
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_digits(length: int = 6):
    """随机数字字符串"""
    return ''.join(random.choices(string.digits, k=length))


def random_choice(*items):
    """从给定选项中随机选择"""
    return random.choice(items) if items else None


# ==================== 模拟数据 ====================

def fake_email(prefix: str = "test"):
    """生成测试邮箱"""
    return f"{prefix}_{timestamp()}@test.com"


def fake_phone():
    """生成测试手机号（中国）"""
    prefixes = ['138', '139', '150', '151', '152', '158', '159', '186', '187', '188']
    return random.choice(prefixes) + random_digits(8)


def fake_username(prefix: str = "user"):
    """生成测试用户名"""
    return f"{prefix}_{uuid_short()}"


def fake_name():
    """生成随机中文姓名"""
    first_names = ['张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴']
    last_names = ['伟', '芳', '娜', '敏', '静', '强', '磊', '洋', '勇', '艳', '杰', '娟', '涛', '明', '超']
    return random.choice(first_names) + ''.join(random.choices(last_names, k=random.randint(1, 2)))


def fake_address():
    """生成随机地址"""
    cities = ['北京市', '上海市', '广州市', '深圳市', '杭州市', '成都市', '武汉市', '南京市']
    districts = ['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '西湖区', '武侯区', '江宁区']
    streets = ['科技路', '创新大道', '人民路', '中山路', '解放路', '建设路']
    return f"{random.choice(cities)}{random.choice(districts)}{random.choice(streets)}{random_int(1, 999)}号"


def fake_id_card():
    """生成测试身份证号（非真实）"""
    area = random_digits(6)
    year = random.randint(1970, 2000)
    month = str(random.randint(1, 12)).zfill(2)
    day = str(random.randint(1, 28)).zfill(2)
    seq = random_digits(3)
    check = random.choice('0123456789X')
    return f"{area}{year}{month}{day}{seq}{check}"


def fake_company():
    """生成测试公司名"""
    prefixes = ['华', '中', '东', '西', '南', '北', '新', '金', '银', '瑞']
    mids = ['科', '创', '智', '信', '达', '联', '通', '盛', '鑫', '源']
    suffixes = ['科技有限公司', '网络有限公司', '信息技术有限公司', '电子商务有限公司']
    return random.choice(prefixes) + random.choice(mids) + random.choice(suffixes)


# ==================== 兼容旧函数 ====================

def demo_get_id():
    """兼容旧版本"""
    return random_int(1, 1000)


def demo_func(a=None, b=None, c=None):
    """兼容旧版本"""
    vals = [v for v in [a, b, c] if v is not None]
    return sum(vals) if vals else 0


# ==================== 使用示例 ====================
if __name__ == '__main__':
    print(f"timestamp: {timestamp()}")
    print(f"uuid: {uuid()}")
    print(f"random_int: {random_int(1, 100)}")
    print(f"fake_email: {fake_email()}")
    print(f"fake_phone: {fake_phone()}")
    print(f"fake_name: {fake_name()}")
    print(f"fake_address: {fake_address()}")