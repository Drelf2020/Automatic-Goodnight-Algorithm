import asyncio
import re
import resource
import sys
import time
from random import randint

import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bilibili_api import live
from bilibili_api.utils.Credential import Credential
from bilibili_api.utils.Danmaku import Danmaku
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMessageBox, QVBoxLayout

from bili import BILI
from RoundShadow import RoundShadow
from TLabel import TLabel
from TLineEdit import TLineEdit
from TPushButton import TPushButton


class night_thread(QThread):
    def __init__(self, roomid, main, debug=False):
        '全自动晚安机'
        super().__init__()

        self.main = main
        self.stopped = False
        self.debug = debug

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
        self.real_signal = main.real_signal
        self.heavy_signal = main.heavy_signal
        self.send_signal = main.send_signal
        self.listening = '({})'.format(')|('.join(self.main.setting['listening_words']))
        self.listening = re.compile(self.listening)
        self.goodnight = self.main.setting['goodnight_words']

        self.credential = Credential(
            sessdata=main.setting['cookies']['sessdata'],
            bili_jct=main.setting['cookies']['bili_jct']
        )

        self.check_room = live.LiveDanmaku(roomid)  # 接收弹幕, debug=True
        self.send_room = live.LiveRoom(roomid, credential=self.credential)  # 发送弹幕

        self.real_danmuku = 0
        self.danmuku_list = []  # 储存一段时间晚安弹幕
        self.count_danmuku = 0  # 储存某时间点晚安弹幕
        self.total_danmuku = 0  # 统计一段时间总晚安弹幕
        self.last_time = 0  # 上一次储存弹幕时的时间戳

        @self.check_room.on('DANMU_MSG')
        async def on_danmaku(event):
            '接收弹幕并计算密度'
            self.real_danmuku += 1
            info = event['data']['info']
            time = info[9]['ts']  # 时间戳
            if time > self.last_time:
                self.last_time = time
                if self.real_signal:
                    self.real_signal.emit(str(self.real_danmuku)+' / s')
                self.real_danmuku = 0
                self.danmuku_list.append(self.count_danmuku)  # 把上个时间戳记录的弹幕数储存并归零
                self.count_danmuku = 0
                self.total_danmuku += self.danmuku_list[-1]  # 总弹幕数增加
                if len(self.danmuku_list) > 5:  # 只记录最近 5 个时间戳内的弹幕 可改
                    self.total_danmuku -= self.danmuku_list.pop(0)  # 从总弹幕数总减去 删去了的时间戳内的弹幕数
            if self.listening.search(info[1]):
                if debug:
                    print(self.listening.search(info[1]), info[1])
                self.count_danmuku += 1

    async def send_msg(self):
        '每 1 秒检测晚安弹幕密度 若超过阈值则随机发送晚安弹幕'
        if self.debug:
            timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            print(f'[heartbeat][{timestr}][INFO] 晚安弹幕密度：'+str(self.total_danmuku)+' / 5s')
        if self.heavy_signal:
            self.heavy_signal.emit(str(self.total_danmuku)+' / 5 s')
        if not self.stopped:
            if self.total_danmuku >= self.main.setting['limited_density']:  # 密度超过 25/5s 则发送晚安 可改
                try:
                    pos = randint(0, len(self.goodnight)-5)
                    if self.debug:
                        timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                        print(f'[send_msg][{timestr}][INFO] 发送晚安弹幕：'+self.goodnight[pos])
                    await self.send_room.send_danmaku(Danmaku(self.goodnight[pos]))
                    if self.send_signal:
                        self.send_signal.emit(self.goodnight[pos])
                    self.goodnight.append(self.goodnight.pop(pos))
                except Exception as e:
                    if self.send_signal:
                        self.send_signal.emit('发送弹幕失败：'+str(e))
                    if self.debug:
                        print('发送弹幕失败：'+str(e))

    def run(self):
        try:
            getattr(self, 'roomid')
        except Exception:
            self.main.running = False
            return
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sched = AsyncIOScheduler()  # 定时检测密度的任务调度器
            trigger = IntervalTrigger(seconds=self.main.setting['send_rate'])  # 定时器
            sched.add_job(self.send_msg, trigger)  # 添加任务
            sched.start()
            loop.run_until_complete(self.check_room.connect())
        except Exception as e:
            with open('error.txt', 'w+', encoding='utf-8') as fp:
                fp.write('运行时错误，已初始化，错误原因：'+str(e))


class MainWindow(RoundShadow):
    real_signal = pyqtSignal(str)
    heavy_signal = pyqtSignal(str)
    send_signal = pyqtSignal(str)

    def __init__(self, setting):
        self.rwidth = 350 # 850
        self.rheight = 335 # 700
        super(MainWindow, self).__init__(self.rwidth, self.rheight, title=' 全自动晚安机')
        self.setWindowIcon(QIcon(':/256.ico'))
        self.setting = setting
        self.running = False
        self.nt = None
        self.box = QHBoxLayout(self.bglab)
        self.box.addWidget(TLabel(color='#E50000'), 2)

        self.vbox = QVBoxLayout()
        self.vbox.setAlignment(Qt.AlignTop)

        def add_TLineEdit(title):
            tl = TLineEdit(title)
            tl.setMinimumHeight(50)
            tl.setMaximumHeight(50)
            self.vbox.addWidget(tl)
            return tl

        tls = [add_TLineEdit(_) for _ in ['直播间号：', '实时密度：', '晚安密度：', '正在发送：']]
        tls[0].setText(str(setting['roomid']))

        self.real_signal.connect(lambda s: tls[1].setText(s))
        self.heavy_signal.connect(lambda s: tls[2].setText(s))
        self.send_signal.connect(lambda s: tls[3].setText(s))
        self.hbox = QHBoxLayout()
        self.hbox.addStretch(3)

        def add_btn(title):
            tp = TPushButton(r=(4, 4, 4, 4), color=[QColor(7, 188, 252), QColor(31, 200, 253), QColor(31, 200, 253)])
            tp.setTitle((Qt.white, QFont('HarmonyOS Sans SC', 13), title))
            tp.setMinimumSize(120, 40)
            self.hbox.addWidget(tp, 1)
            return tp

        tps = [add_btn(_) for _ in ['连接', '暂停']]

        def run_btn():
            if not self.running:
                tls[1].setText('连接中')
                self.nt = night_thread(tls[0].text(), self)
                self.nt.start()
                tls[3].setText('')
                self.running = True
            else:
                tls[1].setText('已连接')

        def stop_btn():
            if not self.nt:
                tls[3].setText('未连接')
            else:
                if not self.nt.stopped:
                    self.nt.stopped = True
                    tls[3].setText('已暂停')
                    tps[1].setTitle((Qt.white, QFont('HarmonyOS Sans SC', 13), '继续'))
                else:
                    self.nt.stopped = False
                    tls[3].setText('')
                    tps[1].setTitle((Qt.white, QFont('HarmonyOS Sans SC', 13), '暂停'))

        tps[0].clicked.connect(run_btn)
        tps[1].clicked.connect(stop_btn)

        self.vbox.addStretch()
        self.vbox.addLayout(self.hbox)
        self.box.addLayout(self.vbox, 6)

def check_setting(setting):
    assert 'roomid' in setting, '缺少 roomid 参数'
    assert 'cookies' in setting, '缺少 cookies 参数'
    assert 'sessdata' in setting['cookies'], '缺少 sessdata 参数'
    assert 'bili_jct' in setting['cookies'], '缺少 bili_jct 参数'
    assert 'listening_words' in setting, '缺少 listening_words 参数'
    assert 'goodnight_words' in setting, '缺少 goodnight_words 参数'
    assert 'limited_density' in setting and setting['limited_density'] >= 0, 'limited_density 参数错误'
    assert 'send_rate' in setting and setting['send_rate'] >= 1, 'send_rate 参数错误'

if __name__ == '__main__':

    standard_setting = {
        "roomid": 21452505,
        "cookies": {
            "sessdata": "",
            "bili_jct": ""
        },
        "listening_words": ['晚安', '拜拜'],
        "goodnight_words": ["晚安", "拜拜", "别走好吗", "晚安晚安", "还会再见吗", "早点睡吧", "海比晚安"],
        "limited_density": 25,
        "send_rate": 1.05
    }

    app = QApplication(sys.argv)  # 新建窗口前必运行app
    
    try:
        with open('config.yml', 'r+', encoding='utf-8') as fp:
            setting = yaml.load(fp, Loader=yaml.Loader)
            check_setting(setting)
    except Exception as e:
        setting = standard_setting

    if not (bili := BILI(**setting['cookies'])).check():
        QMessageBox.critical(None, '请扫码登录', '点击确定后会自动打开二维码，如果未自动打开图片，请在此目录中寻找 qrcode.png 进行扫码。')
        setting['cookies'] = bili.login(app)
        with open('config.yml', 'w+', encoding='utf-8') as fp:
            yaml.dump(setting, fp, allow_unicode=True)
    win = MainWindow(setting)
    win.show()  # 显示主窗口
    app.exec_()  # 等待直到登录窗口关闭
