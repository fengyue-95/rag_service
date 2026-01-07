# -*- coding: utf-8 -*-
"""向量存储模块

使用 FAISS 进行向量存储和检索
"""

import json

import faiss
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from rag.ollama_client import get_embedding_model


class VectorStore:
    """向量存储类"""
    
    def __init__(self, index_dir: str = "indexes", embedding_model_name: str = None):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        
        # 嵌入模型
        self.embedding_model = get_embedding_model(embedding_model_name)
        
        # FAISS 索引（延迟加载）
        self._index = None
        self._documents = []  # 原始文档
        self._metadatas = []  # 元数据
    
    @property
    def index(self):
        """懒加载 FAISS 索引"""
        if self._index is None:
            self._load_index()
        return self._index
    
    def _get_store_file(self, store_name: str) -> Path:
        """获取存储文件路径"""
        return self.index_dir / f"{store_name}.store"
    
    def _get_faiss_index_file(self, store_name: str) -> Path:
        """获取 FAISS 索引文件路径"""
        return self.index_dir / f"{store_name}.faiss"
    
    def _init_index(self, dimension: int):
        """初始化 FAISS 索引"""
        try:
            import faiss
            # 使用内积索引（归一化向量）
            self._index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
            self._documents = []
            self._metadatas = []
        except ImportError:
            print("FAISS 未安装，将使用简单向量存储")
            self._index = None
    
    def _load_index(self):
        """加载已存在的索引"""
        store_file = self._get_store_file("default")
        faiss_file = self._get_faiss_index_file("default")
        
        if faiss_file.exists() and store_file.exists():
            try:
                import faiss
                
                # 加载 FAISS 索引
                self._index = faiss.read_index(str(faiss_file))
                
                # 加载文档和元数据
                with open(store_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._documents = data.get("documents", [])
                    self._metadatas = data.get("metadatas", [])
                
                print(f"加载索引成功: {len(self._documents)} 个文档块")
            except ImportError:
                print("FAISS 未安装，无法加载向量索引")
            except Exception as e:
                print(f"加载索引失败: {str(e)}")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        store_name: str = "default"
    ):
        """添加文档到向量存储
        
        Args:
            texts: 文档文本列表
            metadatas: 元数据列表
            store_name: 存储名称
        """
        if not texts:
            return
        
        print(f"正在处理 {len(texts)} 个文档块...")
        
        # 获取向量维度
        if self._index is None and len(texts) > 0:
            # 用第一条数据测试维度
            test_embedding = self.embedding_model.embed(texts[0])
            if test_embedding:
                dimension = len(test_embedding)
                self._init_index(dimension)
                print(f"初始化向量索引，维度: {dimension}")
        
        if self._index is None:
            print("向量索引未初始化，跳过添加")
            return
        
        # 批量生成嵌入
        embeddings = self.embedding_model.embed_batch(texts)
        
        if not embeddings:
            print("生成嵌入失败")
            return
        
        # 添加到索引
        ids = list(range(len(self._documents), len(self._documents) + len(embeddings)))
        
        # 转换为 numpy 数组
        embeddings_array = np.array(embeddings).astype('float32')
        
        # 归一化向量（用于余弦相似度）
        faiss.normalize_L2(embeddings_array)
        
        self._index.add_with_ids(embeddings_array, np.array(ids))
        
        # 添加文档和元数据
        self._documents.extend(texts)
        if metadatas:
            self._metadatas.extend(metadatas)
        else:
            self._metadatas.extend([{}] * len(texts))
        
        # 保存索引
        self.save_index(store_name)
        
        print(f"成功添加 {len(texts)} 个文档块到索引")
    
    def save_index(self, store_name: str = "default"):
        """保存索引到磁盘"""
        if self._index is None:
            return
        
        try:
            import faiss
            
            # 保存 FAISS 索引
            faiss_file = self._get_faiss_index_file(store_name)
            faiss.write_index(self._index, str(faiss_file))
            
            # 保存文档和元数据
            store_file = self._get_store_file(store_name)
            data = {
                "documents": self._documents,
                "metadatas": self._metadatas
            }
            with open(store_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"索引已保存: {faiss_file}")
        except ImportError:
            print("FAISS 未安装，无法保存索引")
        except Exception as e:
            print(f"保存索引失败: {str(e)}")
    
    def search(
        self,
        query: str,
        k: int = 5,
        store_name: str = None
    ) -> List[Tuple[str, float, dict]]:
        """搜索相似文档
        
        Args:
            query: 查询文本
            k: 返回结果数量
            store_name: 存储名称
        
        Returns:
            [(文档内容, 相似度分数, 元数据), ...]
        """
        if self._index is None:
            self._load_index()
        
        if self._index is None or self._index.ntotal == 0:
            print("索引为空或未初始化")
            return []
        
        # 生成查询向量
        query_embedding = self.embedding_model.embed(query)
        if not query_embedding:
            print("生成查询向量失败")
            return []
        
        query_array = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_array)
        
        # 搜索
        scores, indices = self._index.search(query_array, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._documents):
                metadata = self._metadatas[idx] if idx < len(self._metadatas) else {}
                results.append((self._documents[idx], float(score), metadata))
        
        return results
    
    def delete(self, ids: List[int] = None, store_name: str = "default"):
        """删除索引中的文档"""
        if self._index is None:
            self._load_index()
        
        if self._index is None:
            return
        
        # 注意：FAISS 删除操作比较复杂，这里简化处理
        # 实际应用中可能需要重建索引
        print("删除操作需要重建索引，暂时不支持")
    
    def clear(self, store_name: str = "default"):
        """清空索引"""
        self._index = None
        self._documents = []
        self._metadatas = []
        
        # 删除文件
        faiss_file = self._get_faiss_index_file(store_name)
        store_file = self._get_store_file(store_name)
        
        for f in [faiss_file, store_file]:
            if f.exists():
                f.unlink()
        
        print("索引已清空")
    
    def get_stats(self, store_name: str = "default") -> dict:
        """获取索引统计信息"""
        if self._index is None:
            self._load_index()
        
        return {
            "document_count": len(self._documents),
            "index_size": self._index.ntotal if self._index else 0,
            "store_name": store_name
        }


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将文本分割成块
    
    Args:
        text: 原始文本
        chunk_size: 块大小
        overlap: 重叠大小
    
    Returns:
        文本块列表
    """
    if not text:
        return []
    
    # 按句子分割
    import re
    
    # 清理多余空白
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    
    # 按段落和句子分割
    paragraphs = text.split('\n')
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果段落本身很大，按句子分割
        if len(para) > chunk_size:
            sentences = re.split(r'(?<=[。！？!?])\s*', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + "\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + "\n"
        else:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # 如果没有分句成功，使用简单的滑动窗口
    if len(chunks) == 0 and len(text) > chunk_size:
        chars = list(text)
        for i in range(0, len(chars), chunk_size - overlap):
            chunk = ''.join(chars[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
    
    return chunks


if __name__ == "__main__":
    # 测试向量存储
    store = VectorStore()
    
    print("=" * 50)
    print("向量存储测试")
    print("=" * 50)
    
    # 测试文档
    test_docs = [
        "人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。",
        "机器学习是人工智能的一个子领域，它使计算机能够从数据中学习而无需明确编程。",
        "深度学习是机器学习的一种方法，使用多层神经网络来学习数据的复杂模式。",
        "自然语言处理（NLP）使计算机能够理解、解释和生成人类语言。",
        "向量数据库存储和检索高维向量，是AI应用的重要组成部分。"
    ]
    
    # 添加文档
    store.add_documents(test_docs)
    
    # 搜索
    results = store.search("什么是机器学习？", k=3)
    
    print("\n搜索结果: 什么是机器学习？")
    for i, (doc, score, meta) in enumerate(results):
        print(f"\n{i+1}. [相似度: {score:.4f}]")
        print(f"   {doc}")
    
    print(f"\n索引统计: {store.get_stats()}")