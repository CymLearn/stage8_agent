# -*- coding: utf-8 -*-
from fastmcp import FastMCP
import re


mcp = FastMCP("math_mcp")

def _normalize_expression(text: str) -> str:
    """Normalize input to a strict arithmetic expression.
    """
    t = text.replace("×", "*").replace("÷", "/")

    allowed = set("0123456789.+-*/() % ")
    cleaned = []
    for ch in t:
        if ch in allowed:
            cleaned.append(ch)

    expr = ''.join(cleaned)
    expr = re.sub(r"\s+", " ", expr).strip()
    return expr


@mcp.tool
def math(question: str) -> int | float:
    """Solve a natural-language arithmetic question, e.g. "what's (3 + 5) x 12?".
    Returns a number; integers are returned without a decimal.
    """
    # 安全性：限制输入长度以防止拒绝服务攻击s
    if len(question) > 1000:
        raise ValueError("Input too long. Maximum 1000 characters allowed.")
    
    expr = _normalize_expression(question)
    if not expr:
        raise ValueError("No arithmetic expression found in input")
    
    # 规范化后进一步限制表达式长度 
    if len(expr) > 200:
        raise ValueError("Expression too complex after normalization")
    
    try:
        """使用python的eval工具来执行数学运算"""
        result = eval(expr)

    except Exception as e:
        raise ValueError(f"Failed to evaluate expression: {expr}") from e

    # Return int if it is an integer value, else float
    if isinstance(result, float) and result.is_integer():
        return int(result)
    return result


if __name__ == "__main__":
    mcp.run()
