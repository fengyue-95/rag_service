new Vue({
    el: '#app',
    data() {
        return {
            sidebarExpanded: true,
            currentPage: 'rag'
        };
    },
    mounted() {
        this.loadPage('rag');
    },
    methods: {
        toggleSidebar() {
            this.sidebarExpanded = !this.sidebarExpanded;
        },
        switchPage(page) {
            this.currentPage = page;
            this.loadPage(page);
        },
        loadPage(page) {
            const frame = document.getElementById('pageFrame');
            if (frame) {
                frame.src = `/static/pages/${page}/index.html`;
            }
        }
    }
});
