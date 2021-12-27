from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontMetricsF
from PyQt5.QtWidgets import QLineEdit, QWidget


class EXEdit(QLineEdit):
    def __init__(self, parent=None):
        super(EXEdit, self).__init__(parent)

    def enterEvent(self, QMouseEvent):
        QMouseEvent.ignore()

    def mousePressEvent(self, QMouseEvent):
        QMouseEvent.ignore()

    def leaveEvent(self, QMouseEvent):
        QMouseEvent.ignore()

    def focusInEvent(self, focusEvent):
        '获得焦点事件'
        super(EXEdit, self).focusInEvent(focusEvent)
        self.parent().pen = self.parent().pen_style['press']
        self.parent().update()
        focusEvent.accept()

    def focusOutEvent(self, focusEvent):
        '失去焦点事件'
        super(EXEdit, self).focusOutEvent(focusEvent)
        self.parent().pen = self.parent().pen_style['leave']
        self.parent().update()
        focusEvent.accept()


class TLineEdit(QWidget):
    '自定义的只含底线的文本框'

    def __init__(self, title=None, parent=None):
        super(TLineEdit, self).__init__(parent)
        self.title = title
        self.Edit = EXEdit(self)  # 编辑框
        self.Edit.setAlignment(Qt.AlignCenter)
        self.Edit.setContextMenuPolicy(Qt.NoContextMenu)  # 禁用右键菜单 https://bbs.csdn.net/topics/391545518
        # 利用css代码取消边框和背景
        self.Edit.setStyleSheet(("border:0px;background:rgba(0,0,0,0);"))
        # 三种不同颜色的底画线
        self.pen_style = {
            'leave': QPen(QColor(75, 75, 75), 3),
            'enter': QPen(QColor(25, 25, 25), 3),
            'press': QPen(QColor(0, 0, 0), 3)
        }
        self.pen = self.pen_style['leave']  # 初始画笔

    def paintEvent(self, event):
        '绘制文本框'
        pat = QPainter(self)
        pat.setRenderHint(pat.Antialiasing)
        pat.setPen(self.pen)
        font = QFont('微软雅黑', 13, QFont.Normal)
        font.setPixelSize(0.45*self.height())
        fm = QFontMetricsF(font)  # 测字符长度
        w = fm.width(self.title)
        pat.setFont(font)
        pat.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignLeft, self.title)
        pat.drawLine(QPointF(w, self.height()), QPointF(self.width(), self.height()))
        self.Edit.setFont(font)
        self.Edit.setGeometry(w, 0.05*self.height(), self.width()-w-5, 0.9*self.height())

    def enterEvent(self, QMouseEvent):
        '检测鼠标是否移动至文本框并变色'
        self.pen = self.pen_style['enter']
        self.update()
        QMouseEvent.accept()

    def mousePressEvent(self, QMouseEvent):
        '按下文本框 变色'
        self.pen = self.pen_style['press']
        self.Edit.setFocus()
        self.update()
        QMouseEvent.accept()

    def leaveEvent(self, QMouseEvent):
        '未按下时移开鼠标变色'
        if self.pen == self.pen_style['enter']:
            self.pen = self.pen_style['leave']
        self.update()
        QMouseEvent.accept()

    def focusInEvent(self, focusEvent):
        '获得焦点事件'
        self.pen = self.pen_style['press']
        self.update()
        focusEvent.accept()

    def focusOutEvent(self, focusEvent):
        '失去焦点事件'
        self.pen = self.pen_style['leave']
        self.update()
        focusEvent.accept()
