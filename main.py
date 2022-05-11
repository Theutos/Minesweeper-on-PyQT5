import sys
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import Qt
from PyQt5.QtGui import *
from PyQt5 import QtWidgets, QtCore

from random import randint

all_difficulties = {'easy': {'size_x': 9, 'size_y': 9, 'bombs': 10, 'btn_size': 40, 'x_move': 10},
                    'normal': {'size_x': 16, 'size_y': 16, 'bombs': 40, 'btn_size': 23, 'x_move': 7},
                    'hard': {'size_x': 30, 'size_y': 16, 'bombs': 99, 'btn_size': 23, 'x_move': 7}}
difficulty = 'easy'
bombs_count = 10
flags_pos = []
bomb_pos = []
closed_remain = 0


class Board:
    def __init__(self):
        global board, bombs_count, bomb_pos, flags_pos, closed_remain
        self.size_x = all_difficulties[difficulty]['size_x']
        self.size_y = all_difficulties[difficulty]['size_y']
        self.bombs = all_difficulties[difficulty]['bombs']
        board = [['0'] * self.size_x for _ in range(self.size_y)]
        self.empty = True
        bombs_count = all_difficulties[difficulty]['bombs']
        bomb_pos = []
        flags_pos = []
        closed_remain = self.size_x * self.size_y

    def create_board(self, x_pressed, y_pressed):
        for _ in range(self.bombs):
            y = randint(0, self.size_y - 1)
            x = randint(0, self.size_x - 1)
            while (board[y][x] == '*' or (x == y_pressed and y == x_pressed)):
                y = randint(0, self.size_y - 1)
                x = randint(0, self.size_x - 1)
            board[y][x] = '*'
            bomb_pos.append((y, x))

        for y in range(len(board)):
            for x in range(len(board[y])):
                if board[y][x] == '*':
                    continue
                bomb_count = 0
                for y_plus in range(-1, 2):
                    for x_plus in range(-1, 2):
                        y_check = y + y_plus
                        x_check = x + x_plus
                        if y_check < 0 or x_check < 0 or y_check >= len(board) or x_check >= len(board[y]):
                            continue
                        if board[y_check][x_check] == '*':
                            bomb_count += 1
                board[y][x] = str(bomb_count)
        self.empty = False


class Settings(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('settings.ui', self)

        self.setWindowTitle("Minesweeper")
        self.radioButton.toggle()

        self.pushButton.clicked.connect(self.start_game)

        con = sqlite3.connect("records_db")
        cur = con.cursor()
        result = cur.execute("""SElECT DISTINCT difficulty, seconds FROM records ORDER BY seconds""")
        for res in result:
            if res[0] == 1:
                dif = 'Easy'
            elif res[0] == 2:
                dif = 'Normal'
            elif res[0] == 3:
                dif = 'Hard'
            self.listWidget.addItem("{} - {} секунд".format(dif, res[1]))

    def start_game(self):
        global difficulty
        if self.radioButton.isChecked():
            difficulty = self.radioButton.text().lower()
        elif self.radioButton_2.isChecked():
            difficulty = self.radioButton_2.text().lower()
        elif self.radioButton_3.isChecked():
            difficulty = self.radioButton_3.text().lower()

        self.dialog = Minesweeper(difficulty)
        self.dialog.show()
        self.close()


class Minesweeper(QWidget):
    def __init__(self, dif):
        super().__init__()
        self.difficulty = dif
        self.zero = []
        self.zero_opened = []
        self.restarting = False
        self.end = False

        self.initUI()

    def initUI(self):
        if self.difficulty == 'easy' or self.difficulty == 'normal':
            self.setGeometry(200, 200, 380, 460)
        else:
            self.setGeometry(200, 200, 710, 460)
        self.setWindowTitle("Minesweeper")

        self.board = Board()
        self.btns = [[0] * self.board.size_x for _ in range(self.board.size_y)]

        btn_size = all_difficulties[difficulty]['btn_size']
        x_move = all_difficulties[difficulty]['x_move']
        _x_move = x_move
        y_move = 90

        for y in range(len(board)):
            for x in range(len(board[y])):
                self.btn = PushButtonRight(self)
                self.btn.move(x_move, y_move)
                self.btn.setFixedSize(btn_size, btn_size)
                self.btn.clicked.connect(self.btn_pressed)
                self.btn.setStyleSheet("background-color: #949494")
                self.btn.setObjectName(f"{y};{x}")
                self.btns[y][x] = self.btn
                x_move += btn_size
            y_move += btn_size
            x_move = _x_move

        self.bombLCD = QLCDNumber(self)
        self.bombLCD.resize(100, 50)
        self.bombLCD.move(18, 18)
        self.bombLCD.display(bombs_count)

        self.timeLCD = QLCDNumber(self)
        self.timeLCD.resize(120, 50)
        self.restartButton = QPushButton(self)
        self.restartButton.resize(50, 50)

        if difficulty == 'hard':
            self.timeLCD.move(550, 18)
            self.restartButton.move(330, 18)
        else:
            self.timeLCD.move(230, 18)
            self.restartButton.move(165, 18)
        self.restartButton.setText('⭯')
        self.restartButton.setFont(QFont("Arial", 15))
        self.restartButton.clicked.connect(self.restart)
        self.timeLCD.display(0)

    def restart(self):
        self.restarting = True
        self.new = Minesweeper(difficulty)
        self.new.show()
        self.close()

    def time(self):
        self.timeLCD.display(self.timeLCD.value() + 1)

    def board_creation(self):
        self.board.create_board(*list(map(int, self.sender().objectName().split(';'))))
        for i in board:
            print(*i)

    def btn_pressed(self):
        global closed_remain
        if self.board.empty:
            self.board_creation()
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.time)
            self.timer.start(1000)
        if not self.end:
            if self.sender().text() == '':
                y, x = list(map(int, self.sender().objectName().split(';')))
                self.sender().setText(board[y][x])
                self.sender().setStyleSheet("background-color: #c7c7c7")
                if board[y][x] == '0':
                    self.zero.append((y, x))
                while len(self.zero) != 0:
                    self.zero_open()
                if board[y][x] == '*':
                    self.end = True
                    self.lose()
                closed_remain -= 1
                if closed_remain == self.board.bombs:
                    self.win()
                print(closed_remain)

    def win(self):
        for y, x in bomb_pos:
            if self.btns[y][x].text() == '':
                self.btns[y][x].setText('🚩')
        self.timer.stop()
        self.end = True
        self.bombLCD.display(0)
        text1 = """INSERT INTO records(seconds, difficulty) VALUES(?, ?);"""
        if difficulty == 'easy':
            d = 1
        elif difficulty == 'normal':
            d = 2
        elif difficulty == 'hard':
            d = 3
        con = sqlite3.connect("records_db")
        cur = con.cursor()
        cur.execute(text1, (self.timeLCD.value(), d))
        con.commit()
        cur.close()

    def lose(self):
        for y, x in bomb_pos:
            if self.btns[y][x].text() == '' or self.btns[y][x].text() == '*':
                self.btns[y][x].setText('*')
                self.btns[y][x].setStyleSheet("background-color: #cfabab")
        for flag in flags_pos:
            if flag not in bomb_pos:
                self.btns[flag[0]][flag[1]].setStyleSheet("background-color: #ff5b5b")
        self.timer.stop()

    def zero_open(self):
        global closed_remain
        if len(self.zero) != 0:
            y, x = self.zero[0]
            self.zero_opened.append((y, x))
            for y_plus in range(-1, 2):
                for x_plus in range(-1, 2):
                    y_check = y + y_plus
                    x_check = x + x_plus
                    if y_check < 0 or x_check < 0 or y_check >= len(board) or x_check >= len(board[y]):
                        continue
                    if self.btns[y_check][x_check].text() == '' or self.btns[y_check][x_check].text() == '🚩':
                        self.btns[y_check][x_check].setText(board[y_check][x_check])
                        self.btns[y_check][x_check].setStyleSheet("background-color: #c7c7c7")
                        closed_remain -= 1
                    if (y_check, x_check) in flags_pos:
                        flags_pos.remove((y_check, x_check))
                    if board[y_check][x_check] == '0' and (y_check, x_check) not in self.zero_opened:
                        self.zero.append((y_check, x_check))

            self.zero.remove((y, x))

    def closeEvent(self, event):
        if not self.restarting:
            self.dialog = Settings()
            self.dialog.show()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.Qt.RightButton:
            self.bombLCD.display(bombs_count)


class PushButtonRight(QtWidgets.QPushButton):
    left_click = QtCore.pyqtSignal()
    right_click = QtCore.pyqtSignal()

    def __init__(self, string):
        super().__init__(string)

    def mousePressEvent(self, event):
        global bombs_count, flags_pos
        if event.button() == Qt.Qt.RightButton:
            self.right_click.emit()
            if self.text() == '':
                self.setText('🚩')
                bombs_count -= 1
                flags_pos.append(tuple(map(int, self.objectName().split(';'))))
            elif self.text() == '🚩':
                self.setText('')
                bombs_count += 1
                flags_pos.remove(tuple(map(int, self.objectName().split(';'))))

        QtWidgets.QPushButton.mousePressEvent(self, event)


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


# Back up the reference to the exceptionhook
sys._excepthook = sys.excepthook

# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook

if __name__ == "__main__":
    app = QApplication(sys.argv)

    ex = Settings()
    ex.show()

    sys.exit(app.exec())
