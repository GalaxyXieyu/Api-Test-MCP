# @time:    2024-08-06
# @author:  xiaoqq

import re
import mysql.connector
import threading
from atf.core.log_manager import log

class AssertHandler:
    """断言处理器"""
    def __init__(self):
        self.connection = None
        self.lock = threading.Lock()
    
    def __enter__(self):
        log.info("Opening database connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            log.info("Closing database connection")
            self.connection.close()

    def handle_assertion(self, asserts, response, db_config=None):
        """
        验证 assert 列表中的所有断言
        :param asserts: 断言列表
        :param response: 请求返回的 response 对象
        :param db_config: 数据库配置字典，包含 host, user, password, database 等信息
        """
        log.info(f"执行断言: {asserts}")
        # 如果存在 MySQL 相关的断言类型，建立数据库连接
        if any(assertion['type'].startswith('mysql') for assertion in asserts):
            if db_config is None:
                raise ValueError("数据库配置 db_config 不能为空，因为有 MySQL 相关断言")
            self.connection = mysql.connector.connect(**db_config)
        
        for assertion in asserts:
            assert_type = assertion.get('type')
            field_path = assertion.get('field')
            expected = assertion.get('expected')
            container = assertion.get('container')
            query = assertion.get('query')

            # 检查必填字段
            if not field_path and assert_type not in [
                'mysql_query',
                'mysql_query_exists',
                'mysql_query_true',
                'contains',
                'contain',
                'status_code',
                'status',
            ]:
                log.error(f"断言的 'field' 不能为空: {assertion}")
                raise ValueError(f"断言的 'field' 不能为空: {assertion}")
            if assert_type in ['equal', 'equals', 'not equal', 'not_equal', 'not_equals'] and expected is None:
                log.error(f"断言的 'expected' 不能为空: {assertion}")
                raise ValueError(f"断言的 'expected' 不能为空: {assertion}")
            if assert_type == 'length' and expected is None:
                log.error(f"断言的 'expected' 不能为空: {assertion}")
                raise ValueError(f"断言的 'expected' 不能为空: {assertion}")
            if assert_type in ['in', 'not in', 'not_in'] and container is None:
                log.error(f"断言的 'container' 不能为空: {assertion}")
                raise ValueError(f"断言的 'container' 不能为空: {assertion}")

            # 获取字段的实际值
            field_value = self.get_field_value(response, field_path) if field_path else None

            # 处理各种断言类型
            if assert_type in ('status_code', 'status'):
                # status_code 检查 HTTP 状态码（response 可能是 dict 或 Response 对象）
                actual_status = response.get('_status_code') if isinstance(response, dict) else response.status_code
                assert actual_status == expected, f"Expected status code {expected}, but got {actual_status}"
            elif assert_type in ('equal', 'equals'):
                assert field_value == expected, f"Expected {expected}, but got {field_value}"
            elif assert_type in ('not equal', 'not_equal', 'not_equals'):
                assert field_value != expected, f"Expected not {expected}, but got {field_value}"
            elif assert_type in ('exists', 'exist'):
                assert field_value is not None, f"Expected field {field_path} to exist, but got None"
            elif assert_type in ('is_none', 'is None', 'None'):
                assert field_value is None, f"Expected None, but got {field_value}"
            elif assert_type in ('is_not_none', 'is not None', 'not None'):
                assert field_value is not None, f"Expected not None, but got {field_value}"
            elif assert_type == 'length':
                assert field_value is not None, f"Expected field {field_path} not to be None for length assertion"
                try:
                    actual_len = len(field_value)
                except TypeError:
                    raise ValueError(f"length 断言不支持该类型: field={field_path}, value={field_value}")
                assert actual_len == expected, f"Expected length {expected}, but got {actual_len}"
            elif assert_type == 'in':
                assert field_value in container, f"Expected {field_value} to be in {container}"
            elif assert_type in ('not in', 'not_in'):
                assert field_value not in container, f"Expected {field_value} to be not in {container}"
            elif assert_type in ('contains', 'contain'):
                # contains 不需要 field，直接检查 response 中是否包含 expected
                def _check_contains(obj, target):
                    """递归检查 obj 中是否包含 target"""
                    if isinstance(obj, dict):
                        return any(_check_contains(v, target) for v in obj.values())
                    elif isinstance(obj, list):
                        return any(_check_contains(item, target) for item in obj)
                    elif isinstance(obj, str):
                        return target in obj
                    else:
                        return str(obj) == str(target)

                assert _check_contains(response, expected), f"Expected {expected} to be in {response}"
            elif assert_type == 'mysql_query':
                self._validate_mysql_query(query, expected)
            elif assert_type == 'mysql_query_exists':
                self._validate_mysql_query_exists(query)
            elif assert_type == 'mysql_query_true':
                self._validate_mysql_query_true(query)
            # SSE 断言类型
            elif assert_type == 'sse_event_count':
                self._validate_sse_event_count(response, assertion)
            elif assert_type == 'sse_contains':
                self._validate_sse_contains(response, assertion)
            elif assert_type == 'sse_event_exists':
                self._validate_sse_event_exists(response, assertion)
            elif assert_type == 'sse_event_field':
                self._validate_sse_event_field(response, assertion)
            elif assert_type == 'sse_last_event':
                self._validate_sse_last_event(response, assertion)
            else:
                raise ValueError(f"未知的断言类型: {assert_type}")
        
        log.info(f"断言通过")

    def get_field_value(self, response, field_path):
        """
        根据字段路径获取响应中的值，支持数组索引和多级嵌套。
        :param response: 响应数据
        :param field_path: 字段路径，如 data[0].areaName.ids[1].id
        :return: 字段值或 None
        """
        # 使用正则表达式区分数组索引和字段名
        pattern = re.compile(r'([a-zA-Z_][\w]*)\[(\d+)\]|([a-zA-Z_][\w]*)')
        value = response
    
        # 找到所有匹配的部分并逐一处理
        for match in pattern.finditer(field_path):
            field, index, simple_field = match.groups()
        
            # 如果是数组形式，例如 data[0]
            if field and index is not None:
                value = value.get(field, []) if isinstance(value, dict) else None
                if isinstance(value, list) and len(value) > int(index):
                    value = value[int(index)]
                else:
                    value = None
        
            # 如果是普通字段
            elif simple_field:
                value = value.get(simple_field) if isinstance(value, dict) else None
        
            if value is None:
                break
    
        return value


    def _validate_mysql_query(self, query, expected):
        """
        执行 MySQL 查询并验证结果是否等于 expected
        :param query: 要执行的 MySQL 查询
        :param expected: 期望值
        """
        result = self._execute_query(query)
        assert result == expected, f"Expected {expected}, but got {result}"

    def _validate_mysql_query_exists(self, query):
        """
        执行 MySQL 查询并验证是否返回了至少一行结果
        :param query: 要执行的 MySQL 查询
        """
        result = self._execute_query(query)
        assert result is not None, f"Expected query to return results, but got None"

    def _validate_mysql_query_true(self, query):
        """
        执行 MySQL 查询并验证结果是否为真 (存在)
        :param query: 要执行的 MySQL 查询
        """
        result = self._execute_query(query)
        assert bool(result), f"Expected query result to be True, but got {result}"

    def _execute_query(self, query):
        """
        执行 MySQL 查询并返回结果
        :param query: 要执行的 MySQL 查询
        :return: 查询结果
        """
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query)
            try:
                result = cursor.fetchone()
                log.info(f"MySQL query executed: {query}, Result: {result}")
            except mysql.connector.Error as err:
                log.error(f"Error executing query: {query}, Error: {err}")
                raise
            cursor.close()
            return result[0] if result else None

    # ==================== SSE 断言方法 ====================

    def _validate_sse_event_count(self, response, assertion):
        """
        验证 SSE 事件数量
        :param response: SSEResponse 对象
        :param assertion: 断言配置，支持 expected (精确), min, max
        """
        count = response.event_count
        expected = assertion.get('expected')
        min_count = assertion.get('min')
        max_count = assertion.get('max')

        if expected is not None:
            assert count == expected, f"SSE 事件数量期望 {expected}，实际 {count}"
        if min_count is not None:
            assert count >= min_count, f"SSE 事件数量至少 {min_count}，实际 {count}"
        if max_count is not None:
            assert count <= max_count, f"SSE 事件数量最多 {max_count}，实际 {count}"
        log.info(f"SSE 事件数量断言通过: {count}")

    def _validate_sse_contains(self, response, assertion):
        """
        验证 SSE 事件中是否包含指定文本
        :param response: SSEResponse 对象
        :param assertion: 断言配置，expected 为要查找的文本
        """
        expected = assertion.get('expected')
        assert response.contains(expected), f"SSE 事件中未找到文本: {expected}"
        log.info(f"SSE 包含断言通过: {expected}")

    def _validate_sse_event_exists(self, response, assertion):
        """
        验证是否存在满足条件的 SSE 事件
        :param response: SSEResponse 对象
        :param assertion: 断言配置，支持 event_type, data_contains 等条件
        """
        conditions = {}
        if 'event_type' in assertion:
            conditions['event_type'] = assertion['event_type']
        if 'data_contains' in assertion:
            conditions['data_contains'] = assertion['data_contains']

        event = response.find_event(**conditions)
        assert event is not None, f"未找到满足条件的 SSE 事件: {conditions}"
        log.info(f"SSE 事件存在断言通过: {conditions}")

    def _validate_sse_event_field(self, response, assertion):
        """
        验证指定索引的 SSE 事件的字段值
        :param response: SSEResponse 对象
        :param assertion: 断言配置，index 为事件索引，field 为字段路径，expected 为期望值
        """
        index = assertion.get('index', 0)
        field = assertion.get('field')
        expected = assertion.get('expected')

        event = response.get_event(index)
        assert event is not None, f"SSE 事件索引 {index} 不存在"

        # 从 event.data 中获取字段值
        value = self._get_nested_value(event.get('data', {}), field)
        assert value == expected, f"SSE 事件[{index}].{field} 期望 {expected}，实际 {value}"
        log.info(f"SSE 事件字段断言通过: [{index}].{field} = {expected}")

    def _validate_sse_last_event(self, response, assertion):
        """
        验证最后一个 SSE 事件
        :param response: SSEResponse 对象
        :param assertion: 断言配置，支持 event_type, data_contains, field + expected
        """
        event = response.get_event(-1)
        assert event is not None, "没有收到任何 SSE 事件"

        if 'event_type' in assertion:
            assert event.get('event') == assertion['event_type'], \
                f"最后事件类型期望 {assertion['event_type']}，实际 {event.get('event')}"

        if 'data_contains' in assertion:
            assert assertion['data_contains'] in str(event.get('data', '')), \
                f"最后事件未包含: {assertion['data_contains']}"

        if 'field' in assertion and 'expected' in assertion:
            value = self._get_nested_value(event.get('data', {}), assertion['field'])
            assert value == assertion['expected'], \
                f"最后事件 {assertion['field']} 期望 {assertion['expected']}，实际 {value}"

        log.info(f"SSE 最后事件断言通过")

    def _get_nested_value(self, data, field_path):
        """从嵌套字典中获取值"""
        if not field_path or not isinstance(data, dict):
            return data
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
        
if __name__ == '__main__':
    class MockResponse:
        def __init__(self, json_data):
            self._json_data = json_data
        
        def json(self):
            return self._json_data
    
    assert_var = [
        {
            "type": "equal",
            "field": "code",
            "expected": 0
        },
        {
            "type": "is not None",
            "field": "data.id"
        },
        {
            "type": "equal",
            "field": "message",
            "expected": "success"
        }
    ]
    response_var = {'code': 0, 'message': 'success', 'data': {}}

    AssertHandler().handle_assertion(asserts=assert_var, response=response_var)