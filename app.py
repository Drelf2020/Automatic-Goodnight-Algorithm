import re
import sys
import time
import json

import resource

from random import randint

from bilibili_api import live, sync
from bilibili_api.utils.Danmaku import Danmaku
from bilibili_api.utils.Credential import Credential

from TLineEdit import TLineEdit
from TPushButton import TPushButton
from RoundShadow import RoundShadow

from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class night_thread(QThread):
    def __init__(self, roomid, main):
        '全自动晚安机'
        super().__init__()

        self.main = main
        self.stopped = False

        if not roomid:
            if main.heavy_signal:
                main.heavy_signal.emit('房间号错误')
            return
        else:
            try:
                roomid = int(roomid)
            except Exception:
                if main.heavy_signal:
                    main.heavy_signal.emit('房间号错误')
                return

        self.roomid = roomid
        self.heavy_signal = main.heavy_signal
        self.send_signal = main.send_signal
        self.listening = '[{}]'.format(','.join(self.main.setting['listening_words']))
        self.listening = re.compile(self.listening)
        self.goodnight = self.main.setting['goodnight_words']

        self.credential = Credential(
            sessdata=main.setting['cookies']['sessdata'],
            bili_jct=main.setting['cookies']['bili_jct'],
            buvid3=main.setting['cookies']['buvid3']
        )

        self.check_room = live.LiveDanmaku(roomid)  # 接收弹幕, debug=True
        self.send_room = live.LiveRoom(roomid, credential=self.credential)  # 发送弹幕

        self.danmuku_list = []  # 储存一段时间晚安弹幕
        self.count_danmuku = 0  # 储存某时间点晚安弹幕
        self.total_danmuku = 0  # 统计一段时间总晚安弹幕
        self.last_time = 0  # 上一次储存弹幕时的时间戳

        @self.check_room.on('DANMU_MSG')
        async def on_danmaku(event):
            '接收弹幕并计算密度'
            info = event['data']['info']
            msg = info[1]  # 弹幕文本内容
            time = info[9]['ts']  # 时间戳
            if time > self.last_time:
                self.last_time = time
                self.danmuku_list.append(self.count_danmuku)  # 把上个时间戳记录的弹幕数储存并归零
                self.count_danmuku = 0
                self.total_danmuku += self.danmuku_list[-1]  # 总弹幕数增加
                if len(self.danmuku_list) > 5:  # 只记录最近 5 个时间戳内的弹幕 可改
                    self.total_danmuku -= self.danmuku_list.pop(0)  # 从总弹幕数总减去 删去了的时间戳内的弹幕数
            if self.listening.search(msg):
                self.count_danmuku += 1

    async def send_msg(self):
        '每 1 秒检测晚安弹幕密度 若超过阈值则随机发送晚安弹幕'
        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        print(f'[heartbeat][{timestr}][INFO] 晚安弹幕密度：'+str(self.total_danmuku)+' / 5s')
        if self.heavy_signal:
            self.heavy_signal.emit(str(self.total_danmuku)+' / 5s')
        if not self.stopped:
            if self.total_danmuku >= self.main.setting['limited_density']:  # 密度超过 25/5s 则发送晚安 可改
                try:
                    pos = randint(0, len(self.goodnight)-5)
                    timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                    print(f'[send_msg][{timestr}][INFO] 发送晚安弹幕：'+self.goodnight[pos])
                    await self.send_room.send_danmaku(Danmaku(self.goodnight[pos]))
                    if self.send_signal:
                        self.send_signal.emit(self.goodnight[pos])
                    self.goodnight.append(self.goodnight.pop(pos))
                except Exception as e:
                    if self.send_signal:
                        self.send_signal.emit('发送弹幕失败：'+str(e))
                    print('发送弹幕失败：'+str(e))

    def run(self):
        try:
            getattr(self, 'roomid')
        except Exception:
            self.main.running = False
            return
        try:
            sched = AsyncIOScheduler()  # 定时检测密度的任务调度器
            trigger = IntervalTrigger(seconds=self.main.setting['send_rate'])  # 定时器
            sched.add_job(self.send_msg, trigger)  # 添加任务
            sched.start()
            sync(self.check_room.connect())
        except Exception as e:
            with open('error.txt', 'w+', encoding='utf-8') as fp:
                fp.write('运行时错误，已初始化，错误原因：'+str(e))


class MainWindow(RoundShadow):
    heavy_signal = pyqtSignal(str)
    send_signal = pyqtSignal(str)

    def __init__(self, setting):
        self.rwidth = 315
        self.rheight = 285
        super(MainWindow, self).__init__(self.rwidth, self.rheight, r=8)
        self.setWindowIcon(QIcon(':/256.ico'))
        self.setting = setting
        self.running = False
        self.nt = None
        self.setTitle('全自动晚安机', location=Qt.AlignTop | Qt.AlignLeft)
        self.vbox = QVBoxLayout(self.bglab)
        self.vbox.setAlignment(Qt.AlignTop)

        def add_TLineEdit(i):
            tl = TLineEdit(i)
            tl.setMinimumHeight(50)
            tl.setMaximumHeight(50)
            self.vbox.addWidget(tl)
            return tl

        tls = [add_TLineEdit(i) for i in ['直播间号：', '弹幕密度：', '正在发送：']]
        tls[0].Edit.setText(str(setting['roomid']))

        self.heavy_signal.connect(lambda s: tls[1].Edit.setText(s))
        self.send_signal.connect(lambda s: tls[2].Edit.setText(s))
        self.hbox = QHBoxLayout()

        def add_btn(i):
            tp = TPushButton(r=(4, 4, 4, 4), color=[QColor(7, 188, 252), QColor(31, 200, 253), QColor(31, 200, 253)])
            tp.setTitle((Qt.white, QFont('微软雅黑', 13, QFont.Normal), i))
            tp.setMinimumHeight(40)
            self.hbox.addWidget(tp)
            return tp

        tps = [add_btn(i) for i in ['连接', '暂停']]

        def run_btn():
            if not self.running:
                tls[1].Edit.setText('连接中')
                self.nt = night_thread(tls[0].Edit.text(), self)
                self.nt.start()
                tls[2].Edit.setText('')
                self.running = True
            else:
                tls[1].Edit.setText('已连接')

        def stop_btn():
            if not self.nt:
                tls[2].Edit.setText('未连接')
            else:
                if not self.nt.stopped:
                    self.nt.stopped = True
                    tls[2].Edit.setText('已暂停')
                    tps[1].setTitle((Qt.white, QFont('微软雅黑', 13, QFont.Normal), '继续'))
                else:
                    self.nt.stopped = False
                    tls[2].Edit.setText('')
                    tps[1].setTitle((Qt.white, QFont('微软雅黑', 13, QFont.Normal), '暂停'))

        tps[0].clicked.connect(run_btn)
        tps[1].clicked.connect(stop_btn)

        self.vbox.addStretch(1)
        self.vbox.addLayout(self.hbox)


def check_setting(setting):
    if 'roomid' not in setting:
        raise Exception('缺少 roomid 参数')
    if 'cookies' not in setting:
        raise Exception('缺少 cookies 参数')
    if 'sessdata' not in setting['cookies']:
        raise Exception('缺少 cookies 参数')
    if 'bili_jct' not in setting['cookies']:
        raise Exception('缺少 cookies 参数')
    if 'buvid3' not in setting['cookies']:
        raise Exception('缺少 cookies 参数')
    if 'listening_words' not in setting:
        raise Exception('缺少 listening_words 参数')
    if 'goodnight_words' not in setting:
        raise Exception('缺少 goodnight_words 参数')
    if 'limited_density' not in setting:
        raise Exception('缺少 limited_density 参数')
    else:
        try:
            setting['limited_density'] = max(0, setting['limited_density'])
        except Exception as e:
            raise e
    if 'send_rate' not in setting:
        raise Exception('缺少 send_rate 参数')
    else:
        try:
            setting['send_rate'] = max(1, setting['send_rate'])
        except Exception as e:
            raise e


if __name__ == '__main__':

    standard_setting = {
        "roomid": "",
        "cookies": {
            "sessdata": "",
            "bili_jct": "",
            "buvid3": ""
        },
        "listening_words": ['晚安', '拜拜', '别走好吗'],
        "goodnight_words": ["晚安", "拜拜", "别走好吗", "晚安晚安", "还会再见吗", "早点睡吧", "海比晚安"],
        "limited_density": 25,
        "send_rate": 1
    }

    error = None

    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            setting = json.load(f)
            check_setting(setting)
    except Exception as e:
        error = str(e)
        setting = standard_setting
        with open('config.json', 'w+', encoding='utf-8') as fp:
            json.dump(standard_setting, fp, indent=4, ensure_ascii=False)

    app = QApplication(sys.argv)  # 新建窗口前必运行app
    win = MainWindow(setting)
    win.show()  # 显示主窗口
    if error:
        msgBox = QMessageBox.critical(win, u'配置文件错误，已初始化，请重新填写配置文件 <config.json>', u"错误原因："+error)
        sys.exit(0)
    for i in setting['cookies']:
        if not setting['cookies'][i]:
            msgBox = QMessageBox.critical(win, u'配置文件错误', u"错误原因："+i+' 项未填写')
            sys.exit(0)
    app.exec_()  # 等待直到登录窗口关闭
