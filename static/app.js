new Vue({
    el: '#app',
    data() {
        return {
            uploadedFiles: [],
            selectedFiles: [],
            sidebarExpanded: true,
            currentPage: 'rag',
            showFilePanel: true,
            selectedOption: 'option1',
            expandedOption: 'option1',
            fileSearch: '',
            ragConfigs: {
                option1: '',
                option2: '',
                option3: '',
                option4: '',
                option5: '',
                option6: '',
                option7: '',
                option8: '',
                option9: '',
                option10: '',
                option11: '',
                option12: '',
                option13: '',
                option14: '',
                option15: '',
                option16: '',
                option17: ''
            },
            messages: [
                {
                    type: 'bot',
                    content: '你好！我是你的助手。上传文件后，我可以帮你分析内容或回答相关问题。'
                }
            ],
            inputMessage: '',
            sending: false
        };
    },
    mounted() {
        this.loadUploadedFiles();
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
        }
    },
    
    methods: {
        toggleSidebar() {
            this.sidebarExpanded = !this.sidebarExpanded;
        },
        
        toggleOption(option) {
            this.selectedOption = option;
            this.expandedOption = this.expandedOption === option ? null : option;
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
        
        handleUploadSuccess(response, file, fileList) {
            this.$message.success(`文件 "${file.name}" 上传成功！`);
            this.uploadedFiles.push({
                name: file.name,
                size: file.size,
                type: '.' + file.name.split('.').pop().toLowerCase()
            });
            this.addMessage('bot', `文件 "${file.name}" 上传成功！${response.content ? '内容已读取。' : ''}`);
        },
        
        handleUploadError(err, file, fileList) {
            this.$message.error(`文件 "${file.name}" 上传失败`);
            this.addMessage('bot', `文件 "${file.name}" 上传失败`);
        },
        
        handleFileSelectChange(val) {
            console.log('已选择文件:', val);
        },
        
        handleIndexClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择文件');
                return;
            }
            
            // 标记文件为已索引
            fetch('/index/mark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filenames: this.selectedFiles })
            }).then(response => {
                if (response.ok) {
                    this.$message.success(`已为 ${this.selectedFiles.length} 个文件创建索引`);
                    this.loadUploadedFiles();
                }
            }).catch(error => {
                console.error('索引失败:', error);
                this.$message.error('索引失败，请稍后再试');
            });
        },
        
        handleDeleteIndexClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择要删除索引的文件');
                return;
            }
            
            fetch('/index/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filenames: this.selectedFiles })
            }).then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error('删除索引失败');
            }).then(result => {
                this.$message.success(result.message);
                this.loadUploadedFiles();
            }).catch(error => {
                console.error('删除索引失败:', error);
                this.$message.error('删除索引失败，请稍后再试');
            });
        },
        
        handleDeleteClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择要删除的文件');
                return;
            }
            
            // 先检查哪些文件存在索引
            const filesWithIndex = this.uploadedFiles
                .filter(f => this.selectedFiles.includes(f.name) && f.indexed)
                .map(f => f.name);
            
            let confirmMessage = `确定要删除选中的 ${this.selectedFiles.length} 个文件吗？`;
            if (filesWithIndex.length > 0) {
                confirmMessage += `<br><br><span style="color: #E6A23C;">注意：以下 ${filesWithIndex.length} 个文件存在索引，将同时删除：</span><br>${filesWithIndex.join('<br>')}`;
            }
            
            this.$confirm(confirmMessage, '确认删除', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: filesWithIndex.length > 0 ? 'warning' : 'danger',
                dangerouslyUseHTMLString: true,
                distinguishCancelAndClose: true
            }).then(async () => {
                try {
                    const response = await fetch('/uploads/delete', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ filenames: this.selectedFiles })
                    });
                    
                    if (!response.ok) {
                        throw new Error('删除失败');
                    }
                    
                    const result = await response.json();
                    
                    // 构建成功消息
                    let msg = result.message;
                    if (result.deleted_indexes && result.deleted_indexes.length > 0) {
                        msg += `，索引: ${result.deleted_indexes.join(', ')}`;
                    }
                    if (result.deleted_files && result.deleted_files.length > 0) {
                        msg += `，文件: ${result.deleted_files.join(', ')}`;
                    }
                    
                    this.$message.success(msg);
                    this.selectedFiles = [];
                    this.loadUploadedFiles();
                } catch (error) {
                    console.error('删除文件失败:', error);
                    this.$message.error('删除文件失败，请稍后再试');
                }
            }).catch(() => {
                // 用户取消
            });
        },
        
        async sendMessage() {
            const message = this.inputMessage.trim();
            if (!message || this.sending) return;

            this.addMessage('user', message);
            this.inputMessage = '';
            this.sending = true;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });

                if (!response.ok) {
                    throw new Error('发送失败');
                }

                const result = await response.json();
                this.addMessage('bot', result.message);
            } catch (error) {
                console.error('聊天错误:', error);
                this.$message.error('抱歉，发生了错误，请稍后再试。');
                this.addMessage('bot', '抱歉，发生了错误，请稍后再试。');
            } finally {
                this.sending = false;
            }
        },
        
        addMessage(type, content) {
            this.messages.push({ type, content });
            this.$nextTick(() => {
                this.scrollToBottom();
            });
        },
        
        scrollToBottom() {
            const chatMessages = this.$refs.chatMessages;
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        },
        
        getFileIcon(extension) {
            const icons = {
                '.txt': '📄',
                '.md': '📝',
                '.csv': '📊',
                '.pdf': '📕',
                '.doc': '📘',
                '.docx': '📘',
                '.xls': '📗',
                '.xlsx': '📗'
            };
            return icons[extension] || '📁';
        },
        
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
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
                    this.selectedFiles = []; // 清空选择
                }
            } catch (error) {
                console.error('加载文件列表失败:', error);
            }
        },
        
        getPageIcon(page) {
            const icons = {
                'home': '🏠',
                'files': '📁',
                'chat': '💬',
                'history': '📜',
                'settings': '⚙️'
            };
            return icons[page] || '📄';
        },
        
        getPageTitle(page) {
            const titles = {
                'home': '首页',
                'files': '文件管理',
                'chat': '智能对话',
                'history': '历史记录',
                'settings': '设置'
            };
            return titles[page] || '页面';
        }
    }
});