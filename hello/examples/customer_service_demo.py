# @file: customer_service_demo.py
# @date: 2025/01/15
# @author: jiaohui
# @description: 客服系统多Agent协作演示

import sys
import os

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


# ===== Agent定义 =====

def create_customer_service_team():
    """创建客服团队"""
    
    # 1. 客服总台 - 负责接待和分流
    reception_agent = MultiAgent(
        name="Customer Service Reception", # "客服总台"
        instructions="""你是客服总台，负责接待客户并了解需求。

你的职责：
1. 热情接待客户，了解具体需求
2. 根据客户问题类型，分配给合适的专员：
   - 商品咨询 → 商品专员
   - 订单查询 → 订单专员  
   - 售后服务 → 售后专员
   - 价格计算 → 商品专员

请保持专业和友好的态度。""",
        handoff_description="客服总台，负责接待客户并分流到合适的专员"
    )
    
    # 2. 商品专员 - 负责商品咨询和价格计算
    product_agent = MultiAgent(
        name="Product Specialist", # "商品专员"
        instructions="""你是商品专员专门处理商品相关咨询。

你的职责：
1. 帮助客户搜索商品
2. 提供商品信息和建议
3. 计算商品价格和优惠
4. 回答商品相关问题

如果客户需要其他服务，请转回客服总台。""",
        tools=[search_products, calculate_price],
        handoff_description="商品专员，处理商品咨询、搜索和价格计算"
    )
    
    # 3. 订单专员 - 负责订单查询和跟踪
    order_agent = MultiAgent(
        name="After-sales Specialist", # "订单专员"
        instructions="""你是订单专员，专门处理订单相关问题。

你的职责：
1. 查询订单状态和物流信息
2. 处理订单相关问题
3. 提供配送信息

如果客户需要其他服务，请转回客服总台。""",
        tools=[check_order_status],
        handoff_description="订单专员，处理订单查询和物流跟踪"
    )
    
    # 4. 售后专员 - 负责退换货和售后服务
    service_agent = MultiAgent(
        name="售后专员", 
        instructions="""你是售后专员，专门处理售后服务。

你的职责：
1. 处理退款和退货申请
2. 解决商品质量问题
3. 提供售后支持和建议

如果客户需要其他服务，请转回客服总台。""",
        tools=[process_refund],
        handoff_description="售后专员，处理退款、退货和售后服务"
    )
    
    # 设置handoff关系
    reception_agent.handoffs = [product_agent, order_agent, service_agent]
    product_agent.handoffs = [reception_agent]
    order_agent.handoffs = [reception_agent]
    service_agent.handoffs = [reception_agent]
    
    # 创建团队
    team = Team([reception_agent, product_agent, order_agent, service_agent])
    
    return team


def main():
    """主函数 - 演示客服系统"""
    print("🏪 欢迎使用智能客服系统演示")
    print("=" * 50)
    
    # 创建客服团队
    team = create_customer_service_team()
    
    # 测试案例 - 包含interactive的常见问题
    test_cases = [
        "你好，我想买一个手机",
        "帮我搜索iPhone",
        "我想要iPhone，帮我搜索一下",
        "请帮我查询订单12345的状态",
        "帮我查询订单12345的状态",
        "我要申请退款，订单号是67890，商品有质量问题",
        "iPhone 15 Pro现在多少钱？如果打8折是多少？",
        "搜索一下小米手机",
        "华为电脑有哪些？",
        "AirPods多少钱？",
        "订单67890什么时候发货？",
        "我想退货，订单11111有问题"
    ]
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n🔸 客户咨询 {i}: {question}")
        print("-" * 40)
        
        try:
            result = team.run(question, max_turns=8)
            print(f"✅ 服务结果: {result}")
        except Exception as e:
            print(f"❌ 服务异常: {e}")
        
        print("=" * 50)


if __name__ == "__main__":
    main()
