from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
                             QGroupBox, QFormLayout, QGridLayout, QScrollArea)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt

class PoolDesigner(QWidget):
    # Сигнал об изменении параметров
    parameters_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Форма бассейна
        shape_group = QGroupBox("Форма бассейна")
        shape_layout = QFormLayout()
        
        self.shape_type = QComboBox()
        self.shape_type.addItems(["Прямоугольный", "Овальный", "L-образный", "Свободная форма"])
        shape_layout.addRow("Тип:", self.shape_type)
        
        shape_group.setLayout(shape_layout)
        layout.addWidget(shape_group)
        
        # Группа основных размеров
        dimensions_group = self._create_dimension_inputs()
        layout.addWidget(dimensions_group)
        
        # Группа ступеней
        self.stairs_group = self.setup_stairs_section()
        layout.addWidget(self.stairs_group)
        
        # Тип отделки
        finish_group = QGroupBox("Отделка")
        finish_layout = QFormLayout()
        
        self.finish_type = QComboBox()
        self.finish_type.addItems(["Плитка", "Лайнер"])
        finish_layout.addRow("Тип:", self.finish_type)
        
        finish_group.setLayout(finish_layout)
        layout.addWidget(finish_group)
        
        # Подключаем сигналы
        self.length_spin.valueChanged.connect(self.parameters_changed)
        self.width_spin.valueChanged.connect(self.parameters_changed)
        self.depth_spin.valueChanged.connect(self.parameters_changed)
        self.finish_type.currentIndexChanged.connect(self.parameters_changed)
        self.shape_type.currentIndexChanged.connect(self._on_shape_changed)
        self.shape_type.currentIndexChanged.connect(self.parameters_changed)
        
        # Инициализируем поля для ступеней
        self.update_stairs_fields()
        
    def _create_dimension_inputs(self):
        """Создание полей ввода размеров"""
        dimensions_group = QGroupBox("Размеры")
        layout = QGridLayout()
        
        # Длина
        layout.addWidget(QLabel("Длина (мм):"), 0, 0)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1000, 50000)  # Мин. 1м, макс. 50м
        self.length_spin.setValue(8500)
        self.length_spin.setSingleStep(100)
        layout.addWidget(self.length_spin, 0, 1)
        
        # Ширина
        layout.addWidget(QLabel("Ширина (мм):"), 1, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1000, 25000)  # Мин. 1м, макс. 25м
        self.width_spin.setValue(3600)
        self.width_spin.setSingleStep(100)
        layout.addWidget(self.width_spin, 1, 1)
        
        # Глубина
        layout.addWidget(QLabel("Глубина (мм):"), 2, 0)
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1000, 5000)  # Мин. 1м, макс. 5м
        self.depth_spin.setValue(2000)
        self.depth_spin.setSingleStep(100)
        layout.addWidget(self.depth_spin, 2, 1)
        
        # L-образные размеры
        layout.addWidget(QLabel("L-ширина (мм):"), 3, 0)
        self.l_width_spin = QSpinBox()
        self.l_width_spin.setRange(1000, 25000)
        self.l_width_spin.setValue(3000)
        self.l_width_spin.setSingleStep(100)
        layout.addWidget(self.l_width_spin, 3, 1)
        
        layout.addWidget(QLabel("L-длина (мм):"), 4, 0)
        self.l_length_spin = QSpinBox()
        self.l_length_spin.setRange(1000, 50000)
        self.l_length_spin.setValue(3000)
        self.l_length_spin.setSingleStep(100)
        layout.addWidget(self.l_length_spin, 4, 1)
        
        # Скрываем L-размеры по умолчанию
        self.l_width_spin.hide()
        self.l_length_spin.hide()
        layout.itemAtPosition(3, 0).widget().hide()
        layout.itemAtPosition(4, 0).widget().hide()
        
        dimensions_group.setLayout(layout)
        return dimensions_group
        
    def setup_stairs_section(self):
        self.stairs_group = QGroupBox("Ступени")
        main_layout = QVBoxLayout()
        
        # Количество ступеней
        stairs_count_layout = QHBoxLayout()
        self.stairs_count_label = QLabel("Количество:")
        self.stairs_count = QSpinBox()
        self.stairs_count.setMinimum(0)
        self.stairs_count.setMaximum(6)
        stairs_count_layout.addWidget(self.stairs_count_label)
        stairs_count_layout.addWidget(self.stairs_count)
        stairs_count_layout.addStretch()
        main_layout.addLayout(stairs_count_layout)
        
        # Создаем область прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Контейнер для полей ступеней
        self.stairs_container = QWidget()
        self.stairs_layout = QVBoxLayout(self.stairs_container)
        self.stairs_layout.setSpacing(10)  # Отступ между ступенями
        self.stairs_layout.setContentsMargins(5, 5, 5, 5)  # Отступы от краев
        
        scroll.setWidget(self.stairs_container)
        main_layout.addWidget(scroll)
        
        self.stairs_group.setLayout(main_layout)
        
        # Подключаем сигнал изменения количества ступеней
        self.stairs_count.valueChanged.connect(self.update_stairs_fields)
        
        return self.stairs_group
        
    def update_stairs_fields(self):
        # Очищаем текущие поля
        while self.stairs_layout.count():
            child = self.stairs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        count = self.stairs_count.value()
        self.stair_fields = []
        
        for i in range(count):
            group = QGroupBox(f"Ступень {i+1}")
            group.setStyleSheet("QGroupBox { margin-top: 5px; }")
            layout = QFormLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(5)
            
            # Создаем поля для размеров ступени
            width_field = QSpinBox()
            width_field.setMinimum(200)  # минимум 20 см
            width_field.setMaximum(1000)  # максимум 1 метр
            width_field.setSingleStep(50)  # шаг 5 см
            width_field.setValue(300)  # по умолчанию 30 см
            width_field.setSuffix(" мм")
            
            height_field = QSpinBox()
            height_field.setMinimum(100)  # минимум 10 см
            height_field.setMaximum(300)  # максимум 30 см
            height_field.setSingleStep(50)  # шаг 5 см
            height_field.setValue(150)  # по умолчанию 15 см
            height_field.setSuffix(" мм")
            
            # Добавляем подсказки
            width_field.setToolTip("Ширина ступени (200-1000 мм)")
            height_field.setToolTip("Высота ступени (100-300 мм)")
            
            layout.addRow("Ширина:", width_field)
            layout.addRow("Высота:", height_field)
            
            group.setLayout(layout)
            self.stairs_layout.addWidget(group)
            
            # Сохраняем поля для доступа к значениям
            self.stair_fields.append({
                'width': width_field,
                'height': height_field
            })
            
            # Подключаем сигналы изменения размеров
            width_field.valueChanged.connect(lambda: self.delayed_update())
            height_field.valueChanged.connect(lambda: self.delayed_update())
        
        # Добавляем растягивающийся элемент в конец
        self.stairs_layout.addStretch()
        
        # Обновляем параметры
        self.parameters_changed.emit()
        
    def delayed_update(self):
        # Используем QTimer для задержки обновления
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        else:
            self.update_timer = QTimer()
            self.update_timer.setSingleShot(True)
            self.update_timer.timeout.connect(lambda: self.parameters_changed.emit())
        
        self.update_timer.start(300)  # 300 мс задержка
        
    def _on_shape_changed(self):
        """Обработка изменения формы бассейна"""
        shape = self.shape_type.currentText()
        # Показываем/скрываем дополнительные поля для L-образной формы
        self.l_width_spin.setVisible(shape == "L-образный")
        self.l_length_spin.setVisible(shape == "L-образный")
        self.l_width_spin.parent().layout().itemAtPosition(3, 0).widget().setVisible(shape == "L-образный")
        self.l_length_spin.parent().layout().itemAtPosition(4, 0).widget().setVisible(shape == "L-образный")
        
    def get_parameters(self):
        """Получить все параметры бассейна"""
        params = {
            'shape': self.shape_type.currentText(),
            'length': self.length_spin.value(),
            'width': self.width_spin.value(),
            'depth': self.depth_spin.value(),
            'finish_type': self.finish_type.currentText(),
        }
        
        # Добавляем размеры L-образной части если нужно
        if params['shape'] == "L-образный":
            l_width = self.l_width_spin.value()
            l_length = self.l_length_spin.value()
            
            # Проверяем корректность размеров
            if l_width >= params['width']:
                raise ValueError("Ширина L-части должна быть меньше основной ширины")
            if l_length >= params['length']:
                raise ValueError("Длина L-части должна быть меньше основной длины")
                
            params.update({
                'l_width': l_width,
                'l_length': l_length
            })
        
        # Добавляем параметры ступеней
        stairs = []
        for field in self.stair_fields:
            stairs.append({
                'height': field['height'].value(),
                'width': field['width'].value()
            })
        params['stairs'] = stairs
        
        return params

    def reset_to_defaults(self):
        """Сбросить все параметры на значения по умолчанию"""
        self.shape_type.setCurrentText("Прямоугольный")
        self.length_spin.setValue(8500)
        self.width_spin.setValue(3600)
        self.depth_spin.setValue(2000)
        self.l_width_spin.setValue(3000)
        self.l_length_spin.setValue(3000)
        self.stairs_count.setValue(5)
        self.finish_type.setCurrentText("Плитка")
        self.update_stairs_fields()
        
    def set_parameters(self, params):
        """Установить параметры из словаря"""
        if not params:
            return
            
        self.shape_type.setCurrentText(params.get('shape', "Прямоугольный"))
        self.length_spin.setValue(params.get('length', 8500))
        self.width_spin.setValue(params.get('width', 3600))
        self.depth_spin.setValue(params.get('depth', 2000))
        
        if params.get('shape') == "L-образный":
            self.l_width_spin.setValue(params.get('l_width', 3000))
            self.l_length_spin.setValue(params.get('l_length', 3000))
        
        self.finish_type.setCurrentText(params.get('finish_type', "Плитка"))
        
        # Устанавливаем ступени
        if 'stairs' in params:
            self.stairs_count.setValue(len(params['stairs']))
            self.update_stairs_fields()
            
            # Устанавливаем размеры ступеней
            for i, stair in enumerate(params['stairs']):
                if i < len(self.stair_fields):
                    self.stair_fields[i]['width'].setValue(stair.get('width', 300))
                    self.stair_fields[i]['height'].setValue(stair.get('height', 150))
