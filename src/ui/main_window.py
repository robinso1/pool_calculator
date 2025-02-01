from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QLabel, QSpinBox,
                             QDoubleSpinBox, QComboBox, QTableWidget,
                             QTableWidgetItem, QMessageBox, QFileDialog,
                             QInputDialog)
from PyQt6.QtCore import Qt
from ui.widgets.pool_designer import PoolDesigner
from ui.widgets.materials_table import MaterialsTable
from ui.widgets.works_table import WorksTable
from ui.widgets.preview import PoolPreview
from utils.project import Project
from utils.calculator import PoolCalculator
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор Бассейнов")
        self.setMinimumSize(1200, 800)
        
        # Текущий проект
        self.current_project = Project()
        
        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QHBoxLayout(central_widget)
        
        # Левая панель с параметрами
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Дизайнер бассейна
        self.pool_designer = PoolDesigner()
        left_layout.addWidget(self.pool_designer)
        
        # Кнопка пересчета
        recalc_btn = QPushButton("Пересчитать количество")
        recalc_btn.clicked.connect(self.recalculate_quantities)
        left_layout.addWidget(recalc_btn)
        
        # Предпросмотр
        self.preview = PoolPreview()
        left_layout.addWidget(self.preview)
        
        layout.addWidget(left_panel)
        
        # Правая панель с таблицами
        right_panel = QTabWidget()
        
        # Таблица материалов
        self.materials_table = MaterialsTable()
        right_panel.addTab(self.materials_table, "Материалы")
        
        # Таблица работ
        self.works_table = WorksTable()
        right_panel.addTab(self.works_table, "Работы")
        
        layout.addWidget(right_panel)
        
        # Добавляем меню
        self._create_menu()
        
        # Связываем сигналы
        self.pool_designer.parameters_changed.connect(self.update_calculations)
        
        # Загружаем начальные данные
        self._load_initial_data()
    
    def _load_initial_data(self):
        """Загрузка начальных данных в таблицы"""
        # Материалы
        materials = [
            {"name": "Песок по факту", "unit": "м3", "quantity": 1, "price": 850},
            {"name": "Доставка песка", "unit": "услуга", "quantity": 1, "price": 3500},
            {"name": "Щебень по факту", "unit": "м3", "quantity": 1, "price": 1150},
            {"name": "Доставка щебня", "unit": "услуга", "quantity": 1, "price": 3500},
            {"name": "Стеклопакет СП1.5-10-м2", "unit": "грамм", "quantity": 42, "price": 2225},
            {"name": "Праймер битумный AquaMast", "unit": "шт", "quantity": 3, "price": 3800},
            {"name": "Рубероид", "unit": "шт", "quantity": 7, "price": 1700},
            {"name": "Арматура д-12", "unit": "шт", "quantity": 2, "price": 6000},
            {"name": "Проволока вязальная", "unit": "кг", "quantity": 1, "price": 95},
            {"name": "Бетонировка бассейна", "unit": "м3", "quantity": 17, "price": 6500}
        ]
        self.materials_table.set_materials(materials)
        
        # Работы
        works = [
            {"name": "Разметка бассейна", "unit": "м2", "quantity": 47, "price": 300},
            {"name": "Выемка грунта", "unit": "м3", "quantity": 71, "price": 550},
            {"name": "Вывоз грунта", "unit": "КамАЗ", "quantity": 10, "price": 6500},
            {"name": "Работа с трактором", "unit": "услуга", "quantity": 1, "price": 15000},
            {"name": "Доработка грунта вручную", "unit": "м2", "quantity": 47, "price": 350},
            {"name": "Отсыпка щебенки", "unit": "м2", "quantity": 47, "price": 350},
            {"name": "Устройство контур заземления", "unit": "шт", "quantity": 1, "price": 7500},
            {"name": "Бетонирование подготовки", "unit": "м2", "quantity": 47, "price": 800},
            {"name": "Гидроизоляция бассейна", "unit": "м2", "quantity": 79, "price": 700},
            {"name": "Монтаж опалубки", "unit": "м3", "quantity": 14.5, "price": 1500}
        ]
        self.works_table.set_works(works)
    
    def _create_menu(self):
        menubar = self.menuBar()
        
        # Меню файл
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Новый проект", self.new_project)
        file_menu.addAction("Открыть", self.open_project)
        file_menu.addAction("Сохранить", self.save_project)
        file_menu.addSeparator()
        file_menu.addAction("Экспорт в Excel", self.export_excel)
        file_menu.addAction("Экспорт в PDF", self.export_pdf)
        
        # Меню редактирование
        edit_menu = menubar.addMenu("Редактирование")
        edit_menu.addAction("Обновить цены", self.update_prices)
        
        # Меню справка
        help_menu = menubar.addMenu("Справка")
        help_menu.addAction("О программе", self.about)
    
    def new_project(self):
        """Создать новый проект"""
        reply = QMessageBox.question(
            self, 'Новый проект',
            'Создать новый проект? Несохраненные изменения будут потеряны.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_project = Project()
            self.pool_designer.reset_to_defaults()
            self.materials_table.clear()
            self.works_table.clear()
    
    def open_project(self):
        """Открыть проект"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть проект",
            "",
            "Проекты бассейнов (*.pool);;Все файлы (*.*)"
        )
        
        if filename:
            try:
                self.current_project = Project.load(filename)
                
                # Обновляем интерфейс
                self.pool_designer.set_parameters(self.current_project.pool_params)
                self.materials_table.set_materials(self.current_project.materials)
                self.works_table.set_works(self.current_project.works)
                self.preview.set_parameters(self.current_project.pool_params)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Проект успешно загружен из {filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось загрузить проект: {str(e)}"
                )
    
    def save_project(self):
        """Сохранить проект"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить проект",
            "",
            "Проекты бассейнов (*.pool);;Все файлы (*.*)"
        )
        
        if filename:
            try:
                # Обновляем данные проекта
                self.current_project.pool_params = self.pool_designer.get_parameters()
                self.current_project.materials = self.materials_table.get_materials()
                self.current_project.works = self.works_table.get_works()
                
                # Сохраняем
                self.current_project.save(filename)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Проект успешно сохранен в {filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось сохранить проект: {str(e)}"
                )
    
    def export_excel(self):
        """Экспорт в Excel"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в Excel",
            "",
            "Excel файлы (*.xlsx);;Все файлы (*.*)"
        )
        
        if filename:
            try:
                # Обновляем данные проекта
                self.current_project.pool_params = self.pool_designer.get_parameters()
                self.current_project.materials = self.materials_table.get_materials()
                self.current_project.works = self.works_table.get_works()
                
                # Экспортируем
                self.current_project.export_excel(filename)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Данные успешно экспортированы в {filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось экспортировать данные: {str(e)}"
                )
    
    def export_pdf(self):
        """Экспорт в PDF"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт в PDF",
            "",
            "PDF файлы (*.pdf);;Все файлы (*.*)"
        )
        
        if filename:
            try:
                # Обновляем данные проекта
                self.current_project.pool_params = self.pool_designer.get_parameters()
                self.current_project.materials = self.materials_table.get_materials()
                self.current_project.works = self.works_table.get_works()
                
                # Экспортируем
                self.current_project.export_pdf(filename)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Данные успешно экспортированы в {filename}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось экспортировать данные: {str(e)}"
                )
    
    def update_prices(self):
        """Обновить цены"""
        percentage, ok = QInputDialog.getDouble(
            self,
            "Обновление цен",
            "Введите процент изменения цен (например, 10 или -5):",
            0, -100, 100, 2
        )
        
        if ok:
            try:
                # Обновляем данные проекта
                self.current_project.materials = self.materials_table.get_materials()
                self.current_project.works = self.works_table.get_works()
                
                # Обновляем цены
                self.current_project.update_prices(percentage)
                
                # Обновляем таблицы
                self.materials_table.set_materials(self.current_project.materials)
                self.works_table.set_works(self.current_project.works)
                
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Цены успешно обновлены на {percentage}%"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Не удалось обновить цены: {str(e)}"
                )
    
    def recalculate_quantities(self):
        """Пересчитать количество материалов и работ"""
        try:
            # Получаем параметры бассейна
            params = self.pool_designer.get_parameters()
            
            # Рассчитываем материалы и работы
            materials = PoolCalculator.calculate_materials(params)
            works = PoolCalculator.calculate_works(params)
            
            # Обновляем таблицы
            self.materials_table.set_materials(materials)
            self.works_table.set_works(works)
            
            QMessageBox.information(
                self,
                "Успех",
                "Количество материалов и работ успешно пересчитано"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось пересчитать количество: {str(e)}"
            )
    
    def update_calculations(self):
        """Обновить расчеты при изменении параметров"""
        try:
            # Обновляем предпросмотр
            self.preview.set_parameters(self.pool_designer.get_parameters())
            
            # Автоматически пересчитываем количество
            self.recalculate_quantities()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Не удалось обновить расчеты: {str(e)}"
            )
    
    def about(self):
        QMessageBox.about(self, "О программе",
                         "Калькулятор Бассейнов\n\n"
                         "Версия 1.0\n"
                         " 2025 Все права защищены")
