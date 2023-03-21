import asyncio

import httpx
import qrcode
from bilibili_api import Credential, user
from bilibili_api.live import Danmaku, LiveRoom
from RoundShadow import RoundShadow
from PyQt5.QtWidgets import QLabel
from PIL import Image

Headers = {
    'Connection': 'keep-alive',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
}

class BILI:
    credential: Credential

    def __bool__(self):
        return self.credential.has_bili_jct() and self.credential.has_sessdata()

    def __init__(self, bili_jct: str = None, buvid3: str = None, sessdata: str = None):
        self.credential = Credential(sessdata, bili_jct, buvid3)

    def login(self, app):
        '通过扫描二维码模拟登录B站并获取cookies'

        oauthKey: str = ''
        win = RoundShadow(400, 450, title='qrcode')

        async def get_qrcode():
            async with httpx.AsyncClient(headers=Headers) as session:
                # 获取 oauthKey 以生成二维码
                r = await session.get('https://passport.bilibili.com/qrcode/getLoginUrl')
                global oauthKey
                oauthKey = r.json()['data']['oauthKey']  # 认证密钥

                # 生成图片展示并保存
                qrimg = qrcode.make(r.json()['data']['url'])
                qrimg.save('qrcode.png')

                qimage = qrimg.resize((400, 400), Image.ANTIALIAS).toqpixmap()
                QLabel(win.bglab).setPixmap(qimage)
                win.show()
                app.exec_()
            
        async def check_loop():
            async with httpx.AsyncClient(headers=Headers) as session:
                flag = True  # 循环标志物
                while flag:
                    await asyncio.sleep(3)  # 间隔 3 秒轮询扫码状态
                    try:
                        global oauthKey
                        r = await session.post('https://passport.bilibili.com/qrcode/getLoginInfo', data={'oauthKey': oauthKey})
                        js = r.json()
                        if js['status']:
                            await session.get(js['data']['url'])  # 访问此网站更新cookies
                            flag = False
                            cookies = session.cookies
                    except Exception as e:
                        print(e, e.__traceback__.tb_lineno)
                        break
                else:
                    self.credential = Credential(**{cookie.lower(): cookies[cookie] for cookie in ['SESSDATA', 'bili_jct']})
                print('finish')
                win.close_signal.emit()

        asyncio.run(asyncio.wait([get_qrcode(), check_loop()]))
        return {'sessdata': self.credential.sessdata, 'bili_jct': self.credential.bili_jct}

    async def checkDanmaku(self):
        if not self:
            return -101
        try:
            return await LiveRoom(14703541, self.credential).send_danmaku(Danmaku('checkDanmaku()'))
        except Exception as e:
            print(e.msg)
            return e.code

    def check(self):
        code = asyncio.run(self.checkDanmaku())
        return code not in [-400, -101, -111]

    async def get_info(self):
        return await user.get_self_info(self.credential)
