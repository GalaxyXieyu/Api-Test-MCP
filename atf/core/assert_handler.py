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
            if not field_path and assert_type not in ['mysql_query', 'mysql_query_exists', 'mysql_query_true']:
                log.error(f"断言的 'field' 不能为空: {assertion}")
                raise ValueError(f"断言的 'field' 不能为空: {assertion}")
            if assert_type in ['equal', 'not equal'] and expected is None:
                log.error(f"断言的 'expected' 不能为空: {assertion}")
                raise ValueError(f"断言的 'expected' 不能为空: {assertion}")
            if assert_type in ['in', 'not in'] and container is None:
                log.error(f"断言的 'container' 不能为空: {assertion}")
                raise ValueError(f"断言的 'container' 不能为空: {assertion}")

            # 获取字段的实际值
            field_value = self.get_field_value(response, field_path) if field_path else None

            # 处理各种断言类型
            if assert_type == 'equal':
                assert field_value == expected, f"Expected {expected}, but got {field_value}"
            elif assert_type == 'not equal':
                assert field_value != expected, f"Expected not {expected}, but got {field_value}"
            elif assert_type in ('is_none', 'is None', 'None'):
                assert field_value is None, f"Expected None, but got {field_value}"
            elif assert_type in ('is_not_none', 'is not None', 'not None'):
                assert field_value is not None, f"Expected not None, but got {field_value}"
            elif assert_type == 'in':
                assert field_value in container, f"Expected {field_value} to be in {container}"
            elif assert_type in ('not in', 'not_in'):
                assert field_value not in container, f"Expected {field_value} to be not in {container}"
            elif assert_type == 'mysql_query':
                self._validate_mysql_query(query, expected)
            elif assert_type == 'mysql_query_exists':
                self._validate_mysql_query_exists(query)
            elif assert_type == 'mysql_query_true':
                self._validate_mysql_query_true(query)
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