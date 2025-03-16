new Vue({
    el: '#app',
    data: {
        bvInput: '',
        videoInfo: null,
        danmakuData: [],
        displayDanmaku: [], // 用于显示的弹幕（查询或全部）
        wordFrequency: [],
        wordCloudImage: '', // 存储词云图 Base64
        danmakuTimelineImage: '', // 存储折线图 Base64
        currentPage: 1,
        itemsPerPage: 50,
        totalPages: 1,
        isLoading: false,
        activeTab: 'video-info',
        searchKeyword: '', // 新增：搜索关键字
        tabs: [
            { id: 'video-info', name: '视频信息' },
            { id: 'danmaku', name: '弹幕列表' },
            { id: 'word-frequency', name: '词频统计' },
            { id: 'advanced-analysis', name: '高级分析' }
        ]
    },
    methods: {
        fetchVideoInfo() {
            this.isLoading = true;
            console.log("Fetching video info for BV:", this.bvInput);
            fetch('http://127.0.0.1:5000/api/video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bv: this.bvInput })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    this.videoInfo = data;
                    this.activeTab = 'video-info';
                }
            })
            .catch(error => {
                alert(`获取视频信息失败: ${error.message}`);
                console.error('Error:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
        },
        fetchDanmaku() {
            this.isLoading = true;
            console.log("Fetching danmaku for BV:", this.bvInput);
            fetch('http://127.0.0.1:5000/api/danmaku', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bv: this.bvInput, page: this.currentPage, per_page: this.itemsPerPage })
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    Vue.set(this, 'danmakuData', data.danmaku);
                    Vue.set(this, 'displayDanmaku', data.danmaku); // 初始化显示数据
                    this.totalPages = data.total_pages || 1;
                    this.currentPage = data.current_page;
                    this.searchKeyword = ''; // 重置搜索关键字
                }
            })
            .catch(error => {
                alert(`获取弹幕失败: ${error.message}`);
                console.error('Error:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
        },
        async fetchWordFrequency() {
            try {
                this.isLoading = true;
                console.log("Fetching word frequency for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/word_frequency', {
                    bv: this.bvInput
                });
                if (response.data.top_words) {
                    this.wordFrequency = response.data.top_words;
                } else {
                    alert('词频数据为空');
                }
            } catch (error) {
                console.error('获取词频失败:', error.response ? error.response.data : error);
                alert(`获取词频失败: ${error.response ? error.response.data.error : error.message}`);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchWordCloud() {
            try {
                this.isLoading = true;
                console.log("Fetching word cloud for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/word_cloud', {
                    bv: this.bvInput
                });
                if (response.data.image) {
                    this.wordCloudImage = response.data.image;
                } else {
                    alert('词云图生成失败');
                }
            } catch (error) {
                console.error('获取词云失败:', error.response ? error.response.data : error);
                alert(`获取词云失败: ${error.response ? error.response.data.error : error.message}`);
            } finally {
                this.isLoading = false;
            }
        },
        // 获取弹幕时间分布图
        async fetchDanmakuTimeline() {
            try {
                this.isLoading = true;
                console.log("Fetching danmaku timeline for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_timeline', {
                    bv: this.bvInput
                });
                if (response.data.image) {
                    this.danmakuTimelineImage = response.data.image;
                } else {
                    alert('时间分布图生成失败');
                }
            } catch (error) {
                console.error('获取时间分布图失败:', error.response ? error.response.data : error);
                alert(`获取时间分布图失败: ${error.response ? error.response.data.error : error.message}`);
            } finally {
                this.isLoading = false;
            }
        },
        // 新增：搜索弹幕
        searchDanmaku() {
            if (!this.danmakuData.length) {
                alert('请先查询弹幕数据');
                return;
            }
            this.isLoading = true;
            console.log("Searching danmaku with keyword:", this.searchKeyword);
            
            if (this.searchKeyword.trim() === '') {
                // 如果关键字为空，显示所有弹幕
                this.displayDanmaku = [...this.danmakuData];
            } else {
                // 过滤包含关键字的弹幕
                this.displayDanmaku = this.danmakuData.filter(d => 
                    d.content && d.content.includes(this.searchKeyword)
                );
            }
            
            // 重置分页
            this.currentPage = 1;
            this.totalPages = Math.ceil(this.displayDanmaku.length / this.itemsPerPage);
            this.isLoading = false;
        },
        changePage(page) {
            if (page < 1 || page > this.totalPages) {
                alert(`页码超出范围（1-${this.totalPages}）`);
                return;
            }
            this.currentPage = page;
            this.fetchDanmaku();
        }
    },
    computed: {
        paginatedDanmaku() {
            return this.danmakuData;
        }
    }
});