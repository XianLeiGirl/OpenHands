Mamba安装，如果是网络问题，应该重试几次就好了吧

Openhands运行产生的日志为啥会默认到stderr？是主动设置的吗？

NullObservation 会存到json里吗？
当需要AWAITING_CONFIRMATION的action时，会暂时返回nullobservation，后面用户确认后会继续执行吗


1. action正常
2. action异常

To Study:
1. Duque popleft() 双端队列
2. self.browser_side, self.agent_side = multiprocessing.Pipe() 双进程通信
3. RATE_LIMITED异常时会通过retry_listener重新请求llm


turn_status
操作失败会重新请求吗？
 "observation": "edit”失败时也没状态码
FINISHED也会退出agent吗？如果finished代表此轮结束呢？
Mcp没有写入json，但日志里mcp.shared.exceptions.McpError: Timed out while waiting for response to ClientRequest.？
为啥”run”observation没有error字段？

openhands.runtime.action_execution_server



Openhands几大模块（使用者视角）
- 文件系统
- 日志系统
- 订阅系统 $
- 多线程系统 $
- 序列化系统
- 装饰器系统
- 脱敏系统
- 优雅退出系统 $


TODO: 装饰器系统怎么设计给其他人使用