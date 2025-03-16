from modules.danmaku import get_video_cid, fetch_danmaku
from modules.utils import seconds_to_hms

def test_danmaku_fetch():
    bv = "BV1vjwmesE1L"  # 替换为你想测试的视频 BV 号
    try:
        # 获取 CID
        cid = get_video_cid(bv)
        print(f"CID: {cid}")

        # 获取弹幕数据
        danmaku = fetch_danmaku(cid)
        print(f"Total Danmaku Fetched: {len(danmaku)}")

        # 打印前 10 条弹幕
        for d in danmaku[:40]:
            print(d)

    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_danmaku_fetch()

以下是app.py的相关代码：
# API 路由：爬取弹幕数据 
# 弹幕数据接口：处理分页
# API 路由：爬取弹幕数据 
# 弹幕数据接口：处理分页
@app.route('/api/danmaku', methods=['POST'])
def danmaku():
    data = request.json
    bv_input = data.get('bv', '')  # 从前端获取 BV 号
    page = data.get('page', 1)  # 从前端获取当前页码，默认为1
    per_page = data.get('per_page', 10)  # 从前端获取每页显示的弹幕数，默认为10
    
    app_logger.debug(f"Received request for danmaku: BV={bv_input}, page={page}, per_page={per_page}")
    
    try:
        # 处理 BV 号，获取视频的 CID
        bv = handle_bv_input(bv_input)
        cid = get_video_cid(bv)
        
        # 获取完整的弹幕数据
        danmaku_data = fetch_danmaku(cid)
        
        # 如果弹幕数据为空，抛出异常
        if not danmaku_data:
            raise Exception("未获取到弹幕数据")
        
        # 计算分页范围
        start = (page - 1) * per_page
        end = start + per_page
        paginated_danmaku = danmaku_data[start:end]  # 截取当前页的数据
        
        # 计算总页数
        total_pages = (len(danmaku_data) + per_page - 1) // per_page
        
        # 返回数据，包括分页信息
        return jsonify({
            'danmaku': paginated_danmaku,  # 当前页的弹幕数据
            'total_pages': total_pages,    # 总页数
            'current_page': page           # 当前页码
        })
    except Exception as e:
        # 记录错误日志并返回错误信息
        app_logger.error(f"Error fetching danmaku: {str(e)}")
        return jsonify({'error': str(e)}), 400

以下是index.html相关代码：
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- 设置页面字符编码为UTF-8，确保中文显示正确 -->
    <meta charset="UTF-8">
    
    <!-- 设置视口，确保页面在移动设备上能够响应式显示 -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- 页面标题，显示在浏览器标签页 -->
    <title>B站视频信息查询</title>
    
    <!-- 引入外部样式表文件，样式定义放在css/styles.css文件中 -->
    <link rel="stylesheet" href="css/styles.css">
    
    <!-- 引入Vue.js框架，通过Vue.js实现前端的交互和数据绑定 -->
    <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.js"></script>
</head>
<body>
    <!-- Vue.js 应用的根容器，id="app" 用于Vue.js实例挂载 -->
    <div id="app">
        <!-- 页面主体容器 -->
        <div class="container">
            
            <!-- 主标题，描述当前页面功能 -->
            <h1>查询 B 站视频信息</h1>

            <!-- 用户输入框和查询按钮的容器 -->
            <div class="input-group">
                <!-- 输入框：使用 v-model 双向绑定用户输入的BV号或视频链接 -->
                <input v-model="bvInput" placeholder="请输入 BV 号 或 视频链接" class="input-field">
                
                <!-- 查询按钮：点击按钮时触发 fetchVideoInfo 方法，用于查询视频信息 -->
                <button @click="fetchVideoInfo" class="btn-primary">查询</button>
            </div>

            <!-- 视频信息区域：只有在 videoInfo 数据存在时才会显示 -->
            <div v-if="videoInfo" id="video-info" class="video-info">
                <!-- 视频信息标题 -->
                <h2>视频信息</h2>
                
                <!-- 显示视频标题 -->
                <div class="info-item">
                    <strong>标题：</strong><span>{{ videoInfo.title }}</span>
                </div>
                
                <!-- 显示UP主名称 -->
                <div class="info-item">
                    <strong>UP主：</strong><span>{{ videoInfo.up_name }}</span>
                </div>
                
                <!-- 显示UP主主页的链接 -->
                <div class="info-item">
                    <strong>UP主主页：</strong><a :href="videoInfo.up_link" target="_blank">{{ videoInfo.up_link }}</a>
                </div>
                
                <!-- 显示视频封面图片 -->
                <div class="info-item">
                    <strong>封面：</strong>
                    <!-- 封面图片容器 -->
                    <div class="cover-container">
                        <!-- 显示封面图片，动态绑定 src 属性为 videoInfo.cover -->
                        <img :src="videoInfo.cover" alt="封面" class="cover-image">
                    </div>
                </div>

                <!-- 查询弹幕按钮 -->
                <div class="input-group">
                    <button @click="fetchDanmaku" class="btn-primary">查询弹幕</button>
                </div>

                <!-- 弹幕数据展示部分 -->
                <div v-if="danmakuData.length > 0" class="danmaku-list">
                    <h2>弹幕列表</h2>
                    
                    <!-- 显示当前页的弹幕数据 -->
                    <table class="danmaku-table">
                        <thead>
                            <tr>
                                <th>发送时间</th>
                                <th>发送者哈希值</th>
                                <th>内容</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="d in paginatedDanmaku" :key="d.time">
                                <td>{{ d.time }}</td>
                                <td>{{ d.hash }}</td>
                                <td>{{ d.content }}</td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- 分页按钮 -->
                    <div class="pagination">
                        <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
                        <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                        <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages">下一页</button>
                    </div>
                </div>

                <!-- 如果没有弹幕数据，则显示提示信息 -->
                <div v-else>
                    <p>暂无弹幕数据，点击“查询弹幕”按钮获取。</p>
                </div>
            </div>
        </div>
    </div>

    <!-- 引入外部JavaScript文件，通常包含Vue实例和其他逻辑 -->
    <script src="js/app.js"></script>
</body>
</html>
以下是app.js相关代码：
new Vue({
    el: '#app',
    data: {
        bvInput: '',  // 用于绑定输入框的 BV 号或视频链接
        videoInfo: null,  // 存储视频信息
        danmakuData: [],  // 存储弹幕信息
        currentPage: 1,   // 当前页码
        itemsPerPage: 10, // 每页显示的弹幕数
        totalPages: 1    // 总页数
    },
    methods: {
        // 获取视频信息
        fetchVideoInfo() {
            console.log("Fetching video info for BV:", this.bvInput);

            fetch('http://127.0.0.1:5000/api/video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ bv: this.bvInput })
            })
            .then(response => {
                console.log('Response Status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.error) {
                    alert(data.error);
                } else {
                    this.videoInfo = data;  // 将返回的视频信息存储到 videoInfo 中
                }
            })
            .catch(error => {
                alert("发生错误: " + error);
                console.error('Error:', error);
            });
        },
        
        // 获取弹幕数据
        fetchDanmaku() {
            console.log("Fetching danmaku for BV:", this.bvInput);
        
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
                    this.danmakuData = data.danmaku;
                    this.totalPages = data.total_pages;
                    this.currentPage = data.current_page;
        
                    // 强制 Vue 更新视图
                    this.$forceUpdate();
                    console.log("Updated danmaku data:", this.danmakuData);
                }
            })
            .catch(error => {
                console.error("Error fetching danmaku:", error);
                alert("发生错误: " + error);
            });
        },
        
        
        
        // 切换页码
        changePage(page) {
            console.log("Changing to page:", page);
            if (page < 1 || page > this.totalPages) {
                console.warn("Invalid page number:", page);
                return;
            }
            this.currentPage = page;  // 更新当前页
            this.fetchDanmaku();  // 重新加载数据
        }
    },
    computed: {
        // 分页后的弹幕数据
        paginatedDanmaku() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            const end = start + this.itemsPerPage;
            const currentData = this.danmakuData.slice(start, end);
            console.log(`Current page: ${this.currentPage}, Paginated items:`, currentData);
            return currentData;
        }
    }
    
});
以下是danmaku.py相关：
import requests
import xml.etree.ElementTree as ET
from .utils import seconds_to_hms
from config import Config
# 请求头
headers = {
    'User-Agent': Config.USER_AGENT
}

# 获取视频的 cid
def get_video_cid(bv):
    url = f'https://api.bilibili.com/x/player/pagelist?bvid={bv}'
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()['data']
            if data:
                cid = data[0]['cid']  # 默认获取第一个分P的 cid
                return cid
            else:
                raise Exception("未能获取到视频的 CID")
        else:
            raise Exception(f"获取视频 CID 失败，状态码：{res.status_code}")
    except Exception as e:
        raise Exception(f"获取视频 CID 失败: {e}")

# 爬取弹幕数据
def fetch_danmaku(cid):
    danmaku_url = f'https://comment.bilibili.com/{cid}.xml'
    try:
        res = requests.get(danmaku_url, headers=headers)
        if res.status_code == 200:
            # 解析 XML 数据
            root = ET.fromstring(res.content)
            danmaku_list = []
            for d in root.findall('d'):
                attributes = d.attrib.get('p', '').split(',')
                time_in_seconds = attributes[0] if len(attributes) > 0 else '0'
                sender_hash = attributes[6] if len(attributes) > 6 else ''  # 获取发送者哈希值
                danmaku_content = d.text
                danmaku_list.append({
                    'time': seconds_to_hms(time_in_seconds),
                    'hash': sender_hash,
                    'content': danmaku_content
                })
            return danmaku_list
        else:
            raise Exception(f"获取弹幕数据失败，状态码：{res.status_code}")
    except Exception as e:
        raise Exception(f"获取弹幕数据失败: {e}")
