import math
from typing import Dict, List, Union

class PoolCalculator:
    @staticmethod
    def validate_parameters(params: Dict) -> None:
        """Проверка корректности параметров бассейна"""
        required_params = ['length', 'width', 'depth', 'shape', 'finish_type']
        
        # Проверяем наличие всех обязательных параметров
        for param in required_params:
            if param not in params:
                raise ValueError(f"Отсутствует обязательный параметр: {param}")
        
        # Проверяем минимальные размеры
        if params['length'] < 2000:  # 2 метра
            raise ValueError("Длина бассейна должна быть не менее 2 метров")
        if params['width'] < 1500:   # 1.5 метра
            raise ValueError("Ширина бассейна должна быть не менее 1.5 метров")
        if params['depth'] < 600:     # 60 см
            raise ValueError("Глубина бассейна должна быть не менее 60 см")
        if params['depth'] > 2500:    # 2.5 метра
            raise ValueError("Глубина бассейна не должна превышать 2.5 метра")
            
        # Проверяем параметры L-образной формы
        if params['shape'] == "L-образный":
            if 'l_width' not in params or 'l_length' not in params:
                raise ValueError("Для L-образного бассейна необходимо указать размеры выступа (l_width и l_length)")
            if params['l_width'] >= params['width']:
                raise ValueError("Ширина выступа должна быть меньше общей ширины бассейна")
            if params['l_length'] >= params['length']:
                raise ValueError("Длина выступа должна быть меньше общей длины бассейна")
            if params['l_width'] < 1000:  # 1 метр
                raise ValueError("Ширина выступа должна быть не менее 1 метра")
            if params['l_length'] < 1000:  # 1 метр
                raise ValueError("Длина выступа должна быть не менее 1 метра")
                
        # Проверяем ступени
        if 'stairs' in params and params['stairs']:
            total_height = sum(stair['height'] for stair in params['stairs'])
            if total_height > params['depth']:
                raise ValueError(f"Общая высота ступеней ({total_height}мм) превышает глубину бассейна ({params['depth']}мм)")
            
            total_width = max(stair['width'] for stair in params['stairs'])
            if total_width > params['width']:
                raise ValueError(f"Ширина ступеней ({total_width}мм) превышает ширину бассейна ({params['width']}мм)")
    
    @staticmethod
    def calculate_materials(params: Dict) -> List[Dict[str, Union[str, float, int]]]:
        """Рассчитать количество материалов на основе параметров бассейна"""
        try:
            PoolCalculator.validate_parameters(params)
            
            materials = []
            
            # Получаем основные размеры
            length = params['length'] / 1000  # переводим в метры
            width = params['width'] / 1000
            depth = params['depth'] / 1000
            shape = params['shape']
            finish_type = params['finish_type']
            
            # Рассчитываем площади и объемы
            if shape == "Прямоугольный":
                bottom_area = length * width
                wall_area = 2 * (length + width) * depth
                perimeter = 2 * (length + width)
            elif shape == "Овальный":
                bottom_area = math.pi * (length/2) * (width/2)
                wall_area = math.pi * ((length + width)/2) * depth
                perimeter = math.pi * ((length + width)/2)
            elif shape == "L-образный":
                l_width = params['l_width'] / 1000
                l_length = params['l_length'] / 1000
                bottom_area = length * width - (length - l_length) * (width - l_width)
                wall_area = (2 * (length + width) - (length - l_length + width - l_width)) * depth
                perimeter = 2 * (length + width) - (length - l_length + width - l_width)
            else:
                raise ValueError(f"Неподдерживаемая форма бассейна: {shape}")
                
            total_area = bottom_area + wall_area
            excavation_volume = bottom_area * depth * 1.2  # +20% на запас
            
            # Расчет бетона и арматуры
            concrete_floor_thickness = 0.2  # толщина пола 20см
            concrete_wall_thickness = 0.2   # толщина стен 20см
            
            concrete_floor_volume = bottom_area * concrete_floor_thickness
            concrete_wall_volume = wall_area * concrete_wall_thickness
            total_concrete_volume = concrete_floor_volume + concrete_wall_volume
            
            # Арматура: двойной каркас из арматуры д12 с шагом 200мм
            rebar_step = 0.2  # шаг арматуры 200мм
            rebar_count_length = math.ceil((length + depth * 2) / rebar_step) * 2  # умножаем на 2 для двойного каркаса
            rebar_count_width = math.ceil((width + depth * 2) / rebar_step) * 2
            total_rebar_length = (length + depth * 2) * rebar_count_width + (width + depth * 2) * rebar_count_length
            rebar_weight_per_meter = 0.888  # вес погонного метра арматуры д12
            total_rebar_weight = total_rebar_length * rebar_weight_per_meter
            
            # Добавляем материалы с расчетными количествами
            materials.extend([
                # Земляные работы
                {"name": "Песок по факту", "unit": "м3", "quantity": round(excavation_volume * 0.15, 2), "price": 850},
                {"name": "Доставка песка", "unit": "услуга", "quantity": 1, "price": 3500},
                {"name": "Щебень по факту", "unit": "м3", "quantity": round(bottom_area * 0.15, 2), "price": 1150},
                {"name": "Доставка щебня", "unit": "услуга", "quantity": 1, "price": 3500},
                
                # Гидроизоляция
                {"name": "Стеклоэласт", "unit": "рулон", "quantity": math.ceil(total_area / 10), "price": 2225},  # 10м2 в рулоне
                {"name": "Праймер битумный AquaMast", "unit": "шт", "quantity": round(total_area / 25, 0), "price": 3800},
                
                # Утепление
                {"name": "Пенополистирол 50мм", "unit": "м2", "quantity": round(total_area * 1.1, 1), "price": 280},
                
                # Арматура и бетон
                {"name": "Арматура д12", "unit": "тонн", "quantity": round(total_rebar_weight / 1000, 2), "price": 60000},  # цена за тонну
                {"name": "Проволока вязальная", "unit": "кг", "quantity": round(total_rebar_weight * 0.01, 0), "price": 95},  # 1% от веса арматуры
                {"name": "Бетон М350", "unit": "м3", "quantity": round(total_concrete_volume * 1.1, 1), "price": 6500},  # +10% на технологические потери
            ])
            
            # Добавляем специфические материалы в зависимости от типа отделки
            if finish_type == "Плитка":
                materials.extend([
                    {"name": "Плиточный клей", "unit": "кг", "quantity": round(total_area * 4.5, 0), "price": 450},
                    {"name": "Затирка для швов", "unit": "кг", "quantity": round(total_area * 0.5, 0), "price": 800},
                    {"name": "Керамогранит/мозаика", "unit": "м2", "quantity": round(total_area * 1.05, 1), "price": 2500},
                ])
            else:  # Лайнер
                materials.extend([
                    {"name": "Лайнер ПВХ", "unit": "м2", "quantity": round(total_area * 1.1, 1), "price": 1200},
                    {"name": "Профиль крепежный", "unit": "м.п.", "quantity": round(perimeter, 1), "price": 350},
                    {"name": "Прижимной бортик", "unit": "м.п.", "quantity": round(perimeter, 1), "price": 450},
                ])
            
            return materials
            
        except Exception as e:
            print(f"Ошибка при расчете материалов: {str(e)}")
            raise

    @staticmethod
    def calculate_works(params: Dict) -> List[Dict[str, Union[str, float, int]]]:
        """Рассчитать объемы работ на основе параметров бассейна"""
        try:
            PoolCalculator.validate_parameters(params)
            
            works = []
            
            # Получаем основные размеры
            length = params['length'] / 1000  # переводим в метры
            width = params['width'] / 1000
            depth = params['depth'] / 1000
            shape = params['shape']
            finish_type = params['finish_type']
            
            # Рассчитываем площади и объемы
            if shape == "Прямоугольный":
                bottom_area = length * width
                wall_area = 2 * (length + width) * depth
                total_area = bottom_area + wall_area
                excavation_volume = bottom_area * depth
            elif shape == "Овальный":
                bottom_area = math.pi * (length/2) * (width/2)
                wall_area = math.pi * ((length + width)/2) * depth
                total_area = bottom_area + wall_area
                excavation_volume = bottom_area * depth
            elif shape == "L-образный":
                l_width = params['l_width'] / 1000
                l_length = params['l_length'] / 1000
                bottom_area = length * width - (length - l_length) * (width - l_width)
                wall_area = (2 * (length + width) - (length - l_length + width - l_width)) * depth
                total_area = bottom_area + wall_area
                excavation_volume = bottom_area * depth
            else:
                bottom_area = length * width
                wall_area = 2 * (length + width) * depth
                total_area = bottom_area + wall_area
                excavation_volume = bottom_area * depth
            
            # Добавляем работы с расчетными объемами
            works.extend([
                # Подготовительные работы
                {"name": "Разметка бассейна", "unit": "м2", "quantity": round(bottom_area, 1), "price": 300},
                {"name": "Выемка грунта", "unit": "м3", "quantity": round(excavation_volume * 1.2, 1), "price": 550},
                {"name": "Вывоз грунта", "unit": "КамАЗ", "quantity": round(excavation_volume / 7, 0), "price": 6500},
                {"name": "Работа с трактором", "unit": "услуга", "quantity": 1, "price": 15000},
                {"name": "Доработка грунта вручную", "unit": "м2", "quantity": round(bottom_area, 1), "price": 350},
                
                # Основные работы
                {"name": "Отсыпка щебенки", "unit": "м2", "quantity": round(bottom_area, 1), "price": 350},
                {"name": "Устройство контур заземления", "unit": "шт", "quantity": 1, "price": 7500},
                {"name": "Бетонирование подготовки", "unit": "м2", "quantity": round(bottom_area, 1), "price": 800},
                {"name": "Гидроизоляция бассейна", "unit": "м2", "quantity": round(total_area, 1), "price": 700},
                {"name": "Монтаж опалубки", "unit": "м3", "quantity": round(total_area * 0.2, 1), "price": 1500},
                {"name": "Армирование чаши бассейна", "unit": "м2", "quantity": round(total_area, 1), "price": 450},
                {"name": "Бетонирование чаши", "unit": "м3", "quantity": round(total_area * 0.2, 1), "price": 6500},
                
                # Отделочные работы для плитки
                {"name": "Выравнивание поверхности", "unit": "м2", "quantity": round(total_area, 1), "price": 400},
                {"name": "Укладка плитки", "unit": "м2", "quantity": round(total_area, 1), "price": 1200},
                {"name": "Затирка швов", "unit": "м2", "quantity": round(total_area, 1), "price": 250},
                
                # Отделочные работы для лайнера
                {"name": "Монтаж профиля", "unit": "м.п.", "quantity": round(2 * (length + width), 1), "price": 300},
                {"name": "Монтаж лайнера", "unit": "м2", "quantity": round(total_area, 1), "price": 500},
                {"name": "Монтаж бортового камня", "unit": "м.п.", "quantity": round(2 * (length + width), 1), "price": 450},
            ])
            
            # Фильтруем работы в зависимости от типа отделки
            if finish_type == "Плитка":
                works = [w for w in works if "лайнер" not in w["name"].lower() and "профил" not in w["name"].lower()]
            else:  # Лайнер
                works = [w for w in works if "плитк" not in w["name"].lower() and "затирк" not in w["name"].lower()]
            
            return works
            
        except Exception as e:
            print(f"Ошибка при расчете работ: {str(e)}")
            raise
