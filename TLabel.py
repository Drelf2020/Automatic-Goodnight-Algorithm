from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QBrush, QPainter, QColor, QFont
from TPath import RoundPath


class TLabel(QLabel):
    '''
    /*带圆角的展示框*/
    mode: 圆角半径类型
        'relative': 取值[0,1] 相对组件长宽
        'absolute': 取值正整数 绝对像素值
    round: 圆角半径
        tuple: 从左上开始逆时针顺序四个数字
    color: 仅展示纯色，若与图片同时存在，优先选择图片
        str: 纯色html代码
        tuple: RGB代码
        QColor: QColor对象
    parent: 父对象
    '''
    def __init__(self, mode='absolute', round=(0, 0, 0, 0), color=Qt.white, parent=None):
        super(TLabel, self).__init__(parent)
        self.text = None
        self.mode = 'relative' if mode == 'relative' else 'absolute'

        if self.mode == 'relative':
            for r in round:
                if r > 1 or r < 0:
                    raise Exception('TLabel Round Error')
        else:
            temp_round = []
            for r in round:
                if r < 0:
                    raise Exception('TLabel Round Error')
                temp_round.append(int(r))
            round = tuple(temp_round)
        self.round = round

        if isinstance(color, tuple):
            self.color = QColor(*color)
        elif isinstance(color, str):
            self.color = QColor(0, 0, 0)
            self.color.setNamedColor(color)
        elif isinstance(color, (QColor, Qt.GlobalColor)):
            self.color = color
        else:
            print(type(color))
            raise Exception('TLabel Color Error')

    def setText(self, msg: str, color=Qt.white, font=QFont('微软雅黑', 13, QFont.Normal), location=Qt.AlignCenter):
        if isinstance(color, tuple):
            color = QColor(*color)
        elif isinstance(color, str):
            color = QColor().setNamedColor(color)
        if not isinstance(color, (QColor, Qt.GlobalColor)):
            raise Exception('TLabel Text Color Error')
        if not isinstance(font, QFont):
            raise Exception('TLabel Text Font Error')
        self.text = (msg, color, font, location)

    def paintEvent(self, event):
        # 画笔设置不描边
        pat = QPainter(self)
        pat.setPen(Qt.NoPen)
        brush = QBrush(self.color)  # 画刷为纯色
        pat.setRenderHint(pat.Antialiasing)  # 抗锯齿

        pat.setBrush(brush)
        path = RoundPath(self.rect(), self.round)
        pat.drawPath(path)
        # 文字
        if self.text:
            msg, color, font, location = self.text
            pat.setPen(Qt.black)
            pat.setFont(font)
            pat.setPen(color)
            pat.drawText(5, 5, self.width()-10, self.height()-10, location, msg)
