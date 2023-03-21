import time
from typing import Dict, TypedDict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bilibili_api import live, sync


class Gift(TypedDict):
    '''用户赠送礼物列表
    username: 用户名
    last_gift_time: 最后一次赠送礼物时时间戳
    gift_list: 赠送的礼物字典，格式 礼物名: 数量'''
    username: str
    last_gift_time: int
    gift_list: Dict[str, int]

user_list: Dict[int, Gift] = dict()
room = live.LiveDanmaku(21452505)
sched = AsyncIOScheduler(timezone="Asia/Shanghai")  # 定时任务框架

@room.on('SEND_GIFT')
async def on_gift(event):
    '记录礼物'
    info = event['data']['data']
    uid = info['uid']
    user = user_list.get(uid)
    if user:
        # 如果用户列表中有该用户 则更新他的礼物字典以及礼物时间戳
        num = user['gift_list'].get(info['giftName'], 0)
        user['gift_list'][info['giftName']] = num + info['num']
        user['last_gift_time'] = int(time.time())
    else:
        # 不存在则以现在时间及礼物新建 Gift 对象
        user_list[uid] = Gift(
            username=info['uname'],
            last_gift_time=int(time.time()),
            gift_list={info['giftName']: info['num']}
        )
        # 开启一个监控
        sched.add_job(check, 'interval', seconds=1, args=[uid], id=str(uid))

async def check(uid: int):
    '判断是否超过阈值并输出'
    user = user_list.get(uid)
    if user:
        tt = time.time()
        if tt - user.get('last_gift_time', 0) > 5:  # 此处的 5 即需求中的 n 表示秒数
            sched.remove_job(str(uid))  # 移除该监控任务
            whatever = user_list.pop(uid)  # 将该用户从列表中弹出并打印
            out = '谢谢' + whatever['username'] + '赠送的' + '、'.join([str(v) + '个' + k for k, v in whatever['gift_list'].items()])
            print(out)

if __name__ == '__main__':
    sched.start()  # 启动定时任务
    sync(room.connect())  # 连接直播间
