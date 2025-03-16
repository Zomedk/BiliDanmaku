new Vue({
    el: '#app',  // Vue实例挂载到页面中的id为'app'的元素上
    data: {
        bvInput: '',  // 用户输入的BV号或视频链接
        videoInfo: null,  // 存储视频信息
        danmakuData: [],  // 存储弹幕信息
        currentPage: 1,   // 当前页码
        itemsPerPage: 50, // 每页显示的弹幕数
        totalPages: 1,    // 总页数
        isLoading: false  // 处理加载状态，防止重复请求
    },
    methods: {
        fetchVideoInfo() {
            console.log("Fetching video info for BV:", this.bvInput);  // 在控制台输出正在请求的视频信息

            // 向后端发送请求，获取视频信息
            fetch('http://127.0.0.1:5000/api/video', {
                method: 'POST',  // 使用POST方法
                headers: {
                    'Content-Type': 'application/json'  // 请求内容为JSON格式
                },
                body: JSON.stringify({ bv: this.bvInput })  // 将用户输入的BV号转换为JSON格式并发送
            })
            .then(response => {
                console.log('Response Status:', response.status);  // 输出响应状态
                return response.json();  // 将响应数据转换为JSON格式
            })
            .then(data => {
                console.log('Response data:', data);  // 输出响应数据
                if (data.error) {  // 如果返回数据中有错误字段，弹出错误提示
                    alert(data.error);
                } else {
                    this.videoInfo = data;  // 将返回的视频信息存储到videoInfo中
                }
            })
            .catch(error => {
                alert("发生错误: " + error);  // 请求失败时弹出错误提示
                console.error('Error:', error);  // 在控制台输出错误信息
            });
        },
        // 获取弹幕数据
        fetchDanmaku() {
            console.log("Fetching danmaku for BV:", this.bvInput);
            
            // 设置加载状态，避免重复请求
            this.isLoading = true;
    
            fetch('http://127.0.0.1:5000/api/danmaku', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bv: this.bvInput, page: this.currentPage, per_page: this.itemsPerPage })
            })
            .then(res => res.json())
            .then(data => {
                console.log("Danmaku data received:", data);
                if (data.error) {
                    alert(data.error);
                } else {
                    Vue.set(this, 'danmakuData', data.danmaku); // 确保数据可响应
                    this.totalPages = data.total_pages || 1; // 确保 totalPages 不为空
                    this.currentPage = data.current_page;
                    console.log(`Current Page: ${this.currentPage}, Total Pages: ${this.totalPages}`);
                }
            })
            .catch(error => {
                console.error("Error fetching danmaku:", error);
                alert("发生错误: " + error);
            })
            .finally(() => {
                this.isLoading = false;
            });
        },
    
        // 切换页码
        changePage(page) {
            console.log("Changing to page:", page);  
            if (page < 1 || page > this.totalPages) {  
                console.warn("Invalid page number:", page);  
                return;  
            }
            this.currentPage = page;  
            this.fetchDanmaku();  
        }
    },
    computed: {
        paginatedDanmaku() {
            return this.danmakuData; // 直接使用后端返回的数据
        }
    }
});
