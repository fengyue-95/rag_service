# -*- coding: utf-8 -*-
"""DeepSeek 官方 API 客户端封装

支持：
- deepseek-chat：对话模型
- deepseek-reasoner：推理模型
"""

import os
from pathlib import Path
from typing import List, Optional, Generator, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.chat_model = os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat")
        self.reasoner_model = os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-reasoner")
        
        if not self.api_key:
            raise ValueError("DeepSeek API key 未设置，请在 .env 文件中配置 DEEPSEEK_API_KEY")
    
    def is_available(self) -> bool:
        """检查 API 是否可用"""
        try:
            import requests
            # 使用 /chat/completions 端点测试
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.chat_model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            return response.status_code in [200, 400]  # 400 也说明 API 可达
        except Exception as e:
            print(f"DeepSeek API 不可用: {str(e)}")
            return False
    
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """发起 API 请求"""
        import requests
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=120)
        
        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", response.text)
            raise Exception(f"DeepSeek API 错误: {error_msg}")
        
        return response.json()


class DeepSeekChat:
    """DeepSeek 对话模型 (deepseek-chat)"""
    
    def __init__(self, model_name: str = None):
        self.client = DeepSeekClient()
        self.model_name = model_name or self.client.chat_model
    
    def chat(self, message: str, context: str = None, stream: bool = False) -> str:
        """发送对话消息
        
        Args:
            message: 用户消息
            context: 上下文信息（用于 RAG）
            stream: 是否流式输出
        
        Returns:
            AI 回复内容
        """
        messages = []
        
        # 添加系统提示 - 要求用中文
        system_prompt = "你是一个智能助手，请始终用中文回答用户的问题。"
        
        if context:
            system_prompt += f"\n\n请根据以下上下文信息回答用户的问题。如果上下文中没有相关信息，再基于你的知识回答。\n\n上下文：\n{context}"
        
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream
        }
        
        response = self.client._make_request("/chat/completions", data)
        
        return response["choices"][0]["message"]["content"]
    
    def chat_stream(self, message: str, context: str = None) -> Generator[str, None, None]:
        """流式对话"""
        messages = []
        
        if context:
            messages.append({
                "role": "system",
                "content": f"根据以下上下文信息回答用户的问题。\n\n上下文：\n{context}"
            })
        
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": True
        }
        
        import requests
        
        url = f"{self.client.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=120)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        import json
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content


class DeepSeekReasoner:
    """DeepSeek 推理模型 (deepseek-reasoner)"""
    
    def __init__(self, model_name: str = None):
        self.client = DeepSeekClient()
        self.model_name = model_name or self.client.reasoner_model
    
    def reason(self, problem: str, context: str = None) -> str:
        """推理问题
        
        Args:
            problem: 问题描述
            context: 上下文信息
        
        Returns:
            推理结果和答案
        """
        messages = []
        
        # 系统提示
        system_prompt = """你是一个推理模型。请对问题进行深入分析和推理，逐步思考后将答案输出到<answer>标签中。

推理格式要求：
1. 先分析问题的关键点
2. 逐步推理
3. 最后在<answer>标签中给出最终答案"""
        
        if context:
            system_prompt += f"\n\n参考上下文：\n{context}"
        
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": problem})
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }
        
        response = self.client._make_request("/chat/completions", data)
        
        return response["choices"][0]["message"]["content"]
    
    def reason_with_thought(self, problem: str, context: str = None) -> Dict[str, str]:
        """推理问题，返回思考过程和答案"""
        result = self.reason(problem, context)
        
        # 分离思考过程和答案
        thought = ""
        answer = ""
        
        if "<answer>" in result:
            parts = result.split("<answer>")
            thought = parts[0].strip()
            answer = parts[1].replace("</answer>", "").strip() if len(parts) > 1 else ""
        else:
            thought = result
            answer = result
        
        return {
            "thought": thought,
            "answer": answer,
            "full_response": result
        }


# DeepSeek 嵌入模型（如果官方支持）
class DeepSeekEmbedding:
    """DeepSeek 嵌入模型"""
    
    def __init__(self, model_name: str = "deepseek-embedding"):
        self.client = DeepSeekClient()
        self.model_name = model_name
    
    def embed(self, text: str) -> List[float]:
        """生成文本嵌入"""
        # DeepSeek 官方 API 目前可能不支持嵌入
        # 如果需要嵌入，可以使用其他服务（如 OpenAI、阿里云等）
        # 这里返回空列表作为占位
        print("DeepSeek 官方 API 暂不支持嵌入功能，请使用本地 Ollama 嵌入模型")
        return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入"""
        return [self.embed(text) for text in texts if self.embed(text)]


# 便捷函数
def get_deepseek_chat(model_name: str = None) -> DeepSeekChat:
    """获取 DeepSeek 对话模型实例"""
    return DeepSeekChat(model_name)


def get_deepseek_reasoner(model_name: str = None) -> DeepSeekReasoner:
    """获取 DeepSeek 推理模型实例"""
    return DeepSeekReasoner(model_name)


def get_deepseek_embedding(model_name: str = "deepseek-embedding") -> DeepSeekEmbedding:
    """获取 DeepSeek 嵌入模型实例"""
    return DeepSeekEmbedding(model_name)


# 可用的 DeepSeek 模型配置
DEEPSEEK_MODELS = {
    "chat": {
        "default": "deepseek-chat",
        "options": ["deepseek-chat"]
    },
    "reasoner": {
        "default": "deepseek-reasoner",
        "options": ["deepseek-reasoner"]
    },
    "embedding": {
        "default": "deepseek-embedding",
        "options": []  # 暂不支持
    }
}


if __name__ == "__main__":
    # 测试 DeepSeek API
    print("=" * 50)
    print("DeepSeek API 测试")
    print("=" * 50)
    
    try:
        client = DeepSeekClient()
        
        if client.is_available():
            print("✅ DeepSeek API 连接成功")
            
            # 测试对话
            chat_model = DeepSeekChat()
            print("\n测试对话:")
            response = chat_model.chat("你好，请简单介绍一下你自己")
            print(f"回答: {response[:100]}...")
            
            # 测试推理
            reasoner = DeepSeekReasoner()
            print("\n测试推理:")
            response = reasoner.reason("为什么天空是蓝色的？")
            print(f"推理结果: {response[:200]}...")
        else:
            print("❌ DeepSeek API 连接失败")
            
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
