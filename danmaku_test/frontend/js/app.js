new Vue({
    el: '#app', // 指定 Vue 实例挂载的 DOM 元素，'#app' 是 CSS 选择器，表示 id="app"

    // 数据对象，定义 Vue 实例的状态，所有属性都是响应式的
    data: {
        bvInput: '', // 用户输入的 BV 号或视频链接，初始为空字符串，双向绑定到输入框
        videoInfo: null, // 存储从后端获取的视频信息（如标题、封面等），初始为 null
        danmakuData: [], // 存储从后端获取的完整弹幕数据，初始为空数组
        displayDanmaku: [], // 用于前端显示的弹幕数据（可能是全部或搜索结果），初始为空数组
        wordFrequency: [], // 存储词频统计结果，格式为 [[词, 次数], ...]，初始为空数组
        wordCloudImage: '', // 存储词云图的 Base64 编码字符串，初始为空字符串
        danmakuTimelineImage: '', // 存储弹幕时间分布图的 Base64 编码字符串，初始为空字符串
        currentPage: 1, // 当前显示的弹幕页码，初始为第 1 页
        itemsPerPage: 50, // 每页显示的弹幕条数，固定为 50
        totalPages: 1, // 弹幕数据的总页数，初始为 1，由后端返回或计算得出
        isLoading: false, // 加载状态标志，true 表示正在请求数据，初始为 false
        activeTab: 'video-info', // 当前激活的选项卡 ID，初始为 'video-info'（视频信息）
        searchKeyword: '', // 用户输入的弹幕搜索关键字，初始为空字符串
        sentimentData: null,
        tabs: [ // 选项卡配置数组，定义页面中的选项卡，不使用 Object.freeze 以允许动态修改
            { id: 'video-info', name: '视频信息' }, // 视频信息选项卡
            { id: 'danmaku', name: '弹幕列表' }, // 弹幕列表选项卡
            { id: 'word-frequency', name: '词频统计' }, // 词频统计选项卡
            { id: 'advanced-analysis', name: '高级分析' }, // 高级分析选项卡
            { id: 'sentiment', name: '情感分析' }
        ]
    },

    // 方法对象，定义 Vue 实例的行为逻辑
    methods: {
        // 获取视频信息的异步方法
        fetchVideoInfo() {
            this.isLoading = true; // 设置加载状态为 true，禁用按钮并显示加载提示
            console.log("Fetching video info for BV:", this.bvInput); // 调试：输出当前 BV 号
            // 使用 fetch 发送 POST 请求到后端 API
            fetch('http://127.0.0.1:5000/api/video', {
                method: 'POST', // 请求方法为 POST
                headers: { 'Content-Type': 'application/json' }, // 设置请求头为 JSON 格式
                body: JSON.stringify({ bv: this.bvInput }) // 将 BV 号转为 JSON 字符串作为请求体
            })
            .then(response => response.json()) // 将响应解析为 JSON
            .then(data => { // 处理返回的数据
                if (data.error) { // 如果后端返回错误
                    alert(data.error); // 弹出错误提示
                } else { // 如果成功
                    this.videoInfo = data; // 更新 videoInfo 数据
                    this.activeTab = 'video-info'; // 切换到视频信息选项卡
                }
            })
            .catch(error => { // 处理请求失败的情况
                alert(`获取视频信息失败: ${error.message}`); // 弹出错误提示
                console.error('Error:', error); // 在控制台记录详细错误
            })
            .finally(() => { // 无论成功或失败，最终执行
                this.isLoading = false; // 重置加载状态
            });
        },

        // 获取弹幕数据的异步方法
        fetchDanmaku() {
            this.isLoading = true; // 设置加载状态为 true
            console.log("Fetching danmaku for BV:", this.bvInput); // 调试：输出当前 BV 号
            // 使用 fetch 发送 POST 请求到后端 API
            fetch('http://127.0.0.1:5000/api/danmaku', {
                method: 'POST', // 请求方法为 POST
                headers: { 'Content-Type': 'application/json' }, // 设置请求头为 JSON 格式
                body: JSON.stringify({ // 请求体包含 BV 号、分页参数
                    bv: this.bvInput,
                    page: this.currentPage, // 当前页码
                    per_page: this.itemsPerPage,// 每页条数
                    keyword: this.searchKeyword // 添加关键字参数，空字符串表示获取全部
                })
            })
            .then(res => res.json()) // 将响应解析为 JSON
            .then(data => { // 处理返回的数据
                if (data.error) { // 如果后端返回错误
                    alert(data.error); // 弹出错误提示
                } else { // 如果成功
                    Vue.set(this, 'danmakuData', data.danmaku); // 更新完整弹幕数据（使用 Vue.set 确保响应式）
                    this.totalPages = data.total_pages || 1; // 更新总页数，默认 1
                    this.currentPage = data.current_page; // 更新当前页码
                }
            })
            .catch(error => { // 处理请求失败的情况
                alert(`获取弹幕失败: ${error.message}`); // 弹出错误提示
                console.error('Error:', error); // 在控制台记录详细错误
            })
            .finally(() => { // 无论成功或失败，最终执行
                this.isLoading = false; // 重置加载状态
            });
        },

        // 获取词频统计的异步方法（使用 axios）
        async fetchWordFrequency() {
            try {
                this.isLoading = true; // 设置加载状态为 true
                console.log("Fetching word frequency for BV:", this.bvInput); // 调试：输出当前 BV 号
                // 使用 axios 发送 POST 请求到后端 API
                const response = await axios.post('http://127.0.0.1:5000/api/word_frequency', {
                    bv: this.bvInput // 请求体包含 BV 号
                });
                if (response.data.top_words) { // 如果返回词频数据
                    this.wordFrequency = response.data.top_words; // 更新词频统计结果
                } else { // 如果数据为空
                    alert('词频数据为空'); // 弹出提示
                }
            } catch (error) { // 处理请求失败的情况
                console.error('获取词频失败:', error.response ? error.response.data : error); // 记录详细错误
                alert(`获取词频失败: ${error.response ? error.response.data.error : error.message}`); // 弹出错误提示
            } finally { // 无论成功或失败，最终执行
                this.isLoading = false; // 重置加载状态
            }
        },

        // 获取词云图的异步方法（使用 axios）
        async fetchWordCloud() {
            try {
                this.isLoading = true; // 设置加载状态为 true
                console.log("Fetching word cloud for BV:", this.bvInput); // 调试：输出当前 BV 号
                // 使用 axios 发送 POST 请求到后端 API
                const response = await axios.post('http://127.0.0.1:5000/api/word_cloud', {
                    bv: this.bvInput // 请求体包含 BV 号
                });
                if (response.data.image) { // 如果返回词云图数据
                    this.wordCloudImage = response.data.image; // 更新词云图 Base64 字符串
                } else { // 如果生成失败
                    alert('词云图生成失败'); // 弹出提示
                }
            } catch (error) { // 处理请求失败的情况
                console.error('获取词云失败:', error.response ? error.response.data : error); // 记录详细错误
                alert(`获取词云失败: ${error.response ? error.response.data.error : error.message}`); // 弹出错误提示
            } finally { // 无论成功或失败，最终执行
                this.isLoading = false; // 重置加载状态
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
        async fetchSentiment() {
            try {
                this.isLoading = true;
                const response = await axios.post('http://127.0.0.1:5000/api/sentiment', {
                    bv: this.bvInput
                });
                this.sentimentData = response.data;
            } catch (error) {
                console.error('情感分析失败:', error);
                alert(`情感分析失败: ${error.response?.data?.error || error.message}`);
            } finally {
                this.isLoading = false;
            }
        },
        // 切换弹幕页码的方法
        changePage(page) {
            if (page < 1 || page > this.totalPages) { // 检查页码是否超出范围
                alert(`页码超出范围（1-${this.totalPages}）`); // 提示用户
                return;
            }
            this.currentPage = page; // 更新当前页码
            this.fetchDanmaku(); // 重新获取该页的弹幕数据
        }
    },

    // 计算属性，用于动态计算数据
    computed: {
        // 返回当前用于分页的弹幕数据（当前直接返回完整数据，未实现前端分页）
        paginatedDanmaku() {
            return this.danmakuData; // 返回后端已分页的弹幕数据
        }
    }
});