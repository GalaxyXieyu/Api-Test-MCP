# @time:    2024-08-01
# @author:  xiaoqq

import json
import time
import requests
from atf.core.log_manager import log


class SSEResponse:
    """SSE 响应封装"""
    def __init__(self, events, raw_lines, status_code):
        self.events = events          # 解析后的事件列表
        self.raw_lines = raw_lines    # 原始行数据
        self.status_code = status_code
        self.event_count = len(events)

    def get_event(self, index):
        """获取指定索引的事件"""
        return self.events[index] if 0 <= index < len(self.events) else None

    def get_all_data(self, field=None):
        """获取所有事件的 data，可选提取特定字段"""
        if field:
            return [e.get('data', {}).get(field) for e in self.events if isinstance(e.get('data'), dict)]
        return [e.get('data') for e in self.events]

    def find_event(self, **kwargs):
        """查找匹配条件的事件"""
        for event in self.events:
            match = True
            for key, value in kwargs.items():
                if key == 'data_contains':
                    if value not in str(event.get('data', '')):
                        match = False
                elif key == 'event_type':
                    if event.get('event') != value:
                        match = False
                else:
                    if event.get(key) != value:
                        match = False
            if match:
                return event
        return None

    def contains(self, text):
        """检查是否包含指定文本"""
        return any(text in str(e.get('data', '')) for e in self.events)


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
            response_json['_status_code'] = response.status_code  # 添加状态码到响应中
            log.info("返回参数：{}".format(response_json))
            return response_json
        except ValueError:
            log.error("非JSON响应：{}".format(response.text))
            response.raise_for_status()

        if not response.ok:
            log.error("请求失败：状态码 {}".format(response.status_code))
            response.raise_for_status()

    @staticmethod
    def send_sse_request(method, url, headers=None, data=None, params=None,
                         timeout=60, max_events=None, stop_on=None):
        """
        发送 SSE 流式请求
        :param method: 请求方法
        :param url: 请求地址
        :param headers: 请求头
        :param data: 请求体
        :param params: 查询参数
        :param timeout: 超时时间（秒）
        :param max_events: 最大事件数，达到后停止
        :param stop_on: 停止条件，如 {"data_contains": "[DONE]"} 或 {"event_type": "done"}
        :return: SSEResponse 对象
        """
        headers = headers or {}
        headers.setdefault('Accept', 'text/event-stream')

        log.info(f"正在发送 SSE {method} 请求至 {url}, timeout={timeout}, max_events={max_events}, stop_on={stop_on}")

        events = []
        raw_lines = []
        current_event = {}

        try:
            with requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method.upper() != 'GET' else None,
                params=params if method.upper() == 'GET' else None,
                stream=True,
                timeout=timeout
            ) as resp:
                status_code = resp.status_code
                start_time = time.time()

                for line in resp.iter_lines(decode_unicode=True):
                    # 超时检查
                    if time.time() - start_time > timeout:
                        log.info(f"SSE 请求超时，已收集 {len(events)} 个事件")
                        break

                    if line:
                        raw_lines.append(line)

                        if line.startswith('event:'):
                            current_event['event'] = line[6:].strip()
                        elif line.startswith('data:'):
                            data_str = line[5:].strip()
                            # 尝试解析 JSON
                            try:
                                current_event['data'] = json.loads(data_str)
                            except json.JSONDecodeError:
                                current_event['data'] = data_str
                        elif line.startswith('id:'):
                            current_event['id'] = line[3:].strip()
                        elif line.startswith('retry:'):
                            current_event['retry'] = int(line[6:].strip())
                    else:
                        # 空行表示事件结束
                        if current_event:
                            events.append(current_event)
                            log.debug(f"收到 SSE 事件: {current_event}")

                            # 检查停止条件
                            if stop_on:
                                should_stop = True
                                for key, value in stop_on.items():
                                    if key == 'data_contains':
                                        if value not in str(current_event.get('data', '')):
                                            should_stop = False
                                    elif key == 'event_type':
                                        if current_event.get('event') != value:
                                            should_stop = False
                                    else:
                                        if current_event.get(key) != value:
                                            should_stop = False
                                if should_stop:
                                    log.info(f"满足停止条件 {stop_on}，停止接收")
                                    break

                            # 检查最大事件数
                            if max_events and len(events) >= max_events:
                                log.info(f"达到最大事件数 {max_events}，停止接收")
                                break

                            current_event = {}

                # 处理最后一个未完成的事件
                if current_event:
                    events.append(current_event)

        except requests.exceptions.Timeout:
            log.warning(f"SSE 请求超时，已收集 {len(events)} 个事件")
            status_code = 0
        except Exception as e:
            log.error(f"SSE 请求异常: {e}")
            raise

        sse_response = SSEResponse(events, raw_lines, status_code)
        log.info(f"SSE 请求完成，共收到 {sse_response.event_count} 个事件")
        return sse_response