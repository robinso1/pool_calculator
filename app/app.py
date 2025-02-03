from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PoolCalculator:
    def __init__(self, length, width, shallow_depth, deep_depth, steps_count=3):
        self.length = length
        self.width = width
        self.shallow_depth = shallow_depth
        self.deep_depth = deep_depth
        self.steps_count = steps_count
        
    def calculate_dimensions(self):
        # Внутренние размеры
        internal = {
            "length": self.length,
            "width": self.width,
            "shallow_depth": self.shallow_depth,
            "deep_depth": self.deep_depth
        }
        
        # Наружные размеры (+ 50 см с каждой стороны)
        external = {
            "length": self.length + 1000,  # +50см с каждой стороны
            "width": self.width + 1000,
            "shallow_depth": self.shallow_depth + 300,
            "deep_depth": self.deep_depth + 300
        }
        
        # Размеры котлована (+ 80 см с каждой стороны от наружных)
        excavation = {
            "length": external["length"] + 1600,
            "width": external["width"] + 1600,
            "shallow_depth": external["shallow_depth"] + 300,
            "deep_depth": external["deep_depth"] + 300
        }
        
        return {
            "internal": internal,
            "external": external,
            "excavation": excavation
        }

    def calculate_areas(self):
        # Площадь дна
        bottom_area = (self.length * self.width) / 1_000_000  # в м²
        
        # Площадь стен
        avg_depth = (self.shallow_depth + self.deep_depth) / 2
        walls_area = ((self.length + self.width) * 2 * avg_depth) / 1_000_000  # в м²
        
        # Площадь ступеней
        step_width = 400  # мм
        step_height = self.shallow_depth / self.steps_count
        steps_area = (self.width * step_width * self.steps_count) / 1_000_000  # в м²
        
        # Общая площадь
        total_area = bottom_area + walls_area + steps_area
        
        return {
            "bottom": round(bottom_area, 2),
            "walls": round(walls_area, 2),
            "steps": round(steps_area, 2),
            "total": round(total_area, 2)
        }

    def calculate_volumes(self):
        dimensions = self.calculate_dimensions()
        
        # Объем котлована
        exc = dimensions["excavation"]
        avg_depth = (exc["shallow_depth"] + exc["deep_depth"]) / 2
        excavation_volume = (exc["length"] * exc["width"] * avg_depth) / 1_000_000_000  # в м³
        
        # Объем бетона М200 (подбетонка)
        concrete_m200_volume = (dimensions["external"]["length"] * 
                              dimensions["external"]["width"] * 100) / 1_000_000_000  # в м³
        
        # Объем бетона М300 (чаша)
        ext = dimensions["external"]
        avg_depth = (ext["shallow_depth"] + ext["deep_depth"]) / 2
        concrete_m300_volume = ((ext["length"] * ext["width"] * avg_depth) - 
                              (self.length * self.width * avg_depth)) / 1_000_000_000  # в м³
        
        return {
            "excavation": round(excavation_volume, 2),
            "concrete_m200": round(concrete_m200_volume, 2),
            "concrete_m300": round(concrete_m300_volume, 2)
        }

    def calculate_materials(self, pool_type="liner"):
        areas = self.calculate_areas()
        volumes = self.calculate_volumes()
        
        materials = {
            "sand": f"{round(volumes['excavation'] * 0.15, 2)} м³",
            "gravel": f"{round(volumes['excavation'] * 0.2, 2)} м³",
            "plywood_18mm": f"{round(areas['total'] * 1.1, 2)} м²",
            "rebar_12mm": f"{round(areas['total'] * 2 * 7.5, 2)} кг",
            "timber_50x50": f"{round((areas['total'] * 2), 2)} м.п.",
            "consumables": "комплект",
            "concrete_m200": f"{round(volumes['concrete_m200'], 2)} м³",
            "concrete_m300": f"{round(volumes['concrete_m300'], 2)} м³",
            "ground_angle": f"{round(areas['total'] * 0.5, 2)} м.п.",
            "concrete_pump": "услуга",
            "cement": f"{round(areas['total'] * 15, 2)} кг",
            "fibroazolit": f"{round(areas['total'] * 5, 2)} кг"
        }
        
        if pool_type == "ceramic":
            materials.update({
                "coverflex": f"{round(areas['total'] * 1.1, 2)} м²",
                "glue_ec3000": f"{round(areas['total'] * 7.5, 2)} кг",
                "plaster": f"{round(areas['total'] * 25, 2)} кг",
                "primer": f"{round(areas['total'] * 0.2, 2)} л",
                "coping_stone_glue": f"{round(areas['total'] * 0.3, 2)} кг",
                "coping_stone_grout": f"{round(areas['total'] * 0.2, 2)} кг",
                "sealant": f"{round(areas['total'] * 0.1, 2)} л"
            })
        else:  # liner
            materials.update({
                "pvc_membrane": f"{round(areas['total'] * 1.1, 2)} м²",
                "steelglast": f"{round(areas['total'] * 1.1, 2)} м²"
            })
            
        return materials

    def calculate_works(self):
        areas = self.calculate_areas()
        volumes = self.calculate_volumes()
        
        return {
            "pool_marking": "1 услуга",
            "leveling": "1 услуга",
            "territory_binding": "1 услуга",
            "ground_excavation": f"{round(volumes['excavation'], 2)} м³",
            "ground_removal": f"{round(volumes['excavation'], 2)} м³",
            "manual_finishing": f"{round(areas['total'], 2)} м²",
            "gravel_filling": f"{round(areas['total'], 2)} м²",
            "grounding_contour": f"{round(areas['total'], 2)} м.п.",
            "concrete_base": f"{round(areas['total'], 2)} м²",
            "formwork_installation": f"{round(areas['total'], 2)} м²",
            "reinforcement": f"{round(areas['total'], 2)} м²",
            "concrete_pouring": f"{round(volumes['concrete_m300'], 2)} м³",
            "steps_creation": f"{self.steps_count} шт",
            "mortgages_creation": f"{round(areas['total'] * 0.2, 2)} шт",
            "clay_backfilling": f"{round(volumes['excavation'] * 0.7, 2)} м³"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        
        calculator = PoolCalculator(
            length=float(data['length']),
            width=float(data['width']),
            shallow_depth=float(data['shallow_depth']),
            deep_depth=float(data['deep_depth']),
            steps_count=int(data.get('steps_count', 3))
        )
        
        pool_type = data.get('pool_type', 'liner')
        
        result = {
            'dimensions': calculator.calculate_dimensions(),
            'areas': calculator.calculate_areas(),
            'volumes': calculator.calculate_volumes(),
            'materials': calculator.calculate_materials(pool_type),
            'works': calculator.calculate_works()
        }
        
        logger.debug(f"Calculated result: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in calculate: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/export/excel', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        
        # Создаем Excel файл в памяти
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Размеры
        dimensions_df = pd.DataFrame({
            'Параметр': ['Длина', 'Ширина', 'Глубина (мелкая часть)', 'Глубина (глубокая часть)'],
            'Внутренние (мм)': [
                data['dimensions']['internal']['length'],
                data['dimensions']['internal']['width'],
                data['dimensions']['internal']['shallow_depth'],
                data['dimensions']['internal']['deep_depth']
            ],
            'Внешние (мм)': [
                data['dimensions']['external']['length'],
                data['dimensions']['external']['width'],
                data['dimensions']['external']['shallow_depth'],
                data['dimensions']['external']['deep_depth']
            ],
            'Котлован (мм)': [
                data['dimensions']['excavation']['length'],
                data['dimensions']['excavation']['width'],
                data['dimensions']['excavation']['shallow_depth'],
                data['dimensions']['excavation']['deep_depth']
            ]
        })
        dimensions_df.to_excel(writer, sheet_name='Размеры', index=False)
        
        # Площади
        areas_df = pd.DataFrame({
            'Параметр': ['Дно', 'Стены', 'Ступени', 'Общая площадь'],
            'Площадь (м²)': [
                data['areas']['bottom'],
                data['areas']['walls'],
                data['areas']['steps'],
                data['areas']['total']
            ]
        })
        areas_df.to_excel(writer, sheet_name='Площади', index=False)
        
        # Объемы
        volumes_df = pd.DataFrame({
            'Параметр': ['Котлован', 'Бетон М200', 'Бетон М300'],
            'Объем (м³)': [
                data['volumes']['excavation'],
                data['volumes']['concrete_m200'],
                data['volumes']['concrete_m300']
            ]
        })
        volumes_df.to_excel(writer, sheet_name='Объемы', index=False)
        
        # Материалы
        materials_df = pd.DataFrame({
            'Материал': list(data['materials'].keys()),
            'Количество': list(data['materials'].values())
        })
        materials_df.to_excel(writer, sheet_name='Материалы', index=False)
        
        # Работы
        works_df = pd.DataFrame({
            'Работа': list(data['works'].keys()),
            'Количество': list(data['works'].values())
        })
        works_df.to_excel(writer, sheet_name='Работы', index=False)
        
        writer.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='pool_calculation.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Error in export_excel: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        
        # Создаем PDF файл в памяти
        output = io.BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Заголовок
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Расчет параметров бассейна")
        
        # Размеры
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 100, "Размеры:")
        
        c.setFont("Helvetica", 12)
        y = height - 120
        for dim_type, dims in data['dimensions'].items():
            y -= 20
            c.drawString(70, y, f"{dim_type.capitalize()}:")
            for key, value in dims.items():
                y -= 20
                c.drawString(90, y, f"{key}: {value} мм")
        
        # Площади
        y -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Площади:")
        
        c.setFont("Helvetica", 12)
        for key, value in data['areas'].items():
            y -= 20
            c.drawString(70, y, f"{key}: {value} м²")
        
        # Объемы
        y -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Объемы:")
        
        c.setFont("Helvetica", 12)
        for key, value in data['volumes'].items():
            y -= 20
            c.drawString(70, y, f"{key}: {value} м³")
        
        # Если достигли конца страницы, создаем новую
        if y < 100:
            c.showPage()
            y = height - 50
        
        # Материалы
        y -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Материалы:")
        
        c.setFont("Helvetica", 12)
        for key, value in data['materials'].items():
            y -= 20
            if y < 50:  # Если достигли конца страницы
                c.showPage()
                y = height - 50
            c.drawString(70, y, f"{key}: {value}")
        
        # Работы
        y -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Работы:")
        
        c.setFont("Helvetica", 12)
        for key, value in data['works'].items():
            y -= 20
            if y < 50:  # Если достигли конца страницы
                c.showPage()
                y = height - 50
            c.drawString(70, y, f"{key}: {value}")
        
        c.save()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='pool_calculation.pdf'
        )
        
    except Exception as e:
        logger.error(f"Error in export_pdf: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
