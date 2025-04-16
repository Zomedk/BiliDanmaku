from modules.danmaku import get_video_cid, fetch_danmaku
from modules.logger import app_logger
bv = "BV1qxZSYHEoT"  # 替换为有效 BV 号
cid = get_video_cid(bv)
data = fetch_danmaku(cid)
app_logger.debug(f"Danmaku type: {type(data)}, length: {len(data)}, sample: {data[:5]}")