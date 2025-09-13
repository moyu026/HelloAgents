# @file: test_handoff.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 测试多Agent切换功能

import sys
import os
import json

# 获取当前文件所在目录的上级目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将上级目录添加到系统路径
sys.path.append(parent_dir)

from src.tool import tool
from src.team import MultiAgent, Team


@tool
def add_numbers(a: int, b: int) -> str:
    """
    计算两个数字的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        计算结果
    """
    result = a + b
    return f"计算结果：{a} + {b} = {result}"


@tool
def get_greeting(name: str = "朋友") -> str:
    """
    生成问候语
    
    Args:
        name: 要问候的人的名字
    
    Returns:
        问候语
    """
    return f"你好，{name}！很高兴见到你！"


def test_agent_handoff():
    """测试Agent切换功能"""
    print("=== 测试Agent切换功能 ===")
    
    # 创建分流Agent
    triage_agent = MultiAgent(
        name="分流助手",
        instructions="""你是一个智能分流助手。根据用户的需求，将其分配给合适的专家：

1. 如果用户需要数学计算，请切换到"计算专家"
2. 如果用户需要问候或聊天，请切换到"问候专家"
3. 如果用户只是打招呼，你可以直接回复

请使用工具调用格式进行切换。""",
        handoff_description="智能分流助手，负责分析用户需求并分配给合适的专家"
    )
    
    # 创建计算专家
    calc_agent = MultiAgent(
        name="计算专家",
        instructions="""你是计算专家，专门处理数学计算问题。

当用户需要计算时，使用add_numbers工具进行计算。
计算完成后，提供清晰的结果说明。

如果用户的问题不是计算相关的，请切换回"分流助手"。""",
        tools=[add_numbers],
        handoff_description="数学计算专家，处理各种数学计算问题"
    )
    
    # 创建问候专家
    greeting_agent = MultiAgent(
        name="问候专家",
        instructions="""你是问候专家，专门处理问候和日常聊天。

当用户需要问候时，使用get_greeting工具生成友好的问候语。
你可以进行简单的聊天对话。

如果用户的问题不是聊天相关的，请切换回"分流助手"。""",
        tools=[get_greeting],
        handoff_description="问候和聊天专家，处理日常对话和问候"
    )
    
    # 设置handoff关系
    triage_agent.handoffs = [calc_agent, greeting_agent]
    calc_agent.handoffs = [triage_agent]
    greeting_agent.handoffs = [triage_agent]
    
    # 创建团队
    team = Team([triage_agent, calc_agent, greeting_agent])
    
    # 测试不同类型的请求
    test_cases = [
        "请计算 10 + 20",
        "你好，我叫小明",
        "帮我算一下 5 + 3",
        "问候一下张三"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i}: {question} ---")
        try:
            result = team.run(question, max_turns=6)
            print(f"✅ 最终结果: {result}")
        except Exception as e:
            print(f"❌ 错误: {e}")
        print("-" * 60)


def test_simple_handoff():
    """测试简单的两个Agent切换"""
    print("\n=== 测试简单Agent切换 ===")
    
    # Agent A：处理问候
    agent_a = MultiAgent(
        name="问候助手",
        instructions="""你是问候助手，专门处理问候。

如果用户说"你好"或类似问候，请回复友好的问候。
如果用户问其他问题（比如计算），请切换到"计算助手"。

使用<response>标签包围你的最终回复。""",
        handoff_description="处理问候和欢迎"
    )
    
    # Agent B：处理计算
    agent_b = MultiAgent(
        name="计算助手",
        instructions="""你是计算助手，专门处理数学计算。

如果用户需要计算，使用add_numbers工具进行计算。
如果用户要问候，请切换到"问候助手"。

使用<response>标签包围你的最终回复。""",
        tools=[add_numbers],
        handoff_description="处理数学计算"
    )
    
    # 设置handoff关系
    agent_a.handoffs = [agent_b]
    agent_b.handoffs = [agent_a]
    
    # 创建团队
    team = Team([agent_a, agent_b])
    
    # 测试切换
    test_cases = [
        "你好！",
        "请计算 7 + 8"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n--- 简单测试 {i}: {question} ---")
        try:
            result = team.run(question, max_turns=4)
            print(f"✅ 结果: {result}")
        except Exception as e:
            print(f"❌ 错误: {e}")
        print("-" * 40)


if __name__ == "__main__":
    test_simple_handoff()
    test_agent_handoff()
