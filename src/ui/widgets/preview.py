from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QFont
from PyQt6.QtCore import Qt, QPointF

class PoolPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.pool_params = {
            'shape': 'Прямоугольный',
            'length': 8500,
            'width': 3600,
            'depth': 2000
        }
        self.setMinimumSize(300, 200)
        
    def set_parameters(self, params):
        """Установить параметры бассейна для отображения"""
        try:
            if not params:
                return
            self.pool_params = params.copy()  # Создаем копию, чтобы избежать проблем с ссылками
            self.update()  # Перерисовать виджет
        except Exception as e:
            print(f"Ошибка при установке параметров: {str(e)}")
            
    def paintEvent(self, event):
        try:
            if not self.pool_params:
                return
                
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Настраиваем перо
            pen = QPen(Qt.GlobalColor.black)
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Получаем размеры виджета
            width = self.width()
            height = self.height()
            
            # Определяем форму бассейна
            shape = self.pool_params.get('shape', 'Прямоугольный')
            
            if shape == "Прямоугольный":
                self._draw_rectangular_pool(painter, width, height)
            elif shape == "Овальный":
                self._draw_oval_pool(painter, width, height)
            elif shape == "L-образный":
                self._draw_l_shaped_pool(painter, width, height)
            else:  # Свободная форма
                self._draw_rectangular_pool(painter, width, height)
                
        except Exception as e:
            print(f"Ошибка при отрисовке: {str(e)}")
            painter = QPainter(self)
            painter.drawText(10, 20, f"Ошибка при отрисовке: {str(e)}")
    
    def _draw_rectangular_pool(self, painter, width, height):
        """Отрисовка прямоугольного бассейна"""
        try:
            # Получаем размеры бассейна
            pool_length = self.pool_params['length']
            pool_width = self.pool_params['width']
            
            # Определяем масштаб
            scale = min(width / pool_length, height / pool_width) * 0.8
            
            # Вычисляем размеры для отрисовки
            draw_length = pool_length * scale
            draw_width = pool_width * scale
            
            # Вычисляем координаты для центрирования
            x = (width - draw_length) / 2
            y = (height - draw_width) / 2
            
            # Рисуем прямоугольник (преобразуем координаты в целые числа)
            painter.drawRect(int(x), int(y), int(draw_length), int(draw_width))
            
            # Добавляем размеры
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            # Длина
            painter.drawText(
                int(x + draw_length/2 - 50),
                int(y - 10),
                f"{pool_length}мм"
            )
            
            # Ширина
            painter.drawText(
                int(x - 70),
                int(y + draw_width/2),
                f"{pool_width}мм"
            )
            
            # Отрисовка ступеней
            if 'stairs' in self.pool_params and self.pool_params['stairs']:
                stair_x = x
                for stair in self.pool_params['stairs']:
                    stair_width = stair['width'] * scale
                    stair_height = stair['height'] * scale
                    painter.drawLine(
                        int(stair_x),
                        int(y),
                        int(stair_x),
                        int(y + stair_height)
                    )
                    stair_x += stair_width
                    
        except Exception as e:
            print(f"Ошибка при отрисовке прямоугольного бассейна: {str(e)}")
            painter.drawText(10, 40, "Ошибка при отрисовке прямоугольного бассейна")
    
    def _draw_oval_pool(self, painter, width, height):
        """Отрисовка овального бассейна"""
        try:
            # Получаем размеры бассейна
            pool_length = self.pool_params['length']
            pool_width = self.pool_params['width']
            
            # Определяем масштаб
            scale = min(width / pool_length, height / pool_width) * 0.8
            
            # Вычисляем размеры для отрисовки
            draw_length = pool_length * scale
            draw_width = pool_width * scale
            
            # Вычисляем координаты для центрирования
            x = (width - draw_length) / 2
            y = (height - draw_width) / 2
            
            # Рисуем овал
            painter.drawEllipse(int(x), int(y), int(draw_length), int(draw_width))
            
            # Добавляем размеры
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            # Длина
            length_text = f"{pool_length}мм"
            painter.drawText(
                int(x + draw_length/2 - 50),
                int(y - 10),
                length_text
            )
            
            # Ширина
            width_text = f"{pool_width}мм"
            painter.drawText(
                int(x - 70),
                int(y + draw_width/2),
                width_text
            )
        except Exception as e:
            print(f"Ошибка при отрисовке овального бассейна: {str(e)}")
            painter.drawText(10, 40, "Ошибка при отрисовке овального бассейна")
    
    def _draw_l_shaped_pool(self, painter, width, height):
        """Отрисовка L-образного бассейна"""
        try:
            # Получаем размеры бассейна
            pool_length = self.pool_params['length']
            pool_width = self.pool_params['width']
            l_length = self.pool_params['l_length']
            l_width = self.pool_params['l_width']
            
            # Определяем масштаб
            scale = min(width / pool_length, height / pool_width) * 0.8
            
            # Вычисляем размеры для отрисовки
            draw_length = pool_length * scale
            draw_width = pool_width * scale
            draw_l_length = l_length * scale
            draw_l_width = l_width * scale
            
            # Вычисляем координаты для центрирования
            x = (width - draw_length) / 2
            y = (height - draw_width) / 2
            
            # Создаем путь для L-образного бассейна
            path = QPainterPath()
            path.moveTo(x, y)
            path.lineTo(x + draw_length, y)
            path.lineTo(x + draw_length, y + draw_l_width)
            path.lineTo(x + draw_length - draw_l_length, y + draw_l_width)
            path.lineTo(x + draw_length - draw_l_length, y + draw_width)
            path.lineTo(x, y + draw_width)
            path.closeSubpath()
            
            # Рисуем бассейн
            painter.drawPath(path)
            
            # Добавляем размеры
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            # Основная длина
            painter.drawText(
                int(x + draw_length/2 - 50),
                int(y - 10),
                f"{pool_length}мм"
            )
            
            # Основная ширина
            painter.drawText(
                int(x - 70),
                int(y + draw_width/2),
                f"{pool_width}мм"
            )
            
            # L-образная длина
            painter.drawText(
                int(x + draw_length - draw_l_length/2 - 50),
                int(y + draw_l_width + 20),
                f"{l_length}мм"
            )
            
            # L-образная ширина
            painter.drawText(
                int(x + draw_length + 10),
                int(y + draw_l_width/2),
                f"{l_width}мм"
            )
        except Exception as e:
            print(f"Ошибка при отрисовке L-образного бассейна: {str(e)}")
            painter.drawText(10, 40, "Ошибка при отрисовке L-образного бассейна")
