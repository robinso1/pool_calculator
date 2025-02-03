from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import math

logger = logging.getLogger(__name__)

@dataclass
class PoolDimensions:
    """Размеры бассейна"""
    length: float  # Внутренняя длина
    width: float  # Внутренняя ширина
    shallow_depth: float  # Глубина мелкой части
    deep_depth: float  # Глубина глубокой части
    steps_count: int  # Количество ступеней
    
    @property
    def outer_length(self) -> float:
        """Наружная длина (внутренняя + 50см с каждой стороны)"""
        return self.length + 1.0
        
    @property
    def outer_width(self) -> float:
        """Наружная ширина (внутренняя + 50см с каждой стороны)"""
        return self.width + 1.0
        
    @property
    def pit_length(self) -> float:
        """Длина котлована (наружная + 80см с каждой стороны)"""
        return self.outer_length + 1.6
        
    @property
    def pit_width(self) -> float:
        """Ширина котлована (наружная + 80см с каждой стороны)"""
        return self.outer_width + 1.6

@dataclass
class PoolAreas:
    """Площади бассейна"""
    bottom: float  # Площадь дна
    walls: float  # Площадь стен
    steps: float  # Площадь ступеней
    outer: float  # Наружная площадь
    pit: float  # Площадь котлована
    
    @property
    def total(self) -> float:
        """Общая площадь (дно + стены + ступени)"""
        return self.bottom + self.walls + self.steps

@dataclass
class PoolVolumes:
    """Объемы бассейна"""
    pit: float  # Объем котлована
    concrete_200: float  # Объем бетона М200 (подбетонка)
    concrete_300: float  # Объем бетона М300 (стены и дно)
    
class PoolCalculator:
    def __init__(self):
        self.dimensions: Optional[PoolDimensions] = None
        self.areas: Optional[PoolAreas] = None
        self.volumes: Optional[PoolVolumes] = None
        
    def calculate_dimensions(self, length_mm: float, width_mm: float, 
                           shallow_depth_mm: float, deep_depth_mm: float,
                           steps_count: int) -> None:
        """Расчет размеров бассейна"""
        # Переводим миллиметры в метры
        self.dimensions = PoolDimensions(
            length=length_mm / 1000,
            width=width_mm / 1000,
            shallow_depth=shallow_depth_mm / 1000,
            deep_depth=deep_depth_mm / 1000,
            steps_count=steps_count
        )
        logger.debug(f"Размеры рассчитаны: {self.dimensions}")
        
    def calculate_areas(self) -> None:
        """Расчет площадей бассейна"""
        if not self.dimensions:
            raise ValueError("Сначала необходимо рассчитать размеры")
            
        # Площадь дна
        bottom = self.dimensions.length * self.dimensions.width
        
        # Площадь стен
        # Торцевые стены (трапеция)
        end_wall = self.dimensions.width * (self.dimensions.shallow_depth + self.dimensions.deep_depth) / 2
        # Боковые стены
        side_wall_shallow = self.dimensions.length * self.dimensions.shallow_depth
        side_wall_deep = self.dimensions.length * self.dimensions.deep_depth
        walls = (end_wall * 2) + side_wall_shallow + side_wall_deep
        
        # Площадь ступеней
        steps = 0
        if self.dimensions.steps_count > 0:
            step_width = 0.3  # 30см
            step_height = 0.15  # 15см
            # Учитываем горизонтальную и вертикальную часть
            steps = self.dimensions.width * (step_width + step_height) * self.dimensions.steps_count
            
        # Наружная площадь
        outer = self.dimensions.outer_length * self.dimensions.outer_width
        
        # Площадь котлована
        pit = self.dimensions.pit_length * self.dimensions.pit_width
        
        self.areas = PoolAreas(
            bottom=bottom,
            walls=walls,
            steps=steps,
            outer=outer,
            pit=pit
        )
        logger.debug(f"Площади рассчитаны: {self.areas}")
        
    def calculate_volumes(self) -> None:
        """Расчет объемов бассейна"""
        if not self.dimensions or not self.areas:
            raise ValueError("Сначала необходимо рассчитать размеры и площади")
            
        # Объем котлована
        # +45см: 25см бетон + 20см подготовка
        shallow_volume = (self.dimensions.pit_length * self.dimensions.pit_width * 
                         (self.dimensions.shallow_depth + 0.45))
        deep_volume = (self.dimensions.pit_length * self.dimensions.pit_width * 
                      (self.dimensions.deep_depth + 0.45))
        pit = (shallow_volume + deep_volume) / 2
        
        # Объем бетона М200 (подбетонка 10см)
        concrete_200 = self.areas.outer * 0.1
        
        # Объем бетона М300 (стены и дно 25см)
        concrete_300 = (self.areas.walls + self.areas.bottom) * 0.25
        
        self.volumes = PoolVolumes(
            pit=pit,
            concrete_200=concrete_200,
            concrete_300=concrete_300
        )
        logger.debug(f"Объемы рассчитаны: {self.volumes}")
        
    def calculate_materials_base(self) -> Dict[str, float]:
        """Базовые материалы для обоих типов бассейнов"""
        if not self.dimensions or not self.areas or not self.volumes:
            raise ValueError("Сначала необходимо рассчитать все параметры")
            
        materials = {}
        
        # Фанера 18мм (наружная опалубка)
        materials['plywood_18'] = (self.areas.outer + self.areas.walls) * 1.1  # +10% на подрезку
        
        # Арматура 12мм (двойной каркас)
        total_concrete_area = self.areas.walls + self.areas.bottom
        materials['rebar_12'] = total_concrete_area * 20  # 20м.п. на м² для двойного каркаса
        
        # Брус 50х50 (периметр снаружи и внутри, два слоя)
        outer_perimeter = 2 * (self.dimensions.outer_length + self.dimensions.outer_width)
        inner_perimeter = 2 * (self.dimensions.length + self.dimensions.width)
        materials['timber_50x50'] = (outer_perimeter + inner_perimeter) * 2  # два слоя
        
        # Бетон
        materials['concrete_200'] = self.volumes.concrete_200
        materials['concrete_300'] = self.volumes.concrete_300
        
        # Расходники
        materials['wire'] = total_concrete_area * 0.3  # 0.3кг на м²
        materials['consumables'] = 1  # комплект
        
        # Копинговый камень
        perimeter = 2 * (self.dimensions.length + self.dimensions.width)
        materials['coping_stone'] = perimeter * 1.1  # +10% на подрезку
        materials['adhesive_80'] = math.ceil(perimeter / 5)  # 1 мешок на 5м
        materials['grout'] = perimeter * 0.2  # 0.2кг на м.п.
        materials['sealant'] = math.ceil(perimeter / 4)  # 1 тюбик на 4м
        
        # Грунтовка и штукатурка
        total_area = self.areas.total
        materials['primer'] = math.ceil(total_area / 100)  # 1 канистра на 100м²
        materials['adhesive_ec3000'] = math.ceil(total_area / 8)  # 1 мешок на 8м²
        materials['plaster'] = math.ceil(total_area * 1.5)  # 1.5 мешка на м²
        
        # Комплекты
        materials['ground_corner'] = 1  # уголок для заземления
        materials['concrete_pump'] = 1  # услуги бетононасоса
        materials['cement'] = 2  # два мешка про запас
        materials['fibroazolit'] = 1  # комплект
        
        return materials
        
    def calculate_materials_liner(self) -> Dict[str, float]:
        """Расчет материалов для бассейна с отделкой лайнером"""
        materials = self.calculate_materials_base()
        
        # Добавляем материалы для лайнера
        total_area = self.areas.total
        materials['geotextile'] = total_area * 1.15  # +15% на нахлесты
        materials['waterproofing'] = total_area * 2.5  # 2.5 слоя
        materials['liner'] = total_area * 1.15  # +15% на сварку
        
        return materials
        
    def calculate_materials_ceramic(self, finish_type: str) -> Dict[str, float]:
        """Расчет материалов для бассейна с отделкой керамогранитом/мозаикой"""
        materials = self.calculate_materials_base()
        
        total_area = self.areas.total
        
        # Гидроизоляция
        materials['coverflex'] = total_area * 1.1  # +10% на потери
        materials['fiberglass_mesh'] = total_area * 1.15  # +15% на нахлесты
        
        # Лента для углов
        corners_length = (self.dimensions.length + self.dimensions.width) * 2  # периметр дна
        materials['litoband'] = corners_length * 1.2  # +20% на нахлесты
        
        if finish_type == 'ceramic':
            # Керамогранит
            materials['ceramic_tile'] = total_area * 1.1  # +10% на подрезку
            materials['tile_adhesive'] = total_area * 7.5  # 7.5кг на м²
        else:
            # Мозаика
            materials['mosaic'] = total_area * 1.15  # +15% на подрезку
            materials['mosaic_adhesive'] = total_area * 5  # 5кг на м²
            
        # Общие материалы для обоих типов
        materials['latex_additive'] = total_area * 0.3  # 0.3л на м²
        materials['epoxy_grout'] = total_area * 0.7  # 0.7кг на м²
        materials['grout_cleaner'] = math.ceil(total_area / 50)  # 1 комплект на 50м²
        
        return materials
        
    def calculate_works(self) -> List[Dict[str, any]]:
        """Расчет работ"""
        if not self.dimensions or not self.areas or not self.volumes:
            raise ValueError("Сначала необходимо рассчитать все параметры")
            
        works = []
        
        # Подготовительные работы
        works.append({
            'name': 'Разметка бассейна для техники',
            'unit': 'м²',
            'quantity': self.areas.pit
        })
        
        works.append({
            'name': 'Нивелировка и привязка к территории',
            'unit': 'услуга',
            'quantity': 1
        })
        
        # Земляные работы
        works.append({
            'name': 'Выемка грунта под чашу бассейна',
            'unit': 'м³',
            'quantity': self.volumes.pit
        })
        
        works.append({
            'name': 'Вывоз грунта',
            'unit': 'рейс',
            'quantity': math.ceil(self.volumes.pit / 6)  # КАМАЗ 6м³
        })
        
        works.append({
            'name': 'Доработка грунта вручную',
            'unit': 'м²',
            'quantity': self.areas.pit
        })
        
        works.append({
            'name': 'Отсыпка щебнем 10см',
            'unit': 'м²',
            'quantity': self.areas.outer
        })
        
        # Бетонные работы
        works.append({
            'name': 'Устройство контура заземления',
            'unit': 'шт',
            'quantity': 1
        })
        
        works.append({
            'name': 'Бетонирование подбетонки',
            'unit': 'м³',
            'quantity': self.volumes.concrete_200
        })
        
        works.append({
            'name': 'Монтаж опалубки и армирование',
            'unit': 'м²',
            'quantity': self.areas.walls + self.areas.bottom
        })
        
        works.append({
            'name': 'Бетонирование чаши',
            'unit': 'м³',
            'quantity': self.volumes.concrete_300
        })
        
        # Ступени
        if self.dimensions.steps_count > 0:
            works.append({
                'name': 'Изготовление ступеней',
                'unit': 'шт',
                'quantity': self.dimensions.steps_count
            })
            
        # Отделочные работы
        works.append({
            'name': 'Обратная отсыпка глиной',
            'unit': 'м³',
            'quantity': self.volumes.pit * 0.3  # 30% от объема котлована
        })
        
        works.append({
            'name': 'Грунтовка под штукатурку',
            'unit': 'м²',
            'quantity': self.areas.total
        })
        
        works.append({
            'name': 'Нанесение клея под гребенку',
            'unit': 'м²',
            'quantity': self.areas.total
        })
        
        works.append({
            'name': 'Штукатурка',
            'unit': 'м²',
            'quantity': self.areas.total
        })
        
        works.append({
            'name': 'Грунтовка борта и ступеней',
            'unit': 'м²',
            'quantity': self.areas.steps + 
                       (2 * (self.dimensions.length + self.dimensions.width) * 0.25)  # периметр * высота борта
        })
        
        return works
