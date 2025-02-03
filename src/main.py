from flask import Flask, render_template, request, jsonify, send_file
from src.utils.calculator import PoolCalculator
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import io
import json
import logging
import os

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        
        # Создаем калькулятор и выполняем расчеты
        calculator = PoolCalculator()
        
        # Размеры
        calculator.calculate_dimensions(
            length_mm=float(data['length']),
            width_mm=float(data['width']),
            shallow_depth_mm=float(data['shallow_depth']),
            deep_depth_mm=float(data['deep_depth']),
            steps_count=int(data['steps_count'])
        )
        
        # Площади и объемы
        calculator.calculate_areas()
        calculator.calculate_volumes()
        
        # Материалы в зависимости от типа бассейна
        pool_type = data['pool_type']
        finish_type = data.get('finish_type', 'ceramic')
        
        if pool_type == 'liner':
            materials = calculator.calculate_materials_liner()
        else:
            materials = calculator.calculate_materials_ceramic(finish_type)
            
        # Работы
        works = calculator.calculate_works()
        
        # Формируем результат
        result = {
            'dimensions': {
                'internal': {
                    'length': calculator.dimensions.length,
                    'width': calculator.dimensions.width,
                    'shallow_depth': calculator.dimensions.shallow_depth,
                    'deep_depth': calculator.dimensions.deep_depth
                },
                'external': {
                    'length': calculator.dimensions.outer_length,
                    'width': calculator.dimensions.outer_width
                },
                'pit': {
                    'length': calculator.dimensions.pit_length,
                    'width': calculator.dimensions.pit_width
                }
            },
            'areas': {
                'bottom': calculator.areas.bottom,
                'walls': calculator.areas.walls,
                'steps': calculator.areas.steps,
                'total': calculator.areas.total,
                'outer': calculator.areas.outer,
                'pit': calculator.areas.pit
            },
            'volumes': {
                'pit': calculator.volumes.pit,
                'concrete_200': calculator.volumes.concrete_200,
                'concrete_300': calculator.volumes.concrete_300
            },
            'materials': materials,
            'works': works
        }
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"Ошибка при расчете: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export/excel', methods=['POST'])
def export_excel():
    try:
        data = request.json
        
        # Создаем Excel файл
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Размеры
        dimensions_df = pd.DataFrame([
            ['Внутренние размеры', f"{data['dimensions']['internal']['length']:.2f}x{data['dimensions']['internal']['width']:.2f}"],
            ['Глубина (мелкая часть)', f"{data['dimensions']['internal']['shallow_depth']:.2f}"],
            ['Глубина (глубокая часть)', f"{data['dimensions']['internal']['deep_depth']:.2f}"],
            ['Наружные размеры', f"{data['dimensions']['external']['length']:.2f}x{data['dimensions']['external']['width']:.2f}"],
            ['Размеры котлована', f"{data['dimensions']['pit']['length']:.2f}x{data['dimensions']['pit']['width']:.2f}"]
        ], columns=['Параметр', 'Значение'])
        dimensions_df.to_excel(writer, sheet_name='Размеры', index=False)
        
        # Площади
        areas_df = pd.DataFrame([
            ['Площадь дна', data['areas']['bottom'], 'м²'],
            ['Площадь стен', data['areas']['walls'], 'м²'],
            ['Площадь ступеней', data['areas']['steps'], 'м²'],
            ['Общая площадь', data['areas']['total'], 'м²'],
            ['Наружная площадь', data['areas']['outer'], 'м²'],
            ['Площадь котлована', data['areas']['pit'], 'м²']
        ], columns=['Параметр', 'Значение', 'Единица'])
        areas_df.to_excel(writer, sheet_name='Площади', index=False)
        
        # Объемы
        volumes_df = pd.DataFrame([
            ['Объем котлована', data['volumes']['pit'], 'м³'],
            ['Объем бетона М200', data['volumes']['concrete_200'], 'м³'],
            ['Объем бетона М300', data['volumes']['concrete_300'], 'м³']
        ], columns=['Параметр', 'Значение', 'Единица'])
        volumes_df.to_excel(writer, sheet_name='Объемы', index=False)
        
        # Материалы
        materials = [[k, v] for k, v in data['materials'].items()]
        materials_df = pd.DataFrame(materials, columns=['Материал', 'Количество'])
        materials_df.to_excel(writer, sheet_name='Материалы', index=False)
        
        # Работы
        works_df = pd.DataFrame(data['works'])
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
        logger.error(f"Ошибка при экспорте в Excel: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.json
        
        # Создаем PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Заголовок
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "Расчет бассейна")
        
        # Размеры
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 100, "Размеры:")
        p.setFont("Helvetica", 12)
        y = height - 120
        p.drawString(70, y, f"Внутренние: {data['dimensions']['internal']['length']:.2f}x{data['dimensions']['internal']['width']:.2f} м")
        y -= 20
        p.drawString(70, y, f"Глубина: {data['dimensions']['internal']['shallow_depth']:.2f}-{data['dimensions']['internal']['deep_depth']:.2f} м")
        y -= 20
        p.drawString(70, y, f"Наружные: {data['dimensions']['external']['length']:.2f}x{data['dimensions']['external']['width']:.2f} м")
        y -= 20
        p.drawString(70, y, f"Котлован: {data['dimensions']['pit']['length']:.2f}x{data['dimensions']['pit']['width']:.2f} м")
        
        # Площади
        y -= 40
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Площади:")
        p.setFont("Helvetica", 12)
        y -= 20
        p.drawString(70, y, f"Дно: {data['areas']['bottom']:.2f} м²")
        y -= 20
        p.drawString(70, y, f"Стены: {data['areas']['walls']:.2f} м²")
        y -= 20
        p.drawString(70, y, f"Ступени: {data['areas']['steps']:.2f} м²")
        y -= 20
        p.drawString(70, y, f"Общая: {data['areas']['total']:.2f} м²")
        
        # Объемы
        y -= 40
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Объемы:")
        p.setFont("Helvetica", 12)
        y -= 20
        p.drawString(70, y, f"Котлован: {data['volumes']['pit']:.2f} м³")
        y -= 20
        p.drawString(70, y, f"Бетон М200: {data['volumes']['concrete_200']:.2f} м³")
        y -= 20
        p.drawString(70, y, f"Бетон М300: {data['volumes']['concrete_300']:.2f} м³")
        
        # Материалы
        y -= 40
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Материалы:")
        p.setFont("Helvetica", 12)
        y -= 20
        for material, quantity in data['materials'].items():
            p.drawString(70, y, f"{material}: {quantity:.2f}")
            y -= 20
            if y < 50:  # Если место на странице заканчивается
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 12)
        
        # Работы
        if y < 100:  # Если осталось мало места, начинаем новую страницу
            p.showPage()
            y = height - 50
            
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Работы:")
        p.setFont("Helvetica", 12)
        y -= 20
        for work in data['works']:
            p.drawString(70, y, f"{work['name']}: {work['quantity']} {work['unit']}")
            y -= 20
            if y < 50:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 12)
        
        p.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='pool_calculation.pdf'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте в PDF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
