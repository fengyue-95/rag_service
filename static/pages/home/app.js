new Vue({
    el: '#app',
    data() {
        return {
            fileCount: 0,
            indexedCount: 0
        };
    },
    mounted() {
        this.loadStats();
    },
    methods: {
        goToPage(page) {
            window.parent.postMessage({ type: 'switchPage', page: page }, '*');
        },
        async loadStats() {
            try {
                const response = await fetch('/uploads');
                if (response.ok) {
                    const result = await response.json();
                    this.fileCount = result.files ? result.files.length : 0;
                    this.indexedCount = result.files ? result.files.filter(f => f.indexed).length : 0;
                }
            } catch (error) {
                console.error('加载统计数据失败:', error);
            }
        }
    }
});