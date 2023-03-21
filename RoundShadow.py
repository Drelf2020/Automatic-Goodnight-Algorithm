from fileinput import close
import os
import sys

from PyQt5.QtCore import QRect, QRectF, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QPainter, QPainterPath
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QMainWindow, QPushButton)
from TLabel import TLabel


class MyButton(QPushButton):
    choice: int = 0  # 不同的选中状态
    COLOR = list()  # 不用状态下的颜色

    def enterEvent(self, QMouseEvent):
        self.choice = 1
        super().enterEvent(QMouseEvent)

    def mousePressEvent(self, QMouseEvent):
        self.choice = 2
        super().mousePressEvent(QMouseEvent)

    def mouseReleaseEvent(self, QMouseEvent):
        self.choice = 1
        super().mouseReleaseEvent(QMouseEvent)

    def leaveEvent(self, QMouseEvent):
        self.choice = 0
        super().leaveEvent(QMouseEvent)

    def paintEvent(self, event):
        self.pat = QPainter(self)
        self.pat.setRenderHint(self.pat.Antialiasing)  # 抗锯齿
        self.pat.setPen(Qt.NoPen)
        self.pat.setBrush(self.COLOR[self.choice])
        self.pat.drawRoundedRect(QRect(0, 0, self.width(), self.height()), self.width()//2, self.height()//2)

class miniButton(MyButton):
    COLOR = [QColor(0, 0, 0, 0), QColor(255, 255, 255, 100), QColor(255, 255, 255, 125)]

    def paintEvent(self, event):
        super().paintEvent(event)
        self.pat.setPen(Qt.white)
        self.pat.setBrush(Qt.white)
        self.pat.drawRoundedRect(QRect(self.width()//5, self.height()//2, self.width()*3//5, self.height()//12), self.height()//24, self.height()//24)
        self.pat.end()

class closeButton(MyButton):
    COLOR = [QColor(0, 0, 0, 0), QColor(255, 84, 57), QColor(224, 74, 50)]

    def paintEvent(self, event):
        super().paintEvent(event)
        x, y, r = self.width()/2-4, self.height()/2-4, self.width()/12
        self.pat.translate(x+4, y+4)
        self.pat.rotate(-45)
        self.pat.setPen(Qt.white)
        self.pat.setBrush(Qt.white)
        self.pat.drawRoundedRect(QRectF(-x, -r//2, 2*x, r), r//2, r//2)
        self.pat.drawRoundedRect(QRectF(-r//2, -y, r, 2*y), r//2, r//2)
        self.pat.end()

class RoundShadow(QMainWindow):
    '''
    圆角窗口\n
    width, height: 去掉边框后界面的长宽\n
    radius: 界面圆角半径\n
    spread: 阴影扩散范围\n
    title:  界面标题
    '''
    close_signal = pyqtSignal()

    m_drag: bool = False  # 窗口是否可移动
    m_DragPosition: QPoint = None  # 移动位置

    alpha = lambda _, i: 20*(1-i**0.5*0.3535)  # 阴影函数
    color = QColor(0, 0, 0, 255)  # 阴影初始颜色
    space = 0.2  # 自变量

    def __init__(self, width: int, height: int, radius: int=8, spread: int=8, title: str='', parent=None):
        super().__init__(parent)
        self.r = radius
        self.s = spread
        
        self.close_signal.connect(lambda: self.close())
        # 导入字体
        QFontDatabase.addApplicationFont(os.path.dirname(__file__)+'\\*.ttf')
        # 初始化窗口
        self.initUI(width, height, title)
        # 窗口居中
        self.center()

    def initUI(self, width: int, height: int, title: str):
        # 设置窗口大小为界面大小加上两倍阴影扩散距离(因为是左右两边)
        self.resize(width+2*self.s, height+2*self.s)
        # 设置窗口无边框和背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # 设置标题栏
        tt_height = 50  # 标题栏高度
        self.ttlab = TLabel(radius=(self.r, 0, 0, self.r), color=(225, 170, 140), parent=self)
        self.ttlab.setGeometry(self.s, self.s, width, tt_height)
        # 设置标题
        self.setTitle(title)
        # 设置圆角背景
        self.bglab = TLabel(radius=(0, self.r, self.r, 0), color=(250, 250, 250), parent=self)
        self.bglab.setGeometry(self.s, self.s+tt_height, width, height-tt_height)
        # 按钮大小
        btn_size = int(0.75 * tt_height)
        # 设置最小化按钮位置和大小 绑定事件
        self.minButton = miniButton(self.ttlab)
        self.minButton.setGeometry(self.ttlab.width()-btn_size*2-10, (self.ttlab.height()-btn_size)//2, btn_size, btn_size)
        self.minButton.clicked.connect(self.showMinimized)
        # 设置关闭按钮位置和大小 绑定事件
        self.closeButton = closeButton(self.ttlab)
        self.closeButton.setGeometry(self.ttlab.width()-btn_size-5, (self.ttlab.height()-btn_size)//2, btn_size, btn_size)
        self.closeButton.clicked.connect(self.close)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def setTitle(self, title: str, color=Qt.white, font=QFont('HarmonyOS Sans SC', 16), location=Qt.AlignVCenter | Qt.AlignLeft):
        self.ttlab.setText(title, color, font, location)

    def paintEvent(self, event):
        '''
        i 表示距离界面的距离\n
        扩散距离为 s 因此 i 的取值从[0-s]\n
        每次生成一个可见度不同的圆角矩形\n
        随着 i 的增大 alpha 函数值下降可使阴影渐变
        '''
        shadow_pat = QPainter(self)
        shadow_pat.setRenderHint(shadow_pat.Antialiasing)
        i = 0
        while i <= self.s:
            shadow_path = QPainterPath()
            shadow_path.setFillRule(Qt.WindingFill)
            ref = QRectF(self.s-i, self.s-i, self.width()-(self.s-i)*2, self.height()-(self.s-i)*2)
            shadow_path.addRoundedRect(ref, self.r, self.r)
            self.color.setAlpha(int(self.alpha(i)))
            shadow_pat.setPen(self.color)
            shadow_pat.drawPath(shadow_path)
            i += self.space
        shadow_pat.end()

    def mousePressEvent(self, QMouseEvent):
        '''
        鼠标点击 检测点击位置判断是否可移动
        清除所有文本框的选中状态
        '''
        if QMouseEvent.button() == Qt.LeftButton:
            # 鼠标点击点的相对位置
            self.m_DragPosition = QMouseEvent.globalPos()-self.pos()
            # print((self.m_DragPosition.x(), self.m_DragPosition.y()))
            if self.m_DragPosition.y() <= 49 + self.s:
                self.m_drag = True

    def mouseMoveEvent(self, QMouseEvent):
        '按住标题栏可移动窗口'
        if self.m_drag:
            self.move(QMouseEvent.globalPos()-self.m_DragPosition)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_drag = False
        QMouseEvent.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)  # 新建窗口前必运行app
    win = RoundShadow(600, 400, title='中国智造')
    win.show()  # 显示主窗口
    app.exec_()  # 等待直到登录窗口关闭
    