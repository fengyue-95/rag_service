new Vue({
    el: '#app',
    data() {
        return {
            viewMode: 'grouped',
            searchKeyword: '',
            drawerVisible: false,
            currentChat: null,
            chats: []
        };
    },
    computed: {
        hasHistory() {
            return this.chats.length > 0;
        },
        filteredChats() {
            if (!this.searchKeyword) return this.chats;
            const keyword = this.searchKeyword.toLowerCase();
            return this.chats.filter(c =>
                c.title.toLowerCase().includes(keyword) ||
                c.messages?.some(m => m.content?.toLowerCase().includes(keyword))
            );
        },
        groupedChats() {
            const groups = {};
            this.filteredChats.forEach(chat => {
                const date = this.formatDate(chat.time);
                if (!groups[date]) groups[date] = [];
                groups[date].push(chat);
            });
            return groups;
        }
    },
    mounted() {
        this.loadHistory();
    },
    methods: {
        loadHistory() {
            const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
            this.chats = Object.values(histories)
                .map((chat, i) => ({
                    id: chat.id,
                    title: chat.title || `对话 ${i + 1}`,
                    time: chat.time || new Date().toLocaleString(),
                    messages: chat.messages || []
                }))
                .sort((a, b) => new Date(b.time) - new Date(a.time));
        },
        formatDate(timeStr) {
            try {
                const date = new Date(timeStr);
                const today = new Date();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                
                if (date.toDateString() === today.toDateString()) return '今天';
                if (date.toDateString() === yesterday.toDateString()) return '昨天';
                
                return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
            } catch {
                return '未知日期';
            }
        },
        getChatPreview(chat) {
            const msg = chat.messages?.[1]?.content || chat.messages?.[0]?.content || '';
            return msg.slice(0, 50) + (msg.length > 50 ? '...' : '');
        },
        openChatDetail(chat) {
            this.currentChat = chat;
            this.drawerVisible = true;
        },
        continueChat() {
            window.parent.postMessage({ type: 'switchPage', page: 'chat' }, '*');
        },
        deleteChat(id) {
            this.$confirm('确定要删除这条历史记录吗？', '确认删除', { type: 'warning' })
                .then(() => {
                    const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
                    delete histories[id];
                    localStorage.setItem('chatHistories', JSON.stringify(histories));
                    this.drawerVisible = false;
                    this.loadHistory();
                    this.$message.success('删除成功');
                });
        },
        clearAllHistory() {
            this.$confirm('确定要清空所有历史记录吗？此操作不可恢复。', '警告', {
                type: 'warning',
                confirmButtonText: '确定清空',
                cancelButtonText: '取消'
            }).then(() => {
                localStorage.setItem('chatHistories', JSON.stringify({}));
                localStorage.setItem('chatCurrentId', null);
                this.chats = [];
                this.$message.success('历史记录已清空');
            });
        }
    }
});