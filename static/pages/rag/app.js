new Vue({
    el: '#app',
    data() {
        return {
            uploadedFiles: [],
            selectedFiles: [],
            selectAll: false,
            fileSearch: '',
            polishEnabled: false,
            selectedMethod: 'option1',
            expandedMethod: 'option1',
            loading: false,
            inputMessage: '',
            messages: [
                {
                    type: 'bot',
                    content: '你好！我是你的助手。上传文件后，我可以帮你分析内容或回答相关问题。'
                }
            ],
            ragMethods: [
                {
                    id: 'option1',
                    num: '1',
                    name: 'SimpleRAG',
                    fullName: 'SimpleRAG（简单切块）',
                    category: 'doc',
                    desc: '固定长度切块，检索后直接返回结果',
                    scenarios: '验证原型、快速上线，对精度要求不高的场景',
                    documents: '结构简单、段落分明的短文，如博客、简单新闻'
                },
                {
                    id: 'option2',
                    num: '2',
                    name: 'Semantic Chunking',
                    fullName: 'Semantic Chunking（语义切块）',
                    category: 'doc',
                    desc: '基于语义相似度动态分块，保持句子完整性',
                    scenarios: '句子间逻辑紧密，传统固定长度切块会割裂语义的场景',
                    documents: '非规范格式文档、长随笔、文学作品'
                },
                {
                    id: 'option3',
                    num: '3',
                    name: 'Context Enriched',
                    fullName: 'Context Enriched Retrieval（上下文增强检索）',
                    category: 'doc',
                    desc: '检索时添加上下文信息，提升语义匹配精度',
                    scenarios: '需要精确匹配但又不能丢失大背景信息的场景',
                    documents: '技术手册、法律条文、需要"以小见大"的精细检索'
                },
                {
                    id: 'option4',
                    num: '4',
                    name: 'Context Headers',
                    fullName: 'Contextual Chunk Headers（上下文分块标题）',
                    category: 'doc',
                    desc: '为每个分块添加层次化标题，帮助理解文档结构',
                    scenarios: '文档结构复杂，需要快速定位的查询',
                    documents: '技术规范、API文档、学术论文'
                },
                {
                    id: 'option5',
                    num: '5',
                    name: 'Document Augmentation',
                    fullName: 'Document Augmentation（文档增强）',
                    category: 'doc',
                    desc: '检索后补充相关上下文，形成更完整的知识单元',
                    scenarios: '答案分散在多处，需要整合信息才能完整回答',
                    documents: 'FAQ文档、分散的知识条目、关联性强的内容'
                },
                {
                    id: 'option6',
                    num: '6',
                    name: 'Query Transformation',
                    fullName: 'Query Transformation（查询转换）',
                    category: 'query',
                    desc: '将用户查询转换为多个子查询，并行检索后融合结果',
                    scenarios: '单次检索难以覆盖所有相关内容的复杂查询',
                    documents: '综合性文档库、跨章节内容检索'
                },
                {
                    id: 'option7',
                    num: '7',
                    name: 'Reranker',
                    fullName: 'Reranker（重排序）',
                    category: 'query',
                    desc: '先粗筛再精排，使用交叉编码器进行精细排序',
                    scenarios: '检索结果相关性需要进一步提升的场景',
                    documents: '大规模文档库、语义相近但实际不同的内容'
                },
                {
                    id: 'option8',
                    num: '8',
                    name: 'RSE',
                    fullName: 'RSE（语义扩展重排序）',
                    category: 'query',
                    desc: '基于查询语义扩展生成伪文档，提升检索召回',
                    scenarios: '查询与文档表述差异大，直接匹配困难',
                    documents: '专业术语多、口语化表达与书面语差异大的内容'
                },
                {
                    id: 'option9',
                    num: '9',
                    name: 'Feedback Loop',
                    fullName: 'Feedback Loop（反馈闭环）',
                    category: 'query',
                    desc: '基于生成结果反馈优化检索，形成迭代改进',
                    scenarios: '需要高精度、允许一定延迟的复杂问题',
                    documents: '高价值知识库、需要持续优化的核心场景'
                },
                {
                    id: 'option10',
                    num: '10',
                    name: 'Adaptive RAG',
                    fullName: 'Adaptive RAG（自适应检索增强生成）',
                    category: 'query',
                    desc: '根据问题类型自动选择最优检索策略',
                    scenarios: '问题类型多样，需要动态调整策略',
                    documents: '通用知识库、混合类型文档'
                },
                {
                    id: 'option11',
                    num: '11',
                    name: 'Self-RAG',
                    fullName: 'Self-RAG（自反思检索增强生成）',
                    category: 'query',
                    desc: '模型自主判断是否需要检索，并评估结果相关性',
                    scenarios: '需要模型自主决策、何时检索的场景',
                    documents: '开放域问答、需要避免不必要检索的场景'
                },
                {
                    id: 'option12',
                    num: '12',
                    name: 'Knowledge Graph',
                    fullName: 'Knowledge Graph（知识图谱）',
                    category: 'doc',
                    desc: '构建实体和关系网络，支持图推理问答',
                    scenarios: '需要关联分析、关系推理的复杂查询',
                    documents: '人物/事件/概念关系复杂的文档'
                },
                {
                    id: 'option13',
                    num: '13',
                    name: 'Hierarchical Indices',
                    fullName: 'Hierarchical Indices（层次化索引）',
                    category: 'doc',
                    desc: '建立多级索引结构，从摘要到细节逐层检索',
                    scenarios: '大型文档集、需要分层次精确定位的场景',
                    documents: '长篇报告、技术规范、书籍章节'
                },
                {
                    id: 'option14',
                    num: '14',
                    name: 'HyDE',
                    fullName: 'HyDE（假设文档嵌入）',
                    category: 'query',
                    desc: '先让模型生成假设答案，再用假设去检索相似文档',
                    scenarios: '查询表述模糊、与文档内容存在"语义差"的场景',
                    documents: '开放式问题、表述不精确的查询'
                },
                {
                    id: 'option15',
                    num: '15',
                    name: 'Fusion',
                    fullName: 'Fusion（融合检索）',
                    category: 'query',
                    desc: '综合多种检索策略的结果，通过算法融合排序',
                    scenarios: '单策略效果不稳定，需要综合多策略优势',
                    documents: '多样化的文档库、混合检索需求'
                },
                {
                    id: 'option16',
                    num: '16',
                    name: 'CRAG',
                    fullName: 'CRAG（纠错型 RAG）',
                    category: 'query',
                    desc: '检测并纠正检索/生成中的错误，提升准确性',
                    scenarios: '对准确性要求高、需要错误纠正机制',
                    documents: '高精度知识库、关键决策支持'
                },
                {
                    id: 'option17',
                    num: '17',
                    name: 'Multi-Modal RAG',
                    fullName: 'Multi-Modal RAG（多模态检索增强生成）',
                    category: 'doc',
                    desc: '支持文本、图像、表格等多种模态的检索与问答',
                    scenarios: '包含大量图表、图像内容的多模态文档',
                    documents: '研究报告、含图表的技术文档、图文混合内容'
                }
            ]
        };
    },
    computed: {
        filteredFiles() {
            if (!this.fileSearch.trim()) {
                return this.uploadedFiles;
            }
            const search = this.fileSearch.toLowerCase();
            return this.uploadedFiles.filter(file => 
                file.name.toLowerCase().includes(search)
            );
        },
        docMethods() {
            return this.ragMethods.filter(m => m.category === 'doc');
        },
        queryMethods() {
            return this.ragMethods.filter(m => m.category === 'query');
        }
    },
    mounted() {
        this.loadUploadedFiles();
    },
    methods: {
        toggleMethod(methodId) {
            if (this.expandedMethod === methodId) {
                this.expandedMethod = null;
            } else {
                this.expandedMethod = methodId;
                this.selectedMethod = methodId;
            }
        },
        
        selectMethod(methodId) {
            this.selectedMethod = methodId;
            this.expandedMethod = methodId;
        },
        
        beforeUpload(file) {
            const allowedExtensions = ['.txt', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx'];
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(fileExt)) {
                this.$message.error(`不支持的文件类型。仅支持: ${allowedExtensions.join(', ')}`);
                return false;
            }
            return true;
        },
        
        handleUploadSuccess(response, file) {
            this.$message.success(`文件 "${file.name}" 上传成功！`);
            this.uploadedFiles.push({
                name: file.name,
                size: file.size,
                type: '.' + file.name.split('.').pop().toLowerCase()
            });
            this.messages.push({
                type: 'bot',
                content: `文件 "${file.name}" 上传成功！`
            });
            this.$nextTick(() => this.scrollToBottom());
        },
        
        handleUploadError() {
            this.$message.error('文件上传失败');
        },
        
        toggleFileSelection(fileName) {
            const index = this.selectedFiles.indexOf(fileName);
            if (index > -1) {
                this.selectedFiles.splice(index, 1);
            } else {
                this.selectedFiles.push(fileName);
            }
            this.selectAll = this.selectedFiles.length === this.filteredFiles.length;
        },
        
        handleSelectAll(val) {
            if (val) {
                this.selectedFiles = this.filteredFiles.map(f => f.name);
            } else {
                this.selectedFiles = [];
            }
        },
        
        getFileIcon(extension) {
            const icons = {
                '.txt': '📄', '.md': '📝', '.csv': '📊',
                '.pdf': '📕', '.doc': '📘', '.docx': '📘',
                '.xls': '📗', '.xlsx': '📗'
            };
            return icons[extension] || '📁';
        },
        
        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        },
        
        async loadUploadedFiles() {
            try {
                const response = await fetch('/uploads');
                if (response.ok) {
                    const result = await response.json();
                    this.uploadedFiles = result.files.map(file => ({
                        name: file.filename,
                        size: file.size,
                        type: file.type,
                        indexed: file.indexed || false
                    }));
                }
            } catch (error) {
                console.error('加载文件列表失败:', error);
            }
        },
        
        async handleIndexClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择文件');
                return;
            }
            this.$message.info('正在创建索引...');
            try {
                const response = await fetch('/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filenames: this.selectedFiles })
                });
                if (response.ok) {
                    this.$message.success('索引创建成功');
                    this.loadUploadedFiles();
                }
            } catch (error) {
                this.$message.error('索引创建失败');
            }
        },
        
        async handleDeleteIndexClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择文件');
                return;
            }
            try {
                const response = await fetch('/index/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filenames: this.selectedFiles })
                });
                if (response.ok) {
                    this.$message.success('删除索引成功');
                    this.loadUploadedFiles();
                }
            } catch (error) {
                this.$message.error('删除索引失败');
            }
        },
        
        handleDeleteClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择文件');
                return;
            }
            this.$confirm(`确定要删除选中的 ${this.selectedFiles.length} 个文件吗？`, '确认删除', {
                type: 'warning'
            }).then(async () => {
                try {
                    const response = await fetch('/uploads/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filenames: this.selectedFiles })
                    });
                    if (response.ok) {
                        this.$message.success('删除成功');
                        this.selectedFiles = [];
                        this.loadUploadedFiles();
                    }
                } catch (error) {
                    this.$message.error('删除失败');
                }
            });
        },
        
        async sendMessage() {
            const message = this.inputMessage.trim();
            if (!message || this.loading) return;

            const method = this.ragMethods.find(m => m.id === this.selectedMethod);
            this.messages.push({ 
                type: 'user', 
                content: `${message}\n\n[使用RAG方法: ${method?.fullName || 'SimpleRAG'}]` 
            });
            this.inputMessage = '';
            this.loading = true;
            this.$nextTick(() => this.scrollToBottom());

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message, 
                        rag_method: this.selectedMethod, 
                        polish: this.polishEnabled 
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    let content = result.message;
                    // 显示出处信息
                    if (result.sources && result.sources.length > 0) {
                        content += `\n\n**参考文档**:\n${result.sources.map(s => '• ' + s).join('\n')}`;
                    }
                    this.messages.push({ type: 'bot', content: content });
                }
            } catch (error) {
                this.messages.push({ type: 'bot', content: '抱歉，发生了错误。' + (error.message ? ': ' + error.message : '') });
            } finally {
                this.loading = false;
                this.$nextTick(() => this.scrollToBottom());
            }
        },
        
        scrollToBottom() {
            const chatMessages = this.$refs.chatMessages;
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
    }
});