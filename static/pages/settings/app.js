new Vue({
    el: '#app',
    data() {
        return {
            settings: {
                apiType: 'deepseek',
                apiKey: '',
                ollamaUrl: 'http://localhost:11434',
                modelName: 'deepseek-chat',
                chunkSize: 500,
                chunkOverlap: 50,
                topK: 5,
                similarityThreshold: 0.7,
                defaultRagMethod: 'option1',
                theme: 'light',
                language: 'zh-CN',
                autoSaveChat: true
            },
            apiStatus: 'disconnected',
            testingApi: false,
            saving: false
        };
    },
    mounted() {
        this.loadSettings();
    },
    methods: {
        loadSettings() {
            const saved = localStorage.getItem('ragSettings');
            if (saved) {
                this.settings = { ...this.settings, ...JSON.parse(saved) };
            }
        },
        async testApiConnection() {
            this.testingApi = true;
            this.apiStatus = 'disconnected';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: 'Hello',
                        rag_method: this.settings.defaultRagMethod
                    })
                });
                
                if (response.ok) {
                    this.apiStatus = 'connected';
                    this.$message.success('API 连接成功');
                } else {
                    this.$message.error('API 连接失败');
                }
            } catch (error) {
                this.$message.error('API 连接失败: ' + error.message);
            } finally {
                this.testingApi = false;
            }
        },
        saveSettings() {
            this.saving = true;
            localStorage.setItem('ragSettings', JSON.stringify(this.settings));
            
            setTimeout(() => {
                this.saving = false;
                this.$message.success('设置已保存');
            }, 500);
        },
        resetSettings() {
            this.$confirm('确定要恢复默认设置吗？', '确认', { type: 'warning' })
                .then(() => {
                    localStorage.removeItem('ragSettings');
                    this.settings = {
                        apiType: 'deepseek',
                        apiKey: '',
                        ollamaUrl: 'http://localhost:11434',
                        modelName: 'deepseek-chat',
                        chunkSize: 500,
                        chunkOverlap: 50,
                        topK: 5,
                        similarityThreshold: 0.7,
                        defaultRagMethod: 'option1',
                        theme: 'light',
                        language: 'zh-CN',
                        autoSaveChat: true
                    };
                    this.$message.success('已恢复默认设置');
                });
        }
    }
});