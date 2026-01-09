new Vue({
    el: '#app',
    data() {
        return {
            chats: [],
            currentChatId: null,
            currentMessages: [],
            searchKeyword: '',
            inputMessage: '',
            loading: false,
            polishEnabled: false,
            selectedModel: 'deepseek',
            suggestions: ['这是什么？', '请详细说明', '有什么应用场景？']
        };
    },
    computed: {
        filteredChats() {
            if (!this.searchKeyword) return this.chats;
            const keyword = this.searchKeyword.toLowerCase();
            return this.chats.filter(c => c.title.toLowerCase().includes(keyword));
        }
    },
    mounted() {
        this.loadChats();
        this.initLocalStorage();
    },
    methods: {
        initLocalStorage() {
            if (!localStorage.getItem('chatHistories')) {
                localStorage.setItem('chatHistories', JSON.stringify({}));
            }
            if (!localStorage.getItem('chatCurrentId')) {
                localStorage.setItem('chatCurrentId', null);
            }
            this.currentChatId = localStorage.getItem('chatCurrentId');
        },
        loadChats() {
            const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
            this.chats = Object.values(histories).map((chat, i) => ({
                id: chat.id,
                title: chat.title || `对话 ${i + 1}`,
                time: chat.time || new Date().toLocaleString(),
                icon: '💬'
            })).reverse();
        },
        selectChat(id) {
            this.currentChatId = id;
            const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
            this.currentMessages = histories[id]?.messages || [];
            localStorage.setItem('chatCurrentId', id);
        },
        newChat() {
            const id = 'chat_' + Date.now();
            const newChat = {
                id,
                title: '新对话',
                time: new Date().toLocaleString(),
                icon: '💬',
                messages: []
            };
            const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
            histories[id] = newChat;
            localStorage.setItem('chatHistories', JSON.stringify(histories));
            this.loadChats();
            this.selectChat(id);
        },
        async sendMessage() {
            const message = this.inputMessage.trim();
            if (!message || this.loading) return;

            if (!this.currentChatId) {
                this.newChat();
            }

            this.currentMessages.push({ role: 'user', content: message });
            this.inputMessage = '';
            this.loading = true;
            this.scrollToBottom();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, rag_method: 'option1', polish: this.polishEnabled })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    this.currentMessages.push({ role: 'bot', content: result.message });
                    this.updateChatHistory();
                }
            } catch (error) {
                this.currentMessages.push({ role: 'bot', content: '抱歉，发生了错误。' });
            } finally {
                this.loading = false;
                this.scrollToBottom();
            }
        },
        updateChatHistory() {
            const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
            if (histories[this.currentChatId]) {
                histories[this.currentChatId].messages = this.currentMessages;
                if (this.currentMessages.length > 1) {
                    const title = this.currentMessages[1]?.content?.slice(0, 15) || '新对话';
                    histories[this.currentChatId].title = title + (title.length >= 15 ? '...' : '');
                }
                localStorage.setItem('chatHistories', JSON.stringify(histories));
                this.loadChats();
            }
        },
        handleChatCommand(command, id) {
            if (command === 'rename') {
                this.$prompt('请输入新的对话名称', '重命名', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消'
                }).then(({ value }) => {
                    const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
                    if (histories[id]) {
                        histories[id].title = value || '新对话';
                        localStorage.setItem('chatHistories', JSON.stringify(histories));
                        this.loadChats();
                    }
                });
            } else if (command === 'delete') {
                this.$confirm('确定要删除这个对话吗？', '确认删除', { type: 'warning' })
                    .then(() => {
                        const histories = JSON.parse(localStorage.getItem('chatHistories') || '{}');
                        delete histories[id];
                        localStorage.setItem('chatHistories', JSON.stringify(histories));
                        if (this.currentChatId === id) {
                            this.currentChatId = null;
                            this.currentMessages = [];
                            localStorage.setItem('chatCurrentId', null);
                        }
                        this.loadChats();
                    });
            }
        },
        askSuggestion(q) {
            this.inputMessage = q;
            this.sendMessage();
        },
        formatMessage(content) {
            return content?.replace(/\n/g, '<br>') || '';
        },
        scrollToBottom() {
            this.$nextTick(() => {
                const el = this.$refs.chatMessages;
                if (el) el.scrollTop = el.scrollHeight;
            });
        }
    }
});