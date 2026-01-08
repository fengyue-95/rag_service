"""Ollama 客户端封装

支持本地 Ollama 的多种模型：
- 嵌入模型：用于将文本转换为向量
- 对话模型：用于生成回答
- OCR 模型：用于图像文字识别
"""

import json
import requests
from typing import List, Optional, Union
from pathlib import Path


# Ollama 默认配置
DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaClient:
    """Ollama 客户端"""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Ollama 服务不可用: {str(e)}")
            return False
    
    def list_models(self) -> List[str]:
        """列出所有可用的模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            print(f"获取模型列表失败: {str(e)}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """拉取模型"""
        try:
            response = requests.post(
                f"{self.api_url}/pull",
                json={"name": model_name},
                stream=True,
                timeout=300
            )
            return response.status_code == 200
        except Exception as e:
            print(f"拉取模型失败: {str(e)}")
            return False


class EmbeddingModel:
    """嵌入模型封装"""
    
    def __init__(self, model_name: str = "qwen3-embedding:8b", base_url: str = DEFAULT_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.client = OllamaClient(base_url)
    
    def embed(self, text: str) -> List[float]:
        """将单段文本转换为向量"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model_name,
                    "prompt": text
                },
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [])
            else:
                print(f"嵌入失败: {response.text}")
                return []
        except Exception as e:
            print(f"嵌入请求失败: {str(e)}")
            return []
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        embeddings = []
        for text in texts:
            embedding = self.embed(text)
            if embedding:
                embeddings.append(embedding)
            else:
                print(f"文本嵌入失败: {text[:50]}...")
        return embeddings


class ChatModel:
    """对话模型封装"""
    
    def __init__(self, model_name: str = "llama3:latest", base_url: str = DEFAULT_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.client = OllamaClient(base_url)
    
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """发送对话消息"""
        try:
            messages = [{"role": "user", "content": message}]
            
            # 如果有上下文，添加到系统提示
            if context:
                system_prompt = """你是一个智能助手，请根据以下上下文回答用户的问题。

要求：
1. 始终用中文回答
2. 如果上下文中有相关信息，优先使用上下文
3. 回答要简洁明了

上下文："""
                system_prompt += context
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            else:
                # 没有上下文时也要求用中文
                messages = [{"role": "system", "content": "请用中文回答用户的问题"}, {"role": "user", "content": message}]
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                print(f"对话失败: {response.text}")
                return ""
        except Exception as e:
            print(f"对话请求失败: {str(e)}")
            return ""
    
    def chat_stream(self, message: str, context: Optional[str] = None):
        """流式对话"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": message}],
                "stream": True
            }
            
            if context:
                payload["system"] = f"根据以下上下文回答问题:\n\n{context}"
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    yield content
                    
        except Exception as e:
            print(f"流式对话失败: {str(e)}")
    
    def polish(self, text: str) -> str:
        """润色文本，使其更流畅自然
        
        Args:
            text: 原始文本
        
        Returns:
            润色后的文本
        """
        try:
            prompt = f"""请对以下文本进行润色，使其语言更流畅自然，表达更准确专业。

要求：
1. 保持原意不变
2. 语言更流畅自然
3. 修正语法和表达错误
4. 适当优化句式结构

原文：
{text}

润色后的文本："""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "你是一个专业的文字润色助手，请用中文润色文本，保持原意，使语言更流畅自然。"},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                polished = data.get("message", {}).get("content", "")
                # 如果润色结果太短或为空，返回原文
                if polished and len(polished.strip()) > 10:
                    return polished.strip()
                return text
            else:
                print(f"润色失败: {response.text}")
                return text
        except Exception as e:
            print(f"润色请求失败: {str(e)}")
            return text


class OCRModel:
    """OCR 模型封装"""
    
    def __init__(self, model_name: str = "deepseek-ocr:latest", base_url: str = DEFAULT_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.client = OllamaClient(base_url)
    
    def ocr(self, image_path: str) -> str:
        """识别图片中的文字"""
        try:
            import base64
            
            # 读取图片并转为 base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "model": self.model_name,
                "prompt": "请识别图片中的所有文字，保持原有格式",
                "images": [image_data]
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                print(f"OCR 失败: {response.text}")
                return ""
        except Exception as e:
            print(f"OCR 请求失败: {str(e)}")
            return ""


class ReasoningModel:
    """推理模型封装（DeepSeek R1 等）"""
    
    def __init__(self, model_name: str = "deepseek-r1:8b", base_url: str = DEFAULT_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url
        self.client = OllamaClient(base_url)
    
    def reason(self, problem: str, context: Optional[str] = None) -> str:
        """推理问题"""
        try:
            prompt = problem
            if context:
                prompt = f"上下文信息:\n{context}\n\n问题:\n{problem}\n\n请先推理分析，再给出答案。"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                print(f"推理失败: {response.text}")
                return ""
        except Exception as e:
            print(f"推理请求失败: {str(e)}")
            return ""


# 预定义的模型配置
AVAILABLE_MODELS = {
    # 嵌入模型
    "embedding": {
        "default": "qwen3-embedding:8b",
        "options": ["qwen3-embedding:8b"]
    },
    
    # 对话模型
    "chat": {
        "default": "llama3:latest",
        "options": ["llama3:latest", "qwen3:8b", "qwen2.5:7b", "deepseek-r1:8b"]
    },
    
    # OCR 模型
    "ocr": {
        "default": "deepseek-ocr:latest",
        "options": ["deepseek-ocr:latest"]
    },
    
    # 推理模型
    "reasoning": {
        "default": "deepseek-r1:8b",
        "options": ["deepseek-r1:8b"]
    }
}


def get_embedding_model(model_name: str = None) -> EmbeddingModel:
    """获取嵌入模型实例"""
    if model_name is None:
        model_name = AVAILABLE_MODELS["embedding"]["default"]
    return EmbeddingModel(model_name)


def get_chat_model(model_name: str = None) -> ChatModel:
    """获取对话模型实例"""
    if model_name is None:
        model_name = AVAILABLE_MODELS["chat"]["default"]
    return ChatModel(model_name)


def get_ocr_model(model_name: str = None) -> OCRModel:
    """获取 OCR 模型实例"""
    if model_name is None:
        model_name = AVAILABLE_MODELS["ocr"]["default"]
    return OCRModel(model_name)


def get_reasoning_model(model_name: str = None) -> ReasoningModel:
    """获取推理模型实例"""
    if model_name is None:
        model_name = AVAILABLE_MODELS["reasoning"]["default"]
    return ReasoningModel(model_name)


if __name__ == "__main__":
    # 测试 Ollama 连接
    client = OllamaClient()
    
    print("=" * 50)
    print("Ollama 模型管理工具")
    print("=" * 50)
    
    if client.is_available():
        print("✅ Ollama 服务已连接")
        
        models = client.list_models()
        print(f"\n可用模型 ({len(models)} 个):")
        for model in models:
            print(f"  - {model}")
    else:
        print("❌ Ollama 服务未连接，请确保 Ollama 已启动")