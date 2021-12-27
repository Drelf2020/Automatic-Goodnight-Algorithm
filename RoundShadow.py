from PyQt5.QtCore import Qt, QRectF, QRect
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QFont
from PyQt5.QtWidgets import QPushButton, QDesktopWidget, QMainWindow
from TLabel import TLabel


class MyButton(QPushButton):
    MINI = 0
    CLOSE = 1

    def __init__(self, patten, parent=None):
        super(MyButton, self).__init__(parent)
        self.patten = patten
        self.choice = 0
        self.color = [QColor(0, 0, 0, 0),
                      QColor(255, 84, 57) if patten else QColor(255, 255, 255, 100),
                      QColor(224, 74, 50) if patten else QColor(255, 255, 255, 125)]

    def enterEvent(self, QMouseEvent):
        self.choice = 1

    def mousePressEvent(self, QMouseEvent):
        self.choice = 2
        super(MyButton, self).mousePressEvent(QMouseEvent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.choice = 1
        super(MyButton, self).mouseReleaseEvent(QMouseEvent)

    def leaveEvent(self, QMouseEvent):
        self.choice = 0

    def paintEvent(self, event):
        pat = QPainter(self)
        pat.setRenderHint(pat.Antialiasing)  # 抗锯齿
        pat.setPen(Qt.NoPen)
        pat.setBrush(self.color[self.choice])
        pat.drawRoundedRect(QRect(0, 0, self.width(), self.height()), self.width()/2, self.height()/2)
        if self.patten == self.CLOSE:
            x, y, r = self.width()/2-3, self.height()/2-3, self.width()/12
            pat.translate(x+3, y+3)
            pat.rotate(-45)
            pat.setPen(Qt.white)
            pat.setBrush(Qt.white)
            pat.drawRoundedRect(QRect(-x, -r/2, 2*x, r), r/2, r/2)
            pat.drawRoundedRect(QRect(-r/2, -y, r, 2*y), r/2, r/2)
        elif self.patten == self.MINI:
            pat.setPen(Qt.white)
            pat.setBrush(Qt.white)
            pat.drawRoundedRect(QRect(self.width()/5, self.height()/2, self.width()*3/5, self.height()/12), self.height()/24, self.height()/24)


class RoundShadow(QMainWindow):
    '''
    圆角边框类
    width, height: 去掉边框后界面的长宽
    setting: 窗口配色设置
    r: 界面圆角半径
    s: 阴影扩散范围
    img: 背景图片
    title: 界面标题
    '''
    def __init__(self, width, height, setting=None, r=16, s=8, img=None, title=None, parent=None):
        super(RoundShadow, self).__init__(parent)
        self.r = r
        self.s = s
        self.setting = setting
        # m_drag 用于判断是否可以移动窗口
        self.m_drag = False
        self.m_DragPosition = None
        # 设置阴影
        self.setShadow()
        # 初始化窗口
        self.__initUI(width, height, img, title)
        # 窗口居中
        self.center()

    def __initUI(self, width, height, img, title):
        # 设置窗口大小为界面大小加上两倍阴影扩散距离
        self.resize(width+2*self.s, height+2*self.s)
        # 设置窗口无边框和背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # 设置标题栏
        tt_height = 40
        self.ttlab = TLabel(round=(self.r, 0, 0, self.r), color=(225, 170, 140), parent=self)
        self.ttlab.setGeometry(self.s, self.s, width, tt_height)
        self.ttlab.setText(title)
        # 设置圆角背景
        self.bglab = TLabel(round=(0, self.r, self.r, 0), color=(250, 250, 250), parent=self)
        self.bglab.setGeometry(self.s, self.s+tt_height, width, height-tt_height)
        # 设置最小化按钮位置和大小 绑定事件
        btn_size = int(0.75 * tt_height)
        self.minButton = MyButton(MyButton.MINI, self.ttlab)
        self.minButton.setGeometry(self.ttlab.width()-btn_size*2-10, (self.ttlab.height()-btn_size)/2, btn_size, btn_size)
        self.minButton.clicked.connect(self.showMinimized)
        # 设置关闭按钮位置和大小 绑定事件
        self.closeButton = MyButton(MyButton.CLOSE, self.ttlab)
        self.closeButton.setGeometry(self.ttlab.width()-btn_size-5, (self.ttlab.height()-btn_size)/2, btn_size, btn_size)
        self.closeButton.clicked.connect(self.close)

    def setShadow(self, alpha=lambda i: 20*(1-i**0.5*0.3535), color=QColor(0, 0, 0, 255), space=0.2):
        '''
        alpha 阴影可见度变化函数
        color 颜色
        space 自变量(距离界面距离，取值[0-s])每次增加距离
        '''
        self.alpha = alpha
        self.color = color
        self.space = space

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def setTitle(self, title: str, color=Qt.white, font=QFont('微软雅黑', 13, QFont.Normal), location=Qt.AlignCenter):
        self.ttlab.setText(title, color, font, location)

    def paintEvent(self, event):
        # 画阴影
        shadow_pat = QPainter(self)
        shadow_pat.setRenderHint(shadow_pat.Antialiasing)
        i = 0
        while i <= self.s:
            '''
            i 表示距离界面的距离\n
            扩散距离为 s 因此 i 的取值从[0-s]\n
            每次生成一个可见度不同的圆角矩形\n
            随着 i 的增大 alpha 函数值下降可使阴影渐变
            '''
            shadow_path = QPainterPath()
            shadow_path.setFillRule(Qt.WindingFill)
            ref = QRectF(self.s-i, self.s-i, self.width()-(self.s-i)*2, self.height()-(self.s-i)*2)
            shadow_path.addRoundedRect(ref, self.r, self.r)
            self.color.setAlpha(self.alpha(i))
            shadow_pat.setPen(self.color)
            shadow_pat.drawPath(shadow_path)
            i += self.space

    def mousePressEvent(self, QMouseEvent):
        '''
        鼠标点击 检测点击位置判断是否可移动
        清除所有文本框的选中状态
        '''
        if QMouseEvent.button() == Qt.LeftButton:
            # 鼠标点击点的相对位置
            self.m_DragPosition = QMouseEvent.globalPos()-self.pos()
            # print((self.m_DragPosition.x(), self.m_DragPosition.y()))
            if self.m_DragPosition.y() <= 39 + self.s:
                self.m_drag = True

    def mouseMoveEvent(self, QMouseEvent):
        '按住标题栏可移动窗口'
        if self.m_drag:
            self.move(QMouseEvent.globalPos()-self.m_DragPosition)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_drag = False
        QMouseEvent.accept()
