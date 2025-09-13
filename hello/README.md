# @file: README.md
# @date: 2025/01/15
# @author: jiaohui
# @description: Hello Agents - React Agent教学项目

# Hello Agents 🤖

一个基于ReAct模式的AI Agent教学项目，从单Agent到多Agent协作，提供完整的智能代理系统学习路径。

## 📋 项目概述

本项目实现了一个完整的ReAct (Reasoning and Acting) Agent框架，包含：

- **ReAct Agent**: 基于思考-行动-观察循环的智能代理
- **多Agent协作**: 智能体间自动切换和任务分配系统
- **工具系统**: 可扩展的工具注册和调用机制
- **自动工具生成**: 根据Agent配置自动生成切换工具
- **LLM客户端**: 统一的大语言模型调用接口
- **Team管理**: 支持多智能体编排的团队框架

## 🏗️ 项目架构

```
hello/
├── src/                    # 核心源码
│   ├── agent.py           # ReactAgent核心实现
│   ├── llm.py             # LLM客户端封装
│   ├── tool.py            # 工具系统和装饰器
│   ├── team.py            # 多Agent团队管理
│   └── utils/             # 工具函数
│       ├── completions.py # 对话历史管理
│       └── extraction.py  # 标签内容提取
├── tests/                 # 测试用例
│   ├── test_react.py      # ReAct Agent测试
│   ├── test_tool.py       # 工具系统测试
│   ├── test_team.py       # 多Agent团队测试
│   ├── test_simple_team.py # 简单团队测试
│   ├── test_handoff.py    # Agent切换测试
│   └── test_client.py     # LLM客户端测试
├── examples/              # 示例项目
│   ├── customer_service_demo.py      # 客服系统演示
│   └── interactive_customer_service.py # 交互式客服系统
├── requirements.txt       # 依赖包列表
├── env.example           # 环境变量示例
└── README.md             # 项目文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd hello

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑.env文件，填入你的API配置
```

### 2. 环境变量配置

在`.env`文件中配置以下参数：

```bash
API_KEY=your_api_key_here
BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=Qwen/Qwen3-8B
```

### 3. 运行示例

```bash
# 运行ReAct Agent测试
python tests/test_react.py

# 运行工具系统测试  
python tests/test_tool.py

# 运行LLM客户端测试
python tests/test_client.py
```

## 🔧 核心组件

### ReactAgent

基于ReAct模式的智能代理，支持：
- 思考-行动-观察循环
- 工具调用和结果处理
- 多轮对话管理
- 错误处理和恢复

```python
from src.agent import ReactAgent
from src.tool import get_tools

# 创建Agent
tools = get_tools(["calculate", "get_weather"])
agent = ReactAgent(
    name="智能助手",
    instructions="你是一个智能助手",
    tools=tools
)

# 运行对话
result = agent.run("请计算1+2*3的结果")
print(result)
```

### MultiAgent & Team

多智能体协作系统，支持：
- 智能体间自动切换
- 工具自动生成和分发
- 上下文管理和传递
- 分布式任务处理

```python
from src.team import MultiAgent, Team
from src.tool import tool

@tool
def calculate(a: int, b: int) -> str:
    """计算两个数字的和"""
    return f"{a} + {b} = {a + b}"

# 创建多个Agent
triage_agent = MultiAgent(
    name="分流助手",
    instructions="你是分流助手，负责将用户分配给合适的专家",
    handoff_description="智能分流助手"
)

math_agent = MultiAgent(
    name="数学专家",
    instructions="你是数学专家，专门处理计算问题",
    tools=[calculate],
    handoff_description="数学计算专家"
)

# 设置切换关系
triage_agent.handoffs = [math_agent]
math_agent.handoffs = [triage_agent]

# 创建团队
team = Team([triage_agent, math_agent])

# 运行多agent对话
result = team.run("请计算 5 + 3")
print(result)
```

### 工具系统

简单易用的工具注册和调用机制：

```python
from src.tool import tool

@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"
```

### LLM客户端

统一的大语言模型调用接口：

```python
from src.llm import LLMClient

llm = LLMClient()
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]
response = llm(messages)
```

## 🛠️ 内置工具

项目包含以下预置工具：

1. **计算器 (calculate)**: 执行数学表达式计算
2. **天气查询 (get_weather)**: 获取指定城市天气信息
3. **网页抓取 (fetch_web_content)**: 获取网页内容

## 🎮 快速体验

### 单Agent体验
```bash
# 测试ReAct Agent
python hello/tests/test_react.py
```

### 多Agent体验
```bash
# 交互式客服系统（推荐）
python hello/examples/interactive_customer_service.py

# 自动化演示
python hello/examples/customer_service_demo.py
```

## 📚 使用示例

### 基础对话

```python
from src.agent import ReactAgent

agent = ReactAgent(
    name="友好助手",
    instructions="你是一个友好的助手"
)
response = agent.run("你好，请介绍一下自己")
```

### 工具调用

```python
from src.agent import ReactAgent
from src.tool import get_tools

tools = get_tools(["calculate"])
agent = ReactAgent(
    name="数学助手",
    instructions="你是一个数学助手",
    tools=tools
)
response = agent.run("请计算 (2+3)*4 的结果")
```

### 多Agent协作

```python
from src.team import MultiAgent, Team
from src.tool import tool

@tool
def get_weather(city: str) -> str:
    """获取天气信息"""
    return f"{city}今天天气晴朗"

@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    return f"计算结果: {eval(expression)}"

# 创建专业化的Agent
weather_agent = MultiAgent(
    name="天气专家",
    instructions="你是天气专家，专门提供天气信息",
    tools=[get_weather],
    handoff_description="天气预报专家"
)

math_agent = MultiAgent(
    name="数学专家",
    instructions="你是数学专家，专门处理计算问题",
    tools=[calculate],
    handoff_description="数学计算专家"
)

triage_agent = MultiAgent(
    name="分流助手",
    instructions="你是分流助手，根据用户需求分配给合适的专家",
    handoffs=[weather_agent, math_agent],
    handoff_description="智能分流助手"
)

# 创建团队
team = Team([triage_agent, weather_agent, math_agent])

# 测试不同类型的请求
print(team.run("北京天气怎么样？"))
print(team.run("请计算 2 + 3 * 4"))
```

### 交互式客服系统

```python
# 运行交互式客服系统
python hello/examples/interactive_customer_service.py

# 支持多轮对话的客服场景：
# 👤 您：你好，我想买一个手机
# 🤖 客服：您好！很高兴为您服务...
# 👤 您：帮我搜索iPhone
# 🤖 客服：以下是搜索到的iPhone型号及价格信息...
```

### 自动化测试演示

```python
# 运行自动化测试，包含12个测试案例
python hello/examples/customer_service_demo.py

# 测试案例包括：
# - 商品咨询和搜索
# - 订单查询和跟踪
# - 退款和售后服务
# - Agent间智能切换
```

## ✨ 核心特性

### 🤖 ReAct Agent
- **思考-行动-观察循环**：完整的ReAct模式实现
- **工具调用**：支持自定义工具和函数调用
- **错误处理**：健壮的异常处理和恢复机制
- **多轮对话**：支持上下文管理的连续对话

### 🔄 多Agent协作
- **自动切换**：根据任务类型智能切换Agent
- **工具生成**：自动生成`switch_to_xxagent`切换工具
- **上下文传递**：Agent间无缝的上下文传递
- **专业分工**：每个Agent专注特定领域任务

### 🛠️ 工具系统
- **装饰器注册**：使用`@tool`装饰器简单注册工具
- **类型检查**：自动生成工具签名和参数验证
- **灵活扩展**：支持任意Python函数作为工具

### 📱 实际应用
- **客服系统**：完整的多Agent客服解决方案
- **智能分流**：自动识别用户需求并分配专员
- **交互式对话**：支持真实的多轮客服对话

## 🔄 开发进度

- [x] 1. OpenAI API调用和LLM客户端
- [x] 2. 工具系统和装饰器实现
- [x] 3. ReAct Agent核心逻辑
- [x] 4. 多Agent架构设计
- [x] 5. 团队协作和切换机制
- [x] 6. 自动工具生成(`switch_to_xxagent`)
- [x] 7. 多轮对话和上下文管理
- [x] 8. 客服系统完整示例
- [x] 9. 交互式对话支持
- [x] 10. 自动化测试套件
- [ ] 11. 流式输出支持
- [ ] 12. 上下文记忆优化
- [ ] 13. 性能监控和日志
- [ ] 14. 部署和生产化

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- 感谢 OpenAI 提供的强大API
- 感谢开源社区的贡献和支持
- 参考了多个优秀的Agent框架设计

---

**Happy Coding! 🎉**
