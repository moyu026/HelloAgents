# @file: test_team.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 多Agent团队系统测试

import sys
import os
import json
import math
import requests

# 获取当前文件所在目录的上级目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将上级目录添加到系统路径
sys.path.append(parent_dir)

from src.tool import tool, get_tools
from src.team import MultiAgent, Team


# ===== 工具定义 =====

@tool
def calculate(expression: str) -> str:
    """
    执行数学计算，支持加减乘除、幂运算及基础函数（sin/cos/sqrt等）
    
    Args:
        expression: 数学表达式字符串，例如"2+3*4"、"sqrt(16)"、"sin(pi/2)"
    
    Returns:
        计算结果或错误信息
    """
    try:
        # 安全执行数学计算，限制可用函数
        allowed = {
            'math': math,
            'pi': math.pi,
            'e': math.e
        }
        result = eval(expression, {"__builtins__": None}, allowed)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}. 请检查表达式格式"


@tool
def get_weather(city: str = None) -> str:
    """
    获取指定城市的天气预报信息
    
    Args:
        city: 城市名称，例如："北京"、"纽约"、"东京"、"武汉"
    
    Returns:
        天气预报信息
    """
    try:
        endpoint = "https://wttr.in/{}"
        if city:
            response = requests.get(endpoint.format(city))
        else:
            response = requests.get(endpoint.format(""))
        response.raise_for_status()
        text_result = response.text
        print(f"Weather data for {city}: \n{text_result}")
        return text_result
    except Exception as e:
        print(f"Error in getting weather for {city}: {str(e)}")
        return json.dumps({"operation": "get_current_weather", "error": str(e)})


@tool
def search_knowledge(query: str) -> str:
    """
    搜索知识库获取相关信息
    
    Args:
        query: 搜索查询词
        
    Returns:
        搜索结果
    """
    # 模拟知识库搜索
    knowledge_base = {
        "python": "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。",
        "ai": "人工智能(AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
        "机器学习": "机器学习是人工智能的一个子集，使计算机能够在没有明确编程的情况下学习和改进。",
        "深度学习": "深度学习是机器学习的一个子集，使用神经网络来模拟人脑的学习过程。"
    }
    
    query_lower = query.lower()
    for key, value in knowledge_base.items():
        if key.lower() in query_lower or query_lower in key.lower():
            return f"知识库搜索结果：{value}"
    
    return f"抱歉，没有找到关于'{query}'的相关信息。"


# ===== Agent定义 =====

def create_customer_service_team():
    """创建客服团队示例"""
    
    # 1. 分流Agent - 负责判断用户需求并分配给合适的专家
    triage_agent = MultiAgent(
        name="分流助手",
        instructions="""你是一个智能分流助手，负责理解用户需求并将其分配给合适的专家。

你的职责：
1. 仔细分析用户的问题
2. 判断问题类型：数学计算、天气查询、知识搜索等
3. 将用户转接给最合适的专家

可用的专家：
- 数学专家：处理各种数学计算问题
- 天气专家：提供天气预报和相关信息  
- 知识专家：回答各种知识性问题

请根据用户问题选择合适的专家。""",
        handoff_description="智能分流助手，负责分析用户需求并分配给合适的专家"
    )
    
    # 2. 数学专家Agent
    math_agent = MultiAgent(
        name="数学专家",
        instructions="""你是一个数学计算专家，擅长处理各种数学问题。

你的职责：
1. 理解用户的数学问题
2. 使用计算工具进行精确计算
3. 提供清晰的计算结果和解释

如果用户的问题不是数学相关的，请切换回分流助手。""",
        tools=[calculate],
        handoff_description="数学计算专家，处理各种数学计算和公式求解"
    )
    
    # 3. 天气专家Agent
    weather_agent = MultiAgent(
        name="天气专家", 
        instructions="""你是一个天气预报专家，专门提供天气信息。

你的职责：
1. 理解用户的天气查询需求
2. 使用天气工具获取准确的天气信息
3. 提供详细的天气预报和建议

如果用户的问题不是天气相关的，请切换回分流助手。""",
        tools=[get_weather],
        handoff_description="天气预报专家，提供各地天气信息和预报"
    )
    
    # 4. 知识专家Agent
    knowledge_agent = MultiAgent(
        name="知识专家",
        instructions="""你是一个知识问答专家，擅长回答各种知识性问题。

你的职责：
1. 理解用户的知识查询需求
2. 使用知识搜索工具查找相关信息
3. 提供准确、详细的知识解答

如果用户的问题不在你的知识范围内，请切换回分流助手。""",
        tools=[search_knowledge],
        handoff_description="知识问答专家，回答各种科技、学术和常识问题"
    )
    
    # 设置handoff关系
    triage_agent.handoffs = [math_agent, weather_agent, knowledge_agent]
    math_agent.handoffs = [triage_agent]
    weather_agent.handoffs = [triage_agent]
    knowledge_agent.handoffs = [triage_agent]
    
    # 创建团队
    team = Team([triage_agent, math_agent, weather_agent, knowledge_agent])
    
    return team


def test_simple_team():
    """测试简单的两个agent切换"""
    print("=== 简单团队测试 ===")
    
    # 创建两个简单的agent
    agent1 = MultiAgent(
        name="助手A",
        instructions="你是助手A，专门处理问候。如果用户问其他问题，请切换到助手B。",
        handoff_description="处理问候和欢迎"
    )
    
    agent2 = MultiAgent(
        name="助手B", 
        instructions="你是助手B，专门回答问题。如果用户要问候，请切换到助手A。",
        tools=[calculate],
        handoff_description="回答各种问题"
    )
    
    agent1.handoffs = [agent2]
    agent2.handoffs = [agent1]
    
    team = Team([agent1, agent2])
    
    # 测试对话
    result = team.run("你好！")
    print(f"结果: {result}")


def test_customer_service():
    """测试客服团队"""
    print("\n=== 客服团队测试 ===")
    
    team = create_customer_service_team()
    
    # 测试不同类型的问题
    test_cases = [
        "请计算 2 + 3 * 4 的结果",
        "北京今天天气怎么样？", 
        "什么是机器学习？",
        "你好，我需要帮助"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i}: {question} ---")
        try:
            result = team.run(question, max_turns=5)
            print(f"最终结果: {result}")
        except Exception as e:
            print(f"错误: {e}")
        print("-" * 50)


if __name__ == "__main__":
    # 运行测试
    test_simple_team()
    test_customer_service()
