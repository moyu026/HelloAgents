# @file: team.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 多Agent团队管理和编排系统

import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from .agent import ReactAgent
from .tool import Tool, tool
from .utils.completions import build_prompt_structure, ChatHistory, update_chat_history
from .utils.extraction import extract_tag_content
from .llm import LLMClient


def transform_string_function_style(name: str) -> str:
    """
    将字符串转换为函数风格命名
    空格→下划线，保留中文字符，全部小写
    """
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Replace special characters but keep Chinese characters and alphanumeric
    name = re.sub(r"[^\w\u4e00-\u9fff]", "_", name)
    # Remove multiple consecutive underscores
    name = re.sub(r"_+", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")
    return name.lower()


# 多Agent系统的推荐提示前缀
HANDOFF_PROMPT_PREFIX = """
# 系统上下文
你是一个多智能体系统的一部分，该系统旨在使智能体协调和执行变得简单。
系统使用两个主要抽象：**智能体（Agents）**和**切换（Handoffs）**。
智能体包含指令和工具，可以在适当时将对话切换到另一个智能体。
切换通过调用切换函数实现，通常命名为 `switch_to_<agent_name>`。
智能体之间的切换在后台无缝处理；不要在与用户的对话中提及或关注这些切换。

重要：当你需要切换到其他智能体时，必须使用工具调用格式：
<tool_call>
{"name": "switch_to_xxx", "arguments": {}, "id": 0}
</tool_call>
"""


@dataclass
class MultiAgent:
    """
    多Agent系统中的简化Agent类
    专门用于多Agent协作场景
    """
    name: str
    instructions: str
    tools: List[Tool] = None
    handoff_description: str = None
    handoffs: List['MultiAgent'] = None

    def __post_init__(self):
        self.tools = self.tools or []
        self.handoffs = self.handoffs or []
        # 内部使用ReactAgent但不暴露循环
        self._react_agent = ReactAgent(
            name=self.name,
            tools=self.tools,
            instructions=self.instructions
        )

    def process_single_turn(self, messages: List[dict], model: str = "Qwen/Qwen3-8B") -> str:
        """
        处理单轮对话，不进行循环
        """
        return self._react_agent.llm(messages, model)


class Team:
    """
    多Agent团队管理器，负责Agent编排和切换
    类似于swarm的runner概念
    """

    def __init__(self, agents: List[MultiAgent] = None):
        """
        初始化Team

        Args:
            agents: Agent列表，第一个作为默认的manager/triage agent
        """
        self.agents = agents or []
        self.agents_dict = {agent.name: agent for agent in self.agents}
        self.current_agent = self.agents[0] if self.agents else None
        self.llm = LLMClient()
        self.chat_history = ChatHistory([])

        # 为所有agent生成handoff工具
        self._generate_handoff_tools()
        # 为所有agent添加handoff提示前缀
        self._add_handoff_instructions()

    def add_agent(self, agent: MultiAgent):
        """添加新的agent到团队"""
        self.agents.append(agent)
        self.agents_dict[agent.name] = agent
        if self.current_agent is None:
            self.current_agent = agent
        # 重新生成handoff工具
        self._generate_handoff_tools()
        self._add_handoff_instructions()

    def _add_handoff_instructions(self):
        """为所有agent添加handoff指令前缀"""
        for agent in self.agents:
            if not agent.instructions.startswith(HANDOFF_PROMPT_PREFIX):
                agent.instructions = f"{HANDOFF_PROMPT_PREFIX}\n\n{agent.instructions}"
                # 更新内部ReactAgent的指令
                agent._react_agent.instructions = agent.instructions

    def _generate_handoff_tools(self):
        """为所有agent生成switch_to工具"""
        # 清除现有的switch_to工具
        for agent in self.agents:
            # 移除现有的switch_to工具
            agent.tools = [tool for tool in agent.tools if not tool.name.startswith('switch_to_')]
            agent._react_agent.tools = agent.tools.copy()
            agent._react_agent.tools_dict = {tool.name: tool for tool in agent.tools}

        # 为每个agent生成其他agent的switch_to工具
        for agent in self.agents:
            for target_agent in self.agents:
                if target_agent.name != agent.name:
                    # 生成switch_to工具
                    switch_tool = self._create_switch_to_tool(target_agent)
                    tool_name = switch_tool.name

                    # 检查是否已存在同名工具，避免重复
                    if tool_name not in agent._react_agent.tools_dict:
                        agent.tools.append(switch_tool)
                        agent._react_agent.tools.append(switch_tool)
                        agent._react_agent.tools_dict[tool_name] = switch_tool

    def _create_switch_to_tool(self, target_agent: MultiAgent) -> Tool:
        """
        为目标agent创建switch_to工具

        Args:
            target_agent: 目标agent

        Returns:
            Tool: switch_to工具实例
        """
        # 生成工具名称
        tool_name = transform_string_function_style(f"switch_to_{target_agent.name}")

        # 生成工具描述
        description = f"切换到 {target_agent.name} 智能体来处理请求。"
        if target_agent.handoff_description:
            description += f" {target_agent.handoff_description}"

        # 创建切换函数
        def switch_function() -> str:
            """切换到目标agent"""
            self.current_agent = target_agent
            return json.dumps({"assistant": target_agent.name}, ensure_ascii=False)

        # 设置函数名称和文档
        switch_function.__name__ = tool_name
        switch_function.__doc__ = description

        # 使用tool装饰器创建Tool实例
        return tool(switch_function)

    def run(self, messages, max_turns: int = 10, model: str = "Qwen/Qwen3-8B") -> str:
        """
        运行多agent对话

        Args:
            messages: 用户输入（字符串）或消息历史（列表）
            max_turns: 最大轮数
            model: 使用的模型

        Returns:
            str: 最终响应
        """
        if not self.current_agent:
            raise ValueError("没有可用的agent")

        # 处理输入：支持字符串或消息列表
        if isinstance(messages, str):
            # 单个字符串输入
            user_prompt = build_prompt_structure(
                prompt=messages, role="user", tag="question"
            )
            # 初始化对话历史
            self.chat_history = ChatHistory([
                build_prompt_structure(
                    prompt=self.current_agent.instructions,
                    role="system",
                ),
                user_prompt,
            ])
        elif isinstance(messages, list):
            # 消息历史列表
            self.chat_history = ChatHistory([
                build_prompt_structure(
                    prompt=self.current_agent.instructions,
                    role="system",
                )
            ])
            # 添加历史消息
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg and "role" in msg:
                    self.chat_history.append(build_prompt_structure(
                        prompt=msg["content"],
                        role=msg["role"]
                    ))
        else:
            raise ValueError("messages must be a string or list of message dicts")

        print(f"🚀 开始对话，当前Agent: {self.current_agent.name}")

        # 多agent ReAct循环
        for turn in range(max_turns):
            print(f"\n--- 第 {turn + 1} 轮 ---")
            print(f"当前Agent: {self.current_agent.name}")

            # 获取当前agent的工具
            current_tools = self.current_agent.tools
            if current_tools:
                # 更新当前agent的工具签名到指令中
                tools_signature = "".join([tool.fn_signature for tool in current_tools])
                system_prompt = self.current_agent.instructions
                if "tools" not in system_prompt.lower():
                    system_prompt += f"\n\n可用工具:\n{tools_signature}"

                # 更新系统消息
                self.chat_history[0] = build_prompt_structure(
                    prompt=system_prompt,
                    role="system",
                )

            # 调用LLM
            completion = self.llm(self.chat_history, model)
            print(f"LLM响应: {completion}")

            # 检查是否有最终响应
            response = extract_tag_content(str(completion), "response")
            if response.found:
                print(f"✅ 获得最终响应: {response.content[0]}")
                return response.content[0]

            # 如果没有工具调用且有实质内容，也可以作为最终响应
            tool_calls = extract_tag_content(str(completion), "tool_call")
            if not tool_calls.found:
                # 没有工具调用，检查是否有有意义的回复
                content = str(completion).strip()
                if content and len(content) > 10:  # 避免空响应或过短响应
                    # 过滤掉一些明显的中间状态
                    if not any(keyword in content.lower() for keyword in [
                        "switch_to", "工具调用", "tool_call", "正在处理", "请稍等"
                    ]):
                        print(f"✅ 获得最终响应: {content}")
                        return content

            # 提取思考和工具调用
            thought = extract_tag_content(str(completion), "thought")
            tool_calls = extract_tag_content(str(completion), "tool_call")

            # 更新对话历史
            update_chat_history(self.chat_history, completion, "assistant")

            # 显示思考内容
            if thought.found and thought.content:
                print(f"💭 思考: {thought.content[0]}")
            else:
                print("💭 思考: [未找到思考内容]")

            # 处理工具调用
            if tool_calls.found:
                observations = self._process_tool_calls(tool_calls.content)
                print(f"🔧 工具结果: {observations}")

                # 将工具结果添加到对话历史
                update_chat_history(self.chat_history, f"{observations}", "user")

                # 检查是否发生了agent切换
                for obs in observations.values():
                    if isinstance(obs, str) and obs.startswith('{"assistant":'):
                        try:
                            switch_data = json.loads(obs)
                            new_agent_name = switch_data.get("assistant")
                            if new_agent_name and new_agent_name in self.agents_dict:
                                print(f"🔄 切换到Agent: {new_agent_name}")
                                # 更新系统消息为新agent的指令
                                self.chat_history[0] = build_prompt_structure(
                                    prompt=self.current_agent.instructions,
                                    role="system",
                                )
                        except json.JSONDecodeError:
                            pass

        print("⚠️ 达到最大轮数限制")
        return "对话已达到最大轮数限制，请重新开始。"

    def _process_tool_calls(self, tool_calls_content: List[str]) -> Dict:
        """
        处理工具调用

        Args:
            tool_calls_content: 工具调用内容列表

        Returns:
            Dict: 工具调用结果
        """
        observations = {}

        for tool_call_str in tool_calls_content:
            try:
                tool_call = json.loads(tool_call_str)
                tool_name = tool_call["name"]
                tool_id = tool_call.get("id", 0)

                print(f"🔧 使用工具: {tool_name}")

                # 在当前agent的工具中查找
                tool = None
                for t in self.current_agent.tools:
                    if t.name == tool_name:
                        tool = t
                        break

                if tool is None:
                    error_msg = f"工具 '{tool_name}' 不存在"
                    print(f"❌ {error_msg}")
                    observations[tool_id] = error_msg
                    continue

                # 验证和执行工具调用
                from .tool import validate_arguments
                validated_tool_call = validate_arguments(
                    tool_call, json.loads(tool.fn_signature)
                )
                print(f"📋 工具调用参数: {validated_tool_call}")

                # 执行工具
                result = tool.run(**validated_tool_call["arguments"])
                print(f"✅ 工具结果: {result}")

                # 存储结果
                observations[validated_tool_call["id"]] = result

            except Exception as e:
                error_msg = f"工具调用失败: {str(e)}"
                print(f"❌ {error_msg}")
                observations[tool_call.get("id", 0)] = error_msg

        return observations