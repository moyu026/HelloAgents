# @file: test_simple_team.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 简单的多Agent团队测试

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
def simple_calculate(a: int, b: int) -> str:
    """
    简单的加法计算
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        计算结果
    """
    result = a + b
    return f"{a} + {b} = {result}"


def test_tool_generation():
    """测试工具生成是否正确"""
    print("=== 测试工具生成 ===")
    
    # 创建两个简单的agent
    agent1 = MultiAgent(
        name="计算助手",
        instructions="你是计算助手，专门处理数学计算。",
        tools=[simple_calculate],
        handoff_description="处理数学计算"
    )
    
    agent2 = MultiAgent(
        name="聊天助手", 
        instructions="你是聊天助手，专门处理日常对话。",
        handoff_description="处理日常对话和问候"
    )
    
    # 创建团队
    team = Team([agent1, agent2])
    
    # 检查工具是否正确生成
    print(f"计算助手的工具数量: {len(agent1.tools)}")
    for tool in agent1.tools:
        print(f"  - {tool.name}: {tool.fn_signature}")
    
    print(f"聊天助手的工具数量: {len(agent2.tools)}")
    for tool in agent2.tools:
        print(f"  - {tool.name}: {tool.fn_signature}")


def test_simple_conversation():
    """测试简单对话"""
    print("\n=== 测试简单对话 ===")
    
    # 创建一个简单的agent
    agent = MultiAgent(
        name="测试助手",
        instructions="""你是一个测试助手。
当用户说"你好"时，请直接回复"你好！我是测试助手。"
请使用<response>标签包围你的最终回复。""",
        handoff_description="测试助手"
    )
    
    team = Team([agent])
    
    try:
        result = team.run("你好", max_turns=3)
        print(f"对话结果: {result}")
    except Exception as e:
        print(f"错误: {e}")


def test_tool_call():
    """测试工具调用"""
    print("\n=== 测试工具调用 ===")
    
    agent = MultiAgent(
        name="计算助手",
        instructions="""你是一个计算助手。
当用户要求计算时，使用simple_calculate工具。
请使用<response>标签包围你的最终回复。""",
        tools=[simple_calculate],
        handoff_description="计算助手"
    )
    
    team = Team([agent])
    
    try:
        result = team.run("请计算 3 + 5", max_turns=5)
        print(f"计算结果: {result}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    test_tool_generation()
    test_simple_conversation()
    test_tool_call()
