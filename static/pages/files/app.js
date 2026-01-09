new Vue({
    el: '#app',
    data() {
        return {
            files: [],
            selectedFiles: [],
            searchKeyword: '',
            statusFilter: '',
            uploadDialogVisible: false,
            detailDialogVisible: false,
            currentFile: null
        };
    },
    computed: {
        filteredFiles() {
            let result = this.files;
            if (this.searchKeyword) {
                const keyword = this.searchKeyword.toLowerCase();
                result = result.filter(f => f.name.toLowerCase().includes(keyword));
            }
            if (this.statusFilter) {
                result = result.filter(f => {
                    if (this.statusFilter === 'uploaded') return !f.indexed;
                    if (this.statusFilter === 'indexed') return f.indexed;
                    return true;
                });
            }
            return result;
        }
    },
    mounted() {
        this.loadFiles();
    },
    methods: {
        loadFiles() {
            fetch('/uploads')
                .then(res => res.json())
                .then(data => {
                    // 将 filename 映射为 name，并添加上传时间
                    this.files = (data.files || []).map(f => ({
                        ...f,
                        name: f.filename,
                        uploadTime: new Date().toLocaleString('zh-CN')
                    }));
                })
                .catch(err => console.error('加载文件列表失败:', err));
        },
        getFileIcon(type) {
            const icons = {
                '.txt': '📄', '.md': '📝', '.csv': '📊',
                '.pdf': '📕', '.doc': '📘', '.docx': '📘',
                '.xls': '📗', '.xlsx': '📗'
            };
            return icons[type] || '📁';
        },
        formatSize(row, col, value) {
            if (!value) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(value) / Math.log(k));
            return Math.round(value / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        },
        handleSelectionChange(val) {
            this.selectedFiles = val;
        },
        showUploadDialog() {
            this.uploadDialogVisible = true;
        },
        beforeUpload(file) {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            const allowed = ['.txt', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx'];
            if (!allowed.includes(ext)) {
                this.$message.error('不支持的文件类型');
                return false;
            }
            return true;
        },
        handleUploadSuccess(response, file) {
            this.$message.success('上传成功');
            this.uploadDialogVisible = false;
            this.loadFiles();
        },
        handleUploadError() {
            this.$message.error('上传失败');
        },
        viewFile(row) {
            this.currentFile = row;
            this.detailDialogVisible = true;
        },
        deleteFile(row) {
            this.$confirm(`确定要删除文件 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
                .then(() => {
                    fetch('/uploads/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filenames: [row.name] })
                    }).then(res => {
                        if (res.ok) {
                            this.$message.success('删除成功');
                            this.loadFiles();
                        }
                    });
                });
        },
        batchIndex() {
                            const names = this.selectedFiles.map(f => f.name);
                            fetch('/index', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ filenames: names })
                            }).then(res => {                if (res.ok) {
                    this.$message.success('索引创建成功');
                    this.loadFiles();
                }
            });
        },
        batchDelete() {
            const names = this.selectedFiles.map(f => f.name);
            this.$confirm(`确定要删除选中的 ${names.length} 个文件吗？`, '批量删除', { type: 'warning' })
                .then(() => {
                    fetch('/uploads/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filenames: names })
                    }).then(res => {
                        if (res.ok) {
                            this.$message.success('删除成功');
                            this.loadFiles();
                        }
                    });
                });
        }
    }
});