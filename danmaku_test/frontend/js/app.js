new Vue({
    el: '#app',  // Vue 实例挂载在页面上 id 为 app 的元素上
    data: {
        bvInput: '',  // 用户输入的 BV 号
        videoInfo: null,  // 存储视频信息
        danmakuData: [],  // 存储弹幕数据
        wordFrequency: [],  // 存储词频数据
        wordCloudImage: '',  // 存储词云图
        danmakuTimelineImage: '',  // 存储弹幕时间分布图
        timeProportionImage: '',  // 存储时间占比图
        currentPage: 1,  // 当前页码
        itemsPerPage: 50,  // 每页显示的条目数
        totalPages: 1,  // 总页数
        isLoading: false,  // 加载状态，防止重复请求
        activeTab: 'video-info',  // 当前激活的 tab，默认是视频信息
        searchKeyword: '',  // 搜索关键词
        sentimentData: null,  // 存储情感分析数据
        sortBy: 'time',  // 默认按时间排序
        sortOrder: 'asc',  // 排序顺序，默认升序
        pageInput: null,  // 页码输入框的值
        tabs: [
            { id: 'video-info', name: '视频信息' },  // 视频信息 tab
            { id: 'danmaku', name: '弹幕列表' },  // 弹幕列表 tab
            { id: 'word-frequency', name: '词频统计' },  // 词频统计 tab
            { id: 'advanced-analysis', name: '高级分析' },  // 高级分析 tab
            { id: 'sentiment', name: '情感分析' },  // 情感分析 tab
            { id: 'time-proportion', name: '弹幕时间占比' }  // 弹幕时间占比 tab
        ]
    },
    methods: {
        // 处理情感分析图表加载失败
        onChartError() {
            alert('情感分析图表加载失败');
            this.sentimentData = null;  // 失败时清空数据
        },
        // 获取视频信息
        fetchVideoInfo() {
            this.isLoading = true;  // 开始加载状态
            console.log("Fetching video info for BV:", this.bvInput);  // 输出日志，调试用
            fetch('http://127.0.0.1:5000/api/video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bv: this.bvInput })  // 发送 BV 号给后端请求视频信息
            })
            .then(response => response.json())  // 转换响应为 JSON
            .then(data => {
                if (data.error) {  // 如果有错误
                    alert(`获取视频信息失败：${data.error}`);  // 提示错误
                } else {
                    this.videoInfo = data;  // 成功获取视频信息
                    this.activeTab = 'video-info';  // 切换到视频信息 tab
                }
            })
            .catch(error => {
                alert(`获取视频信息失败: ${error.message}`);  // 捕获异常并提示错误
                console.error('Error:', error);  // 打印错误日志
            })
            .finally(() => {
                this.isLoading = false;  // 完成加载，停止加载状态
            });
        },
        // 获取弹幕列表数据
        fetchDanmaku() {
            if (this.isLoading) return;  // 如果正在加载，阻止重复请求
            this.isLoading = true;  // 开始加载
            console.log("Fetching danmaku for BV:", this.bvInput, "Sort:", this.sortBy, this.sortOrder, "Page:", this.currentPage);  // 打印请求参数
            fetch('http://127.0.0.1:5000/api/danmaku', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bv: this.bvInput,
                    page: this.currentPage,
                    per_page: this.itemsPerPage,
                    keyword: this.searchKeyword,
                    sort_by: this.sortBy,
                    sort_order: this.sortOrder
                })
            })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);  // 检查响应是否成功
                return res.json();  // 转换为 JSON
            })
            .then(data => {
                console.log("Received danmaku:", data.danmaku.slice(0, 5));  // 打印前五条弹幕
                if (data.error) {
                    alert(`获取弹幕失败：${data.error}`);
                    this.danmakuData = [];  // 如果有错误，清空弹幕数据
                } else {
                    this.danmakuData = data.danmaku || [];  // 成功获取数据
                    this.totalPages = data.total_pages || 1;  // 设置总页数
                    this.currentPage = data.current_page || 1;  // 设置当前页码
                }
            })
            .catch(error => {
                alert(`获取弹幕失败: ${error.message}`);  // 捕获异常
                console.error('Error:', error);  // 打印错误日志
                this.danmakuData = [];  // 清空弹幕数据
            })
            .finally(() => {
                this.isLoading = false;  // 完成加载，停止加载状态
            });
        },
        // 切换页面
        changePage(page) {
            if (page >= 1 && page <= this.totalPages) {  // 如果页码合法
                this.currentPage = page;
                this.pageInput = page;
                this.fetchDanmaku();  // 获取该页数据
            }
        },
        // 跳转到指定页面
        jumpToPage() {
            const page = parseInt(this.pageInput);  // 将输入框的值转换为整数
            if (!isNaN(page) && page >= 1 && page <= this.totalPages) {  // 验证页码合法性
                this.currentPage = page;
                this.fetchDanmaku();  // 获取该页数据
            } else {
                alert(`请输入 1 到 ${this.totalPages} 之间的页码`);  // 提示用户页码无效
                this.pageInput = null;  // 清空输入框
            }
        },
        // 按指定列排序
        sortBy(column) {
            if (this.isLoading) return;  // 如果正在加载，阻止重复排序
            console.log("Sorting by:", column);  // 打印排序字段
            if (this.sortBy === column) {  // 如果当前已经按该字段排序，切换排序方式（升序或降序）
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortBy = column;  // 设置新的排序字段
                this.sortOrder = 'asc';  // 默认升序
            }
            this.currentPage = 1;  // 排序后从第一页开始显示
            this.pageInput = 1;
            this.fetchDanmaku();  // 获取新的排序结果
        },
        // 获取词频数据
        async fetchWordFrequency() {
            try {
                this.isLoading = true;  // 开始加载状态
                console.log("Fetching word frequency for BV:", this.bvInput);  // 打印调试信息
                const response = await axios.post('http://127.0.0.1:5000/api/word_frequency', { bv: this.bvInput });
                if (response.data.top_words) {  // 如果返回了有效数据
                    console.log("Received word frequency:", response.data.top_words.slice(0, 5));  // 打印前五个词
                    this.wordFrequency = response.data.top_words;  // 保存词频数据
                } else {
                    alert('词频数据为空');  // 如果没有数据，提示错误
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取词频失败：${error.response.data.error}`
                    : `获取词频失败：${error.message}`;
                alert(errorMsg);  // 提示错误
                console.error('Error:', error);  // 打印错误日志
            } finally {
                this.isLoading = false;  // 完成加载
            }
        },
        // 获取词云图
        async fetchWordCloud() {
            try {
                this.isLoading = true;  // 开始加载
                console.log("Fetching word cloud for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/word_cloud', { bv: this.bvInput });
                if (response.data.image) {
                    this.wordCloudImage = response.data.image;  // 保存词云图
                } else {
                    alert('词云图生成失败');  // 如果失败，提示错误
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取词云失败：${error.response.data.error}`
                    : `获取词云失败：${error.message}`;
                alert(errorMsg);  // 提示错误
                console.error('Error:', error);  // 打印错误日志
            } finally {
                this.isLoading = false;  // 完成加载
            }
        },
        // 获取弹幕时间分布图
        async fetchDanmakuTimeline() {
            try {
                this.isLoading = true;  // 开始加载
                console.log("Fetching danmaku timeline for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_timeline', { bv: this.bvInput });
                if (response.data.image) {
                    this.danmakuTimelineImage = response.data.image;  // 保存弹幕时间分布图
                } else {
                    alert('时间分布图生成失败');  // 失败时提示错误
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取时间分布图失败：${error.response.data.error}`
                    : `获取时间分布图失败：${error.message}`;
                alert(errorMsg);  // 提示错误
                console.error('Error:', error);  // 打印错误日志
            } finally {
                this.isLoading = false;  // 完成加载
            }
        },
        // 获取情感分析数据
        async fetchSentiment() {
            try {
                this.isLoading = true;  // 开始加载
                console.log("Fetching sentiment analysis for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/sentiment', { bv: this.bvInput });
                if (response.data.counts && response.data.chart) {
                    this.sentimentData = response.data;  // 保存情感分析数据
                    console.log("Sentiment analysis data:", this.sentimentData);  // 打印情感分析数据
                } else {
                    this.sentimentData = null;  // 无效数据，清空
                    alert('情感分析结果无效或无数据');
                }
            } catch (error) {
                this.sentimentData = null;  // 清空情感数据
                const errorMsg = error.response && error.response.data.error 
                    ? `情感分析失败：${error.response.data.error}`
                    : `情感分析失败：${error.message}`;
                alert(errorMsg);  // 提示错误
                console.error('Error:', error);  // 打印错误日志
            } finally {
                this.isLoading = false;  // 完成加载
            }
        },
        // 获取弹幕时间占比图
        async fetchDanmakuTimeProportion() {
            try {
                this.isLoading = true;  // 开始加载
                console.log("Fetching danmaku time proportion for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_time_proportion', { bv: this.bvInput });
                if (response.data.image) {
                    this.timeProportionImage = response.data.image;  // 保存时间占比图
                } else {
                    alert('生成时间占比图失败：无有效数据');  // 无效数据，提示错误
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `生成时间占比图失败：${error.response.data.error}`
                    : `生成时间占比图失败：${error.message}`;
                alert(errorMsg);  // 提示错误
                console.error('Error:', error);  // 打印错误日志
            } finally {
                this.isLoading = false;  // 完成加载
            }
        },
        // 切换页面时获取新数据
        changePage(page) {
            if (page < 1 || page > this.totalPages) {
                alert(`页码超出范围（1-${this.totalPages}）`);  // 页码超出范围
                return;
            }
            this.currentPage = page;  // 设置当前页
            this.fetchDanmaku();  // 获取该页数据
        }
    },
    computed: {
        // 返回分页后的弹幕数据
        paginatedDanmaku() {
            return this.danmakuData;
        }
    }
});
