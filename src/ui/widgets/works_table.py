from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt

class WorksTable(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_row)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(self.remove_selected)
        buttons_layout.addWidget(remove_btn)
        
        layout.addLayout(buttons_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Наименование", "Ед.изм.", "Кол-во", "Цена", "Сумма"
        ])
        
        # Растягиваем столбцы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, header.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Создаем пустые ячейки
        for col in range(5):
            item = QTableWidgetItem("")
            if col in [2, 3, 4]:  # Числовые колонки
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)
    
    def remove_selected(self):
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)
    
    def update_totals(self):
        """Пересчитать суммы"""
        for row in range(self.table.rowCount()):
            try:
                quantity = float(self.table.item(row, 2).text() or 0)
                price = float(self.table.item(row, 3).text() or 0)
                total = quantity * price
                self.table.item(row, 4).setText(f"{total:.2f}")
            except ValueError:
                self.table.item(row, 4).setText("0.00")
    
    def get_works(self):
        """Получить список всех работ"""
        works = []
        for row in range(self.table.rowCount()):
            works.append({
                'name': self.table.item(row, 0).text(),
                'unit': self.table.item(row, 1).text(),
                'quantity': float(self.table.item(row, 2).text() or 0),
                'price': float(self.table.item(row, 3).text() or 0),
                'total': float(self.table.item(row, 4).text() or 0)
            })
        return works
    
    def set_works(self, works):
        """Установить список работ"""
        self.table.setRowCount(0)
        for work in works:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(work['name']))
            self.table.setItem(row, 1, QTableWidgetItem(work['unit']))
            self.table.setItem(row, 2, QTableWidgetItem(str(work['quantity'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(work['price'])))
            total = work['quantity'] * work['price']
            self.table.setItem(row, 4, QTableWidgetItem(str(total)))

    def clear(self):
        """Очистить таблицу"""
        self.table.setRowCount(0)
