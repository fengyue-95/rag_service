new Vue({
    el: '#app',
    data() {
        return {
            uploadedFiles: [],
            selectedFiles: [],
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
    methods: {
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
            this.$message.success(`已选择 ${this.selectedFiles.length} 个文件`);
            // TODO: 实现索引功能
        },
        
        handleDeleteClick() {
            if (this.selectedFiles.length === 0) {
                this.$message.warning('请先选择要删除的文件');
                return;
            }
            
            this.$confirm(`确定要删除选中的 ${this.selectedFiles.length} 个文件吗?`, '确认删除', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
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
                    this.$message.success(result.message);
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
                        type: file.type
                    }));
                    this.selectedFiles = []; // 清空选择
                }
            } catch (error) {
                console.error('加载文件列表失败:', error);
            }
        }
    }
});