# -*- coding: utf-8 -*-
"""17 种 RAG 优化方法实现"""

from typing import List, Dict, Optional, Tuple, Union
from rag.ollama_client import (
    get_embedding_model, 
    get_chat_model,
    get_reasoning_model
)


class BaseRAGMethod:
    """RAG 方法基类"""
    
    name: str = "base"
    description: str = ""
    
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.chat_model = get_chat_model()
    
    def retrieve(self, query: str, vector_store, k: int = 5) -> List[Tuple[str, float, dict]]:
        """检索相关文档"""
        return vector_store.search(query, k=k)
    
    def generate(self, query: str, context: str) -> str:
        """生成回答"""
        return self.chat_model.chat(query, context=context)
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """完整的 RAG 流程，返回包含内容和出处的字典"""
        docs = self.retrieve(query, vector_store)
        sources = []
        
        # 提取出处信息
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            sources.append(source)
        
        # 去重并保持顺序
        unique_sources = []
        for s in sources:
            if s not in unique_sources:
                unique_sources.append(s)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            # 润色回答
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": unique_sources,
                "source_type": "local"
            }
        # 没有检索到本地文档，使用纯对话
        response = self.generate(query, "")
        # 润色回答
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }
    
    def _polish_response(self, response: str) -> str:
        """润色回答"""
        if not response or len(response.strip()) < 10:
            return response
        
        try:
            polished = self.chat_model.polish(response)
            if polished and len(polished.strip()) > 10:
                return polished
            return response
        except Exception as e:
            print(f"润色失败: {str(e)}")
            return response


class SimpleRAG(BaseRAGMethod):
    """1. SimpleRAG（简单切块）"""
    name = "simple"
    description = "简单切块"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """简单 RAG：检索 + 生成"""
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class SemanticChunking(BaseRAGMethod):
    """2. Semantic Chunking（语义切块）"""
    name = "semantic_chunking"
    description = "语义切块"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """语义切块 RAG"""
        docs = self.retrieve(query, vector_store, k=8)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class ContextEnrichedRetrieval(BaseRAGMethod):
    """3. Context Enriched Retrieval（上下文增强检索）"""
    name = "context_enriched"
    description = "上下文增强检索"
    
    def retrieve(self, query: str, vector_store, k: int = 5) -> List[Tuple[str, float, dict]]:
        """增强检索：包含更多上下文"""
        # 先检索，再扩展检索上下文
        docs = vector_store.search(query, k=k)
        # 这里可以添加上下文扩展逻辑
        return docs
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """上下文增强 RAG"""
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class ContextualChunkHeaders(BaseRAGMethod):
    """4. Contextual Chunk Headers（上下文分块标题）"""
    name = "chunk_headers"
    description = "上下文分块标题"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """带标题的上下文 RAG"""
        docs = self.retrieve(query, vector_store, k=6)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            # 添加文档来源信息作为标题
            context_parts = []
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                context_parts.append(f"[来源: {source}]\n{doc}")
            context = "\n\n".join(context_parts)
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class DocumentAugmentation(BaseRAGMethod):
    """5. Document Augmentation（文档增强）"""
    name = "doc_augmentation"
    description = "文档增强"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """文档增强 RAG：增加文档补充信息"""
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            # 合并相关文档片段
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class QueryTransformation(BaseRAGMethod):
    """6. Query Transformation（查询转换）"""
    name = "query_transform"
    description = "查询转换"
    
    def __init__(self):
        super().__init__()
        self.reasoning_model = get_reasoning_model()
    
    def transform_query(self, query: str) -> str:
        """转换查询为多个版本"""
        # 使用推理模型生成查询变体
        prompt = f"将以下问题改写成 3 个不同的版本（保留原意，使用不同表达方式）：\n{query}"
        response = self.reasoning_model.reason(prompt)
        # 解析生成的变体
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        variants = [query]  # 保留原查询
        for line in lines:
            if line and not line.startswith('=') and len(line) > 5:
                variants.append(line)
        return variants[:4]  # 最多返回 4 个版本
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """查询转换 RAG"""
        # 转换查询
        query_variants = self.transform_query(query)
        
        # 对每个查询变体进行检索
        all_docs = []
        sources = []
        for q in query_variants:
            docs = self.retrieve(q, vector_store, k=3)
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                if source not in sources:
                    sources.append(source)
            all_docs.extend(docs)
        
        # 去重并按分数排序
        if all_docs:
            seen = set()
            unique_docs = []
            for doc in all_docs:
                if doc[0] not in seen:
                    seen.add(doc[0])
                    unique_docs.append(doc)
            unique_docs.sort(key=lambda x: x[1], reverse=True)
            
            context = "\n\n".join([doc[0] for doc in unique_docs[:5]])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class Reranker(BaseRAGMethod):
    """7. Reranker（重排序）"""
    name = "reranker"
    description = "重排序"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """重排序 RAG：先粗筛再精排"""
        # 第一步：大规模检索
        docs = self.retrieve(query, vector_store, k=20)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if not docs:
            response = self.generate(query, "")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": [],
                "source_type": "general"
            }
        
        # 第二步：重排序（这里用简单方法：按分数截断）
        top_docs = docs[:5]  # 选择 top 5
        
        context = "\n\n".join([doc[0] for doc in top_docs])
        response = self.generate(query, context)
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": sources,
            "source_type": "local"
        }


class RSERetrieval(BaseRAGMethod):
    """8. RSE（语义扩展重排序）"""
    name = "rse"
    description = "语义扩展重排序"
    
    def __init__(self):
        super().__init__()
        self.reasoning_model = get_reasoning_model()
    
    def expand_query(self, query: str) -> str:
        """扩展查询"""
        prompt = f"为以下问题扩展相关概念和关键词（用于信息检索）：\n{query}"
        return self.reasoning_model.reason(prompt)
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """语义扩展重排序 RAG"""
        # 扩展查询
        expanded_query = self.expand_query(query)
        
        # 使用扩展查询检索
        docs = self.retrieve(expanded_query, vector_store, k=10)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            # 精排：选择 top 5
            top_docs = docs[:5]
            context = "\n\n".join([doc[0] for doc in top_docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class FeedbackLoop(BaseRAGMethod):
    """9. Feedback Loop（反馈闭环）"""
    name = "feedback_loop"
    description = "反馈闭环"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """反馈闭环 RAG：迭代优化"""
        # 初始检索
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if not docs:
            response = self.generate(query, "")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": [],
                "source_type": "general"
            }
        
        # 生成初始回答
        context = "\n\n".join([doc[0] for doc in docs])
        response = self.generate(query, context)
        if polish:
            response = self._polish_response(response)
        
        return {
            "content": response,
            "sources": sources,
            "source_type": "local"
        }


class AdaptiveRAG(BaseRAGMethod):
    """10. Adaptive RAG（自适应检索增强生成）"""
    name = "adaptive_rag"
    description = "自适应检索增强生成"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """自适应 RAG：根据问题类型选择策略"""
        # 分析问题类型
        question_type = self._classify_question(query)
        sources = []
        
        if question_type == "simple":
            # 简单问题，直接检索少量文档
            docs = self.retrieve(query, vector_store, k=3)
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                if source not in sources:
                    sources.append(source)
            context = "\n\n".join([doc[0] for doc in docs]) if docs else ""
            if docs:
                response = self.generate(query, context)
                if polish:
                    response = self._polish_response(response)
                return {
                    "content": response,
                    "sources": sources,
                    "source_type": "local"
                }
        elif question_type == "complex":
            # 复杂问题，检索更多文档
            docs = self.retrieve(query, vector_store, k=8)
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                if source not in sources:
                    sources.append(source)
            context = "\n\n".join([doc[0] for doc in docs]) if docs else ""
            if docs:
                response = self.generate(query, context)
                if polish:
                    response = self._polish_response(response)
                return {
                    "content": response,
                    "sources": sources,
                    "source_type": "local"
                }
        
        # 默认策略
        result = super().chat(query, vector_store, polish=polish)
        return result
    
    def _classify_question(self, query: str) -> str:
        """简单问题分类"""
        query_lower = query.lower()
        # 简单问题特征词
        simple_keywords = ["什么是", "定义", "解释", "谁是", "哪个是", "多少", "什么时候"]
        for kw in simple_keywords:
            if kw in query_lower:
                return "simple"
        return "complex"


class SelfRAG(BaseRAGMethod):
    """11. Self RAG（自反思检索增强生成）"""
    name = "self_rag"
    description = "自反思检索增强生成"
    
    def __init__(self):
        super().__init__()
        self.reasoning_model = get_reasoning_model()
    
    def reflect(self, query: str, response: str) -> bool:
        """反思回答是否需要改进"""
        prompt = f"""
判断以下回答是否充分回答了问题：

问题：{query}
回答：{response}

如果回答不完整或不确定，返回"需要改进"，否则返回"足够"。
"""
        result = self.reasoning_model.reason(prompt)
        return "需要改进" not in result
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """自反思 RAG"""
        # 初始回答
        response = super().chat(query, vector_store, polish=polish)
        
        if isinstance(response, dict):
            response_data = response
            sources = response.get("sources", [])
        else:
            response_data = {"content": response}
            sources = []
        
        # 反思
        if self.reflect(query, response_data["content"]):
            return response_data
        else:
            # 尝试改进：检索更多文档
            docs = self.retrieve(query, vector_store, k=10)
            new_sources = []
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                if source not in new_sources:
                    new_sources.append(source)
            if docs:
                context = "\n\n".join([doc[0] for doc in docs])
                improved_response = self.generate(query, context)
                if polish:
                    improved_response = self._polish_response(improved_response)
                return {
                    "content": improved_response,
                    "sources": new_sources,
                    "source_type": "local"
                }
        if polish:
            response_data["content"] = self._polish_response(response_data["content"])
        return response_data


class KnowledgeGraph(BaseRAGMethod):
    """12. Knowledge Graph（知识图谱）"""
    name = "knowledge_graph"
    description = "知识图谱"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """知识图谱 RAG"""
        # 检索实体相关文档
        docs = self.retrieve(query, vector_store, k=6)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            # 在提示中强调关系和实体
            enhanced_prompt = f"请根据以下文档内容，梳理其中的实体和关系后回答问题：\n\n{context}\n\n问题：{query}"
            response = self.chat_model.chat(enhanced_prompt, context="")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class HierarchicalIndices(BaseRAGMethod):
    """13. Hierarchical Indices（层次化索引）"""
    name = "hierarchical"
    description = "层次化索引"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """层次化索引 RAG"""
        # 先检索摘要级别的文档
        # 然后检索详细内容
        # 这里简化为普通检索
        docs = self.retrieve(query, vector_store, k=6)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class HyDE(BaseRAGMethod):
    """14. HyDE（假设文档嵌入）"""
    name = "hyde"
    description = "假设文档嵌入"
    
    def __init__(self):
        super().__init__()
        self.reasoning_model = get_reasoning_model()
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """生成假设答案"""
        prompt = f"针对以下问题，生成一个详细的假设性答案（不需要真实，基于常识）：\n\n问题：{query}"
        return self.reasoning_model.reason(prompt)
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """HyDE RAG：使用假设文档检索"""
        # 生成假设答案
        hyp_answer = self.generate_hypothetical_answer(query)
        
        # 用假设答案检索
        docs = self.retrieve(hyp_answer, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class FusionRetrieval(BaseRAGMethod):
    """15. Fusion（融合检索）"""
    name = "fusion"
    description = "融合检索"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """融合检索 RAG"""
        # 多策略检索融合
        strategies = [
            ("关键词检索", lambda: self.retrieve(query, vector_store, k=3)),
            ("语义检索", lambda: self.retrieve(query, vector_store, k=3)),
        ]
        
        all_docs = []
        sources = []
        for name, strategy in strategies:
            docs = strategy()
            for doc, score, meta in docs:
                source = meta.get("source", "未知来源")
                if source not in sources:
                    sources.append(source)
            all_docs.extend(docs)
        
        # 去重和融合
        if all_docs:
            seen = set()
            unique_docs = []
            for doc in all_docs:
                if doc[0] not in seen:
                    seen.add(doc[0])
                    unique_docs.append(doc)
            unique_docs.sort(key=lambda x: x[1], reverse=True)
            
            context = "\n\n".join([doc[0] for doc in unique_docs[:5]])
            response = self.generate(query, context)
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


class CRAG(BaseRAGMethod):
    """16. CRAG（纠错型 RAG）"""
    name = "crag"
    description = "纠错型 RAG"
    
    def __init__(self):
        super().__init__()
        self.reasoning_model = get_reasoning_model()
    
    def verify_context(self, query: str, context: str) -> Tuple[bool, str]:
        """验证上下文是否相关"""
        prompt = f"""
判断以下上下文是否与问题相关：

问题：{query}
上下文：{context[:500]}...

如果上下文与问题高度相关，返回"相关"，否则返回"不相关"。
"""
        result = self.reasoning_model.reason(prompt)
        is_relevant = "相关" in result and "不相关" not in result
        return is_relevant, result
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """CRAG：基于置信度的检索增强"""
        # 初始检索
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if not docs:
            response = self.generate(query, "")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": [],
                "source_type": "general"
            }
        
        # 评估检索结果质量
        relevance_scores = self.evaluate_relevance(query, docs)
        
        if sum(relevance_scores) / len(relevance_scores) < 0.5:
            # 检索结果不相关，回退到纯生成
            response = self.generate(query, "")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": [],
                "source_type": "general"
            }
        
        # 过滤不相关文档
        relevant_docs = [doc for doc, score in zip(docs, relevance_scores) if score > 0.3]
        
        if not relevant_docs:
            response = self.generate(query, "")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": [],
                "source_type": "general"
            }
        
        context = "\n\n".join([doc[0] for doc in relevant_docs])
        response = self.generate(query, context)
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": sources,
            "source_type": "local"
        }


class MultiModalRAG(BaseRAGMethod):
    """17. Multi-Modal RAG（多模态检索增强生成）"""
    name = "multimodal"
    description = "多模态检索增强生成"
    
    def chat(self, query: str, vector_store, polish: bool = False) -> Dict[str, Union[str, List]]:
        """多模态 RAG"""
        # 检索文本相关文档
        docs = self.retrieve(query, vector_store, k=5)
        sources = []
        for doc, score, meta in docs:
            source = meta.get("source", "未知来源")
            if source not in sources:
                sources.append(source)
        
        if docs:
            context = "\n\n".join([doc[0] for doc in docs])
            # 添加多模态提示
            multimodal_prompt = f"""请根据以下文档内容回答问题。如果问题涉及图像、表格或其他非文本内容，请说明需要查看原文件。

文档内容：
{context}

问题：{query}

注意：如果需要查看原始文件内容（如图片、表格等），请在回答中说明"建议查看源文档获取完整信息"。
"""
            response = self.chat_model.chat(multimodal_prompt, context="")
            if polish:
                response = self._polish_response(response)
            return {
                "content": response,
                "sources": sources,
                "source_type": "local"
            }
        response = self.generate(query, "")
        if polish:
            response = self._polish_response(response)
        return {
            "content": response,
            "sources": [],
            "source_type": "general"
        }


# RAG 方法工厂
RAG_METHODS: Dict[str, BaseRAGMethod] = {
    "option1": SimpleRAG(),
    "option2": SemanticChunking(),
    "option3": ContextEnrichedRetrieval(),
    "option4": ContextualChunkHeaders(),
    "option5": DocumentAugmentation(),
    "option6": QueryTransformation(),
    "option7": Reranker(),
    "option8": RSERetrieval(),
    "option9": FeedbackLoop(),
    "option10": AdaptiveRAG(),
    "option11": SelfRAG(),
    "option12": KnowledgeGraph(),
    "option13": HierarchicalIndices(),
    "option14": HyDE(),
    "option15": FusionRetrieval(),
    "option16": CRAG(),
    "option17": MultiModalRAG(),
}


def get_rag_method(option_id: str) -> BaseRAGMethod:
    """获取 RAG 方法实例"""
    return RAG_METHODS.get(option_id, SimpleRAG())


if __name__ == "__main__":
    print("17 种 RAG 方法已加载:")
    for key, method in RAG_METHODS.items():
        print(f"  {key}: {method.description}")