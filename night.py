from bilibili_api import live
from bilibili_api.utils.Credential import Credential
from bilibili_api.utils.Danmaku import Danmaku
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from random import randint
import time


async def run(roomid, credential: dict, heavy_signal, send_signal, goodnight=['晚安', '拜拜', '别走好吗', '晚安晚安', '还会再见吗', '早点睡吧', '海比晚安']):
    '全自动晚安机'
    if not roomid:
        if heavy_signal:
            heavy_signal.emit('房间号错误')
        return False
    else:
        try:
            roomid = int(roomid)
        except Exception:
            if heavy_signal:
                heavy_signal.emit('房间号错误')
            return False
    credential = {
        'sessdata': '4d1ea22b%2C1655829387%2Cd0caf%2Ac1',
        'bili_jct': '61389bcafa9cdad234fa4f9e491d5e3a',
        'buvid3': '03D6FF48-55F8-4F43-AB48-316343A8E23670389infoc'
    }
    check_room = live.LiveDanmaku(roomid, debug=True)  # 接收弹幕
    send_room = live.LiveRoom(roomid, Credential(*credential))  # 发送弹幕
    sched = AsyncIOScheduler()  # 定时检测密度的任务调度器

    danmuku_list = []  # 储存一段时间晚安弹幕
    count_danmuku = 0  # 储存某时间点晚安弹幕
    total_danmuku = 0  # 统计一段时间总晚安弹幕
    last_time = 0  # 上一次储存弹幕时的时间戳

    @check_room.on('DANMU_MSG')
    async def on_danmaku(event):
        '接收弹幕并计算密度'
        nonlocal danmuku_list, count_danmuku, total_danmuku, last_time
        info = event['data']['info']
        msg = info[1]  # 弹幕文本内容
        time = info[9]['ts']  # 时间戳
        if time > last_time:
            last_time = time
            danmuku_list.append(count_danmuku)  # 把上个时间戳记录的弹幕数储存并归零
            count_danmuku = 0
            total_danmuku += danmuku_list[-1]  # 总弹幕数增加
            if len(danmuku_list) > 5:  # 只记录最近 5 个时间戳内的弹幕 可改
                total_danmuku -= danmuku_list.pop(0)  # 从总弹幕数总减去 删去了的时间戳内的弹幕数
        if '晚安' in msg or '拜拜' in msg or '别走好吗' in msg:
            count_danmuku += 1

    @sched.scheduled_job('interval', id='send_job', seconds=1)
    async def send_msg():
        '每 1 秒检测晚安弹幕密度 若超过阈值则随机发送晚安弹幕'
        nonlocal total_danmuku, goodnight
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        print(f'[heartbeat][{timestr}][INFO] 晚安弹幕密度：'+str(total_danmuku)+' / 5s')
        if heavy_signal:
            heavy_signal.emit(str(total_danmuku)+' / 5s')
        if total_danmuku >= 0:  # 密度超过 50/5s 则发送晚安 可改
            try:
                pos = randint(0, len(goodnight)-5)
                timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                print(f'[send_msg][{timestr}][INFO] 发送晚安弹幕：'+goodnight[pos])
                if send_signal:
                    send_signal.emit(goodnight[pos])
                await send_room.send_danmaku(Danmaku(goodnight[pos]))
                goodnight.append(goodnight.pop(pos))
            except Exception as e:
                print('发送弹幕失败：'+str(e))

    # 运行
    sched.start()
    await check_room.connect()
