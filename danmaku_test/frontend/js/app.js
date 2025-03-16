new Vue({
    el: '#app',
    data: {
        bvInput: '',
        videoInfo: null,
        danmakuData: [],
        wordFrequency: [],
        currentPage: 1,
        itemsPerPage: 50,
        totalPages: 1,
        wordCloudData: [],
        isLoading: false,
        activeTab: 'video-info', // 默认选项卡
        tabs: [
            { id: 'video-info', name: '视频信息' },
            { id: 'danmaku', name: '弹幕列表' },
            { id: 'word-frequency', name: '词频统计' },
            { id: 'advanced-analysis', name: '高级分析' } // 占位未来功能
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
                    this.activeTab = 'video-info'; // 默认显示视频信息
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
                    this.totalPages = data.total_pages || 1;
                    this.currentPage = data.current_page;
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
                if (response.data.word_cloud) {
                    this.wordCloudData = response.data.word_cloud;
                    this.$nextTick(() => { // 确保 DOM 更新后再渲染
                        this.renderWordCloud();
                    });
                } else {
                    alert('词云数据为空');
                }
            } catch (error) {
                console.error('获取词云失败:', error.response ? error.response.data : error);
                alert(`获取词云失败: ${error.response ? error.response.data.error : error.message}`);
            } finally {
                this.isLoading = false;
            }
        },
        renderWordCloud() {
            const options = {
                list: this.wordCloudData,
                gridSize: 10,
                weightFactor: 2,
                fontFamily: 'Arial, sans-serif',
                color: 'random-dark',
                backgroundColor: '#f5f5f5',
                rotateRatio: 0.5,
                rotationSteps: 2
            };
            WordCloud(document.getElementById('word-cloud'), options);
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