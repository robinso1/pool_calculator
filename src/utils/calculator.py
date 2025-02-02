import logging

logger = logging.getLogger(__name__)

class PoolCalculator:
    def __init__(self):
        self.wall_area = 0
        self.bottom_area = 0
        self.steps_area = 0
        self.total_area = 0
        self.length = 0
        self.width = 0
        
    def calculate_areas(self, length, width, steps_count):
        """Рассчитывает площади бассейна"""
        try:
            # Сохраняем размеры для дальнейших расчетов
            self.length = length / 1000  # в метрах
            self.width = width / 1000    # в метрах
            
            # Площадь дна
            self.bottom_area = self.length * self.width
            
            # Площадь стен (периметр * высота)
            self.wall_area = (2 * self.length + 2 * self.width) * 1.5  # высота 1.5м
            
            # Площадь ступеней
            if steps_count > 0:
                step_width = 0.3  # ширина ступени 30см
                self.steps_area = self.width * step_width * steps_count
            else:
                self.steps_area = 0
                
            # Общая площадь
            self.total_area = self.wall_area + self.bottom_area + self.steps_area
            
            logger.debug(f"Площади рассчитаны: дно={self.bottom_area:.2f}м², "
                      f"стены={self.wall_area:.2f}м², "
                      f"ступени={self.steps_area:.2f}м², "
                      f"всего={self.total_area:.2f}м²")
                      
        except Exception as e:
            logger.error(f"Ошибка при расчете площадей: {str(e)}")
            raise
            
    def calculate_materials(self, pool_type, finish_type):
        """Рассчитывает необходимые материалы"""
        try:
            materials = {}
            
            # Бетонное основание
            materials['concrete_300'] = self.bottom_area * 0.25  # толщина 25см
            materials['concrete_200'] = self.bottom_area * 0.1   # толщина 10см
            
            # Арматура и проволока
            materials['rebar_12'] = self.bottom_area * 25  # 25м.п. на м²
            materials['wire'] = self.bottom_area * 0.3     # 0.3кг на м²
            
            # Гидроизоляция и утепление
            materials['geotextile'] = self.total_area * 1.15     # +15% на нахлесты
            materials['waterproofing'] = self.total_area * 2.5   # 2.5 слоя
            materials['insulation'] = self.total_area * 1.15     # +15% на подрезку
            
            # Опалубка
            materials['plywood_form'] = self.wall_area * 1.2     # +20% на подрезку
            materials['timber'] = self.wall_area * 0.04          # 0.04м³ на м²
            materials['nails'] = self.wall_area * 0.2            # 0.2кг на м²
            
            if pool_type == 'liner':
                # ПВХ пленка
                materials['liner'] = self.total_area * 1.15      # +15% на сварку
                materials['plywood_18'] = self.wall_area * 1.2   # +20% на подрезку
                materials['profile'] = (2 * (self.length + self.width)) * 1.1  # +10% на подрезку
                
            elif pool_type == 'ceramic':
                # Керамогранит или мозаика
                tile_material = 'ceramic_tile' if finish_type == 'ceramic' else 'mosaic'
                materials[tile_material] = self.total_area * 1.1  # +10% на подрезку
                materials['tile_adhesive'] = self.total_area * 7.5  # 7.5кг на м²
                materials['grout'] = self.total_area * 0.7         # 0.7кг на м²
                materials['primer'] = self.total_area * 0.4        # 0.4л на м²
                materials['sealant'] = self.total_area * 0.3       # 0.3л на м²
                materials['border'] = (2 * (self.length + self.width)) * 1.1  # +10% на подрезку
                
            logger.debug(f"Материалы рассчитаны: {materials}")
            return materials
            
        except Exception as e:
            logger.error(f"Ошибка при расчете материалов: {str(e)}")
            raise
