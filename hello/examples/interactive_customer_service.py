# @file: interactive_customer_service.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 交互式客服系统演示 - 支持多轮对话

import sys
import os
import uuid
import json
from typing import List, Dict

# 获取当前文件所在目录的上级目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 将上级目录添加到系统路径
sys.path.append(parent_dir)

from src.team import MultiAgent, Team
from src.tool import tool


# ===== 工具定义 =====

@tool
def calculate_price(base_price: float, discount: float = 0.0) -> str:
    """
    计算商品价格
    
    Args:
        base_price: 商品原价
        discount: 折扣率 (0.0-1.0)
    
    Returns:
        计算后的价格信息
    """
    final_price = base_price * (1 - discount)
    savings = base_price - final_price
    return f"原价: ¥{base_price:.2f}, 折扣: {discount*100:.1f}%, 现价: ¥{final_price:.2f}, 节省: ¥{savings:.2f}"


@tool
def check_order_status(order_id: str) -> str:
    """
    查询订单状态
    
    Args:
        order_id: 订单号
    
    Returns:
        订单状态信息
    """
    # 模拟订单状态查询
    order_statuses = {
        "12345": "已发货，预计明天到达",
        "67890": "正在处理中，预计今天发货",
        "11111": "已送达，感谢您的购买",
        "22222": "订单异常，请联系客服"
    }
    
    status = order_statuses.get(order_id, "订单号不存在，请检查后重试")
    return f"订单 {order_id} 状态: {status}"


@tool
def search_products(keyword: str, category: str = "全部") -> str:
    """
    搜索商品

    Args:
        keyword: 搜索关键词
        category: 商品分类

    Returns:
        搜索结果
    """
    # 模拟商品搜索 - 扩展商品库
    products = {
        "手机": [
            "iPhone 15 Pro - ¥8999",
            "iPhone 15 - ¥6999",
            "iPhone 14 Pro - ¥7999",
            "iPhone 14 - ¥5999",
            "小米14 Pro - ¥4999",
            "小米14 - ¥3999",
            "华为Mate60 Pro - ¥7999",
            "华为Mate60 - ¥6999",
            "三星Galaxy S24 - ¥6499",
            "OPPO Find X7 - ¥4999"
        ],
        "电脑": [
            "MacBook Pro M3 - ¥12999",
            "MacBook Air M2 - ¥8999",
            "ThinkPad X1 Carbon - ¥8999",
            "戴尔XPS 13 - ¥7999",
            "华为MateBook X Pro - ¥8499",
            "小米笔记本Pro - ¥5999"
        ],
        "耳机": [
            "AirPods Pro 2 - ¥1999",
            "AirPods 3 - ¥1399",
            "索尼WH-1000XM5 - ¥2299",
            "Bose QC45 - ¥2199",
            "华为FreeBuds Pro 3 - ¥1299",
            "小米Buds 4 Pro - ¥699"
        ]
    }

    results = []
    keyword_lower = keyword.lower()

    # 搜索逻辑优化：支持品牌名、型号、中英文
    for cat, items in products.items():
        # 如果指定了分类，只在该分类中搜索
        if category != "全部" and category not in cat:
            continue

        for item in items:
            item_lower = item.lower()
            # 支持多种搜索方式
            if (keyword_lower in item_lower or
                keyword_lower in cat.lower() or
                any(word in item_lower for word in keyword_lower.split())):
                results.append(item)

    if not results:
        return f"未找到包含'{keyword}'的商品，建议尝试：iPhone、小米、华为、电脑、耳机等关键词"

    return f"搜索'{keyword}'的结果:\n" + "\n".join(f"- {item}" for item in results[:8])


@tool
def process_refund(order_id: str, reason: str) -> str:
    """
    处理退款申请
    
    Args:
        order_id: 订单号
        reason: 退款原因
    
    Returns:
        退款处理结果
    """
    return f"退款申请已提交:\n订单号: {order_id}\n退款原因: {reason}\n预计3-5个工作日内处理完成，退款将原路返回"


# ===== 对话管理类 =====

class ConversationManager:
    """对话管理器"""
    
    def __init__(self):
        self.conversation_id = str(uuid.uuid4())
        self.conversations: List[Dict] = []
        self.team = self._create_customer_service_team()
    
    def _create_customer_service_team(self) -> Team:
        """创建客服团队"""
        
        # 1. 客服总台
        reception_agent = MultiAgent(
            name="Customer Service Reception", # "客服总台"
            instructions="""你是客服总台，负责接待客户并了解需求。

你的职责：
1. 热情接待客户，了解具体需求
2. 根据客户问题类型，分配给合适的专员：
   - 商品咨询、搜索、价格计算 → 商品专员
   - 订单查询、物流跟踪 → 订单专员
   - 退款、退货、售后服务 → 售后专员

请保持专业和友好的态度。如果问题简单，你也可以直接回答。
使用<response>标签包围你的最终回复。""",
            handoff_description="客服总台，负责接待客户并分流到合适的专员"
        )

        # 2. 商品专员
        product_agent = MultiAgent(
            name="Product Specialist", # "商品专员"
            instructions="""你是商品专员，专门处理商品相关咨询。

你的职责：
1. 帮助客户搜索商品
2. 提供商品信息和建议
3. 计算商品价格和优惠
4. 回答商品相关问题

完成服务后，使用<response>标签包围你的最终回复。
如果客户需要其他服务，请转回客服总台。""",
            tools=[search_products, calculate_price],
            handoff_description="商品专员，处理商品咨询、搜索和价格计算"
        )

        # 3. 订单专员
        order_agent = MultiAgent(
            name="Order Specialist", # "订单专员"
            instructions="""你是订单专员，专门处理订单相关问题。

你的职责：
1. 查询订单状态和物流信息
2. 处理订单相关问题
3. 提供配送信息

完成服务后，使用<response>标签包围你的最终回复。
如果客户需要其他服务，请转回客服总台。""",
            tools=[check_order_status],
            handoff_description="订单专员，处理订单查询和物流跟踪"
        )

        # 4. 售后专员
        service_agent = MultiAgent(
            name="After-sales Specialist", # "售后专员"
            instructions="""你是售后专员，专门处理售后服务。

你的职责：
1. 处理退款和退货申请
2. 解决商品质量问题
3. 提供售后支持和建议

完成服务后，使用<response>标签包围你的最终回复。
如果客户需要其他服务，请转回客服总台。""",
            tools=[process_refund],
            handoff_description="售后专员，处理退款、退货和售后服务"
        )
        
        # 设置handoff关系
        reception_agent.handoffs = [product_agent, order_agent, service_agent]
        product_agent.handoffs = [reception_agent]
        order_agent.handoffs = [reception_agent]
        service_agent.handoffs = [reception_agent]
        
        return Team([reception_agent, product_agent, order_agent, service_agent])
    
    def format_conversation_history(self) -> List[Dict]:
        """格式化对话历史为消息列表"""
        messages = []
        for conv in self.conversations:
            messages.append({"content": conv["user"], "role": "user"})
            messages.append({"content": conv["bot"], "role": "assistant"})
        return messages
    
    def chat(self, user_input: str) -> str:
        """处理用户输入并返回回复"""
        try:
            # 获取对话历史
            history = self.format_conversation_history()
            
            # 添加当前用户输入
            history.append({"content": user_input, "role": "user"})
            
            # 运行团队对话
            response = self.team.run(history, max_turns=6)
            
            # 保存对话记录
            self.conversations.append({
                "user": user_input,
                "bot": response
            })
            
            return response
            
        except Exception as e:
            error_msg = f"抱歉，服务暂时不可用: {e}"
            self.conversations.append({
                "user": user_input,
                "bot": error_msg
            })
            return error_msg


def main():
    """主函数 - 交互式客服系统"""
    print("🏪 欢迎使用智能客服系统")
    print("=" * 50)
    print("💡 提示：输入 'exit' 或 'q' 退出系统")
    print("=" * 50)
    
    # 创建对话管理器
    conversation_manager = ConversationManager()
    
    # 欢迎消息
    print("\n🤖 客服：您好！我是智能客服助手，很高兴为您服务！")
    print("我可以帮您：")
    print("  📱 商品咨询和搜索")
    print("  📦 订单查询和跟踪") 
    print("  🔄 退款和售后服务")
    print("请问需要什么帮助？")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 您：").strip()
            
            # 检查退出条件
            if user_input.lower() in ['exit', 'q', '退出', '再见']:
                print("\n🤖 客服：感谢您的使用，祝您生活愉快！再见！👋")
                break
            
            if not user_input:
                print("请输入您的问题...")
                continue
            
            # 处理用户输入
            print("\n🤖 客服：", end="")
            response = conversation_manager.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n🤖 客服：感谢您的使用，再见！")
            break
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")


if __name__ == "__main__":
    main()
