from PyQt5 import QtWidgets, QtCore
import sys
import sqlite3
from main_ui import Ui_MainWindow
from addEditCoffeeForm import Ui_Form


# Так как Я должен сделать сам файл sql, то я не буду проверять есть файл sql или нет
class AddWord(QtWidgets.QDialog):
    """Класс-диалог. Открывается модальное диалоговое окно с двумя виджета lineedit"""

    def __init__(self, main_wnd):
        super(AddWord, self).__init__(main_wnd)
        self.setWindowTitle('Введите слово или фразу, затем его перевод')
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.flag = False  # флажок показывает где нужно выводить, а где нет
        self.lineedits = list()  # список lineedit виджетов

        self.main_layout.addLayout(self.__create_layout('название сорта:'))
        self.main_layout.addLayout(self.__create_layout('степень обжарки:'))
        self.main_layout.addLayout(self.__create_layout('молотый/в зернах:'))
        self.main_layout.addLayout(self.__create_layout('описание вкуса:'))
        self.main_layout.addLayout(self.__create_layout('цена:'))
        self.main_layout.addLayout(self.__create_layout('объем упаковки:'))

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.__accepted)
        self.buttonBox.rejected.connect(self.__rejected)

        self.main_layout.addWidget(self.buttonBox)
        self.setModal(True)  # Чтобы мы не могли использовать словарь

    def __create_layout(self, text):
        """Возвращает layout с label и lineedit(именно таким порядком)"""
        # Данный метод нужно использовать ровно 2 раза, так как колонки примерно одинаковы,
        # но я не придумал как избавиться от списка lineedits, так как данные этих виджетов нужно добавить в словарь
        other_layout = QtWidgets.QHBoxLayout(self)
        word_lineedit = QtWidgets.QLineEdit(self)

        self.lineedits.append(word_lineedit)  # Добавляет в список

        other_layout.addWidget(QtWidgets.QLabel(text, self), alignment=QtCore.Qt.AlignLeft)
        other_layout.addWidget(word_lineedit)

        return other_layout

    def __accepted(self):
        """Метод для кнопки \'Ок\'"""
        self.flag = True
        self.close()

    def __rejected(self):
        """Метод для кнопки \'Cancel\'"""
        self.close()

    def __getTexts(self):
        """Возвращает данные, где были введены в виджеты lineedit"""
        listok = []
        for i in self.lineedits:
            listok.append(i.text() if i.text() else 'None')
        return listok

    @staticmethod
    def getWords(main_wnd):
        """Создаёт модальное диалоговое окно и возвращает список слов или None"""
        # Заметьте, что это статический метод
        window = AddWord(main_wnd)
        window.show()
        window.exec()
        if window.flag:  # если была нажата кнопка 'Ok'
            return window.__getTexts()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.main_wind = Ui_MainWindow()
        self.main_wind.setupUi(self)
        self.add_del = Ui_Form()
        self.add_del.setupUi(self)
        self.con = sqlite3.connect('../coffee.db')
        self.cur = self.con.cursor()

        self.list_items = self.cur.execute("""SELECT * FROM coffee""").fetchall()

        self.title = self.cur.execute("""PRAGMA table_info(coffee)""").fetchall()
        self.title = list(i[1] for i in self.title)

        self.add_del.DelBtn.setEnabled(False)

        self.main_wind.tableWidget.itemSelectionChanged.connect(self.selected_item_in_table)
        self.add_del.AddBtn.clicked.connect(self.add_word)
        self.add_del.DelBtn.clicked.connect(self.del_button)
        self.main_wind.tableWidget.cellChanged.connect(self.change_item_in_table)

        self.loadsql()

    def loadsql(self):
        self.list_items = self.cur.execute("""SELECT * FROM coffee""").fetchall()
        self.main_wind.tableWidget.setColumnCount(len(self.title))
        self.main_wind.tableWidget.setHorizontalHeaderLabels(self.title)
        self.main_wind.tableWidget.setRowCount(0)
        for i, row in enumerate(self.list_items):
            self.main_wind.tableWidget.setRowCount(
                self.main_wind.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.main_wind.tableWidget.setItem(
                    i, j, QtWidgets.QTableWidgetItem(str(elem)))

        self.main_wind.tableWidget.resizeColumnsToContents()
        for i in range(self.main_wind.tableWidget.columnCount()):
            self.main_wind.tableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

    def selected_item_in_table(self):
        """Метод для del_pushbutton"""
        # Если не выбрано слово, то незачем много раз тыкать на кнопку 'Удалить'
        if self.main_wind.tableWidget.selectedItems():
            self.add_del.DelBtn.setEnabled(True)
        else:
            self.add_del.DelBtn.setEnabled(False)

    def add_word(self):
        """Метод добавления слова"""
        words = AddWord.getWords(self)  # Создаёт Dialog через staticmethod (эксперимент)

        if words:
            words = [self.list_items[-1][0] + 1] + words
            sqlite_insert_query = f"""INSERT INTO coffee
            (ID, 'название сорта', 'степень обжарки', 'молотый/в зернах', 'описание вкуса', цена, 'объем упаковки')
            VALUES
            (?, ?, ?, ?, ?, ?, ?);"""
            count = self.cur.execute(sqlite_insert_query, tuple(words))
            self.con.commit()

            self.loadsql()

    def del_button(self):
        rows = list(set([i.row() for i in self.main_wind.tableWidget.selectedItems()]))
        ids = [self.main_wind.tableWidget.item(i, 0).text() for i in rows]
        valid = QtWidgets.QMessageBox.question(
            self, '', "Действительно удалить элементы с id " + ",".join(ids),
            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if valid == QtWidgets.QMessageBox.Yes:
            cur = self.con.cursor()
            cur.execute("DELETE FROM coffee WHERE ID IN (" + ", ".join(
                '?' * len(ids)) + ")", ids)
            self.con.commit()
        self.loadsql()

    def change_item_in_table(self):
        """Метод изменения слова внутри tablewidget"""
        if self.main_wind.tableWidget.currentColumn() != 0:
            for i in self.main_wind.tableWidget.selectedItems():
                row = self.main_wind.tableWidget.currentRow() + 1
                col = self.main_wind.tableWidget.currentColumn()
                title = self.title[col]
                sqlite_insert_query = \
                    f"""UPDATE coffee
                        set '{title}' = ?
                        where id = {row}
                        """
                data = (self.main_wind.tableWidget.item(row - 1, col).text(),)
                count = self.cur.execute(sqlite_insert_query, data)
                self.con.commit()

        if self.main_wind.tableWidget.selectedItems():  # Если не выбрано, то ничего не делаем
            self.list_items = self.cur.execute("""SELECT * FROM coffee""").fetchall()
            self.loadsql()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QtWidgets.QApplication(sys.argv)
    wnd = MainWindow()
    wnd.show()
    sys.exit(app.exec())
