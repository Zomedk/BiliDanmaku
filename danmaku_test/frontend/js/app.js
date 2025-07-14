// 检查登录状态
if (!localStorage.getItem('isLoggedIn')) {
    window.location.href = '/login.html';
}

new Vue({
    el: '#app',
    data: {
        bvInput: '',
        videoInfo: null,
        danmakuData: [],
        wordFrequency: [],
        wordCloudImage: '',
        danmakuTimelineImage: '',
        timeProportionImage: '',
        currentPage: 1,
        itemsPerPage: 50,
        totalPages: 1,
        isLoading: false,
        activeTab: 'video-info',
        searchKeyword: '',
        sentimentData: null,
        sortBy: 'time',
        sortOrder: 'asc',
        pageInput: null,
        activeUsers: [],
        selectedUserUid: '',
        userDanmakuList: [],
        showUserDanmakuModal: false,
        userHashInput: '',
        showUserDanmakuResult: false,
        lengthDistribution: null,
        colorDistribution: [],
        danmakuSummary: null,
        tabs: [
            { id: 'video-info', name: '视频信息' },
            { id: 'danmaku', name: '弹幕列表' },
            { id: 'word-frequency', name: '词频统计' },
            { id: 'advanced-analysis', name: '高级分析' },
            { id: 'sentiment', name: '情感分析' },
            { id: 'time-proportion', name: '弹幕时间占比' },
            { id: 'danmaku-length', name: '长度分布' },
            { id: 'danmaku-color', name: '颜色分布' },
            { id: 'danmaku-summary', name: '弹幕总结' } 
        ]
    },
    methods: {
        onChartError() {
            alert('情感分析图表加载失败');
            this.sentimentData = null;
        },
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
                    alert(`获取视频信息失败：${data.error}`);
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
        async fetchDanmaku() {
            if (this.isLoading) return;
            this.isLoading = true;
            console.log("Fetching danmaku for BV:", this.bvInput, "Sort:", this.sortBy, this.sortOrder, "Page:", this.currentPage);
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
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                return res.json();
            })
            .then(data => {
                console.log("Received danmaku:", data.danmaku.slice(0, 5));
                if (data.error) {
                    alert(`获取弹幕失败：${data.error}`);
                    this.danmakuData = [];
                } else {
                    this.danmakuData = data.danmaku || [];
                    this.totalPages = data.total_pages || 1;
                    this.currentPage = data.current_page || 1;
                }
            })
            .catch(error => {
                alert(`获取弹幕失败: ${error.message}`);
                console.error('Error:', error);
                this.danmakuData = [];
            })
            .finally(() => {
                this.isLoading = false;
            });
        },
        async fetchUserDanmaku() {
            if (this.isLoading || !this.userHashInput) return;
            this.isLoading = true;
            this.showUserDanmakuResult = true;
            
            try {
                const response = await axios.get('http://127.0.0.1:5000/api/user_danmaku', {
                    params: {
                        hash: this.userHashInput,
                        bv: this.bvInput
                    }
                });
                
                if (response.data.error) {
                    throw new Error(response.data.error);
                }
        
                this.selectedUserUid = response.data.uid;
                this.userDanmakuList = response.data.danmaku || [];
                
                if (this.userDanmakuList.length === 0) {
                    this.$message.warning('未找到该用户的弹幕记录');
                }
            } catch (error) {
                console.error('用户弹幕查询失败:', error);
                this.$message.error(`查询失败: ${error.message}`);
                this.userDanmakuList = [];
            } finally {
                this.isLoading = false;
            }
        },
        changePage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.pageInput = page;
                this.fetchDanmaku();
            }
        },
        jumpToPage() {
            const page = parseInt(this.pageInput);
            if (!isNaN(page) && page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.fetchDanmaku();
            } else {
                alert(`请输入 1 到 ${this.totalPages} 之间的页码`);
                this.pageInput = null;
            }
        },
        sortBy(column) {
            if (this.isLoading) return;
            console.log("Sorting by:", column);
            if (this.sortBy === column) {
                this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortBy = column;
                this.sortOrder = 'asc';
            }
            this.currentPage = 1;
            this.pageInput = 1;
            this.fetchDanmaku();
        },
        async fetchWordFrequency() {
            try {
                this.isLoading = true;
                console.log("Fetching word frequency for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/word_frequency', { bv: this.bvInput });
                if (response.data.top_words) {
                    console.log("Received word frequency:", response.data.top_words.slice(0, 5));
                    this.wordFrequency = response.data.top_words;
                } else {
                    alert('词频数据为空');
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取词频失败：${error.response.data.error}`
                    : `获取词频失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchWordCloud() {
            try {
                this.isLoading = true;
                console.log("Fetching word cloud for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/word_cloud', { bv: this.bvInput });
                if (response.data.image) {
                    this.wordCloudImage = response.data.image;
                } else {
                    alert('词云图生成失败');
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取词云失败：${error.response.data.error}`
                    : `获取词云失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchDanmakuTimeline() {
            try {
                this.isLoading = true;
                console.log("Fetching danmaku timeline for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_timeline', { bv: this.bvInput });
                if (response.data.image) {
                    this.danmakuTimelineImage = response.data.image;
                } else {
                    alert('时间分布图生成失败');
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取时间分布图失败：${error.response.data.error}`
                    : `获取时间分布图失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchActiveUsers() {
            if (this.isLoading) return;
            this.isLoading = true;
            try {
                const res = await axios.get('http://127.0.0.1:5000/api/active_users', { params: { bv: this.bvInput } });
                this.activeUsers = res.data.active_users || [];
            } catch (err) {
                console.error('获取活跃用户失败:', err);
                alert('活跃用户排行榜获取失败');
            } finally {
                this.isLoading = false;
            }
        },
        async fetchUserUid(userHash) {
            try {
                const res = await axios.get('http://127.0.0.1:5000/api/user_uid', {
                    params: {
                        hash: userHash,
                        bv: this.bvInput
                    }
                });
                const { uid } = res.data;
                if (!uid) {
                    alert('哈希转 UID 失败');
                    return;
                }
                this.selectedUserUid = uid;
            } catch (err) {
                console.error('获取 UID 失败', err);
                alert('获取 UID 失败');
            }
        },
        async fetchSentiment() {
            try {
                this.isLoading = true;
                console.log("Fetching sentiment analysis for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/sentiment', { bv: this.bvInput });
                if (response.data.counts && response.data.chart) {
                    this.sentimentData = response.data;
                    console.log("Sentiment analysis data:", this.sentimentData);
                } else {
                    this.sentimentData = null;
                    alert('情感分析结果无效或无数据');
                }
            } catch (error) {
                this.sentimentData = null;
                const errorMsg = error.response && error.response.data.error 
                    ? `情感分析失败：${error.response.data.error}`
                    : `情感分析失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchDanmakuTimeProportion() {
            try {
                this.isLoading = true;
                console.log("Fetching danmaku time proportion for BV:", this.bvInput);
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_time_proportion', { bv: this.bvInput });
                if (response.data.image) {
                    this.timeProportionImage = response.data.image;
                } else {
                    alert('生成时间占比图失败：无有效数据');
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `生成时间占比图失败：${error.response.data.error}`
                    : `生成时间占比图失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchDanmakuLength() {
            if (!this.videoInfo || !this.videoInfo.cid) {
                alert('请先查询视频信息');
                this.isLoading = false;
                return;
            }
            try {
                this.isLoading = true;
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_length', { cid: this.videoInfo.cid });
                if (response.data.error) {
                    alert(`获取弹幕长度分布失败：${response.data.error}`);
                } else {
                    console.log('Length distribution:', response.data);
                    this.lengthDistribution = response.data;
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取弹幕长度分布失败：${error.response.data.error}`
                    : `获取弹幕长度分布失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchDanmakuColor() {
            if (!this.videoInfo || !this.videoInfo.cid) {
                alert('请先查询视频信息');
                this.isLoading = false;
                return;
            }
            try {
                this.isLoading = true;
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_color', { cid: this.videoInfo.cid });
                if (response.data.error) {
                    alert(`获取弹幕颜色分布失败：${response.data.error}`);
                } else {
                    console.log('Color distribution:', response.data);
                    this.colorDistribution = response.data;
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取弹幕颜色分布失败：${error.response.data.error}`
                    : `获取弹幕颜色分布失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        },
        async fetchDanmakuSummary() {
            if (!this.videoInfo || !this.videoInfo.cid) {
                alert('请先查询视频信息');
                this.isLoading = false;
                return;
            }
            try {
                this.isLoading = true;
                const response = await axios.post('http://127.0.0.1:5000/api/danmaku_summary', { cid: this.videoInfo.cid });
                if (response.data.error) {
                    alert(`获取弹幕总结失败：${response.data.error}`);
                } else {
                    console.log('Danmaku summary:', response.data);
                    this.danmakuSummary = response.data;
                }
            } catch (error) {
                const errorMsg = error.response && error.response.data.error 
                    ? `获取弹幕总结失败：${error.response.data.error}`
                    : `获取弹幕总结失败：${error.message}`;
                alert(errorMsg);
                console.error('Error:', error);
            } finally {
                this.isLoading = false;
            }
        }
    },
    computed: {
        paginatedDanmaku() {
            return this.danmakuData;
        }
    }
});