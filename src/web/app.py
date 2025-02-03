from flask import Flask, render_template, request, jsonify, send_file
from src.utils.calculator import PoolCalculator
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import tempfile
import os
import logging
import traceback
from xlsxwriter import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
calculator = PoolCalculator()

# Словарь с нормами расхода материалов
materials_rates = {
    'concrete_300': {'name': 'Бетон М300', 'unit': 'м³', 'consumption': 0.25, 'price': 4500},
    'concrete_200': {'name': 'Бетон М200', 'unit': 'м³', 'consumption': 0.1, 'price': 4000},
    'rebar_12': {'name': 'Арматура 12мм', 'unit': 'м.п.', 'consumption': 25, 'price': 80},
    'wire': {'name': 'Проволока вязальная', 'unit': 'кг', 'consumption': 0.3, 'price': 100},
    'geotextile': {'name': 'Геотекстиль', 'unit': 'м²', 'consumption': 1.15, 'price': 50},
    'waterproofing': {'name': 'Гидроизоляция', 'unit': 'м²', 'consumption': 2.5, 'price': 400},
    'insulation': {'name': 'Утеплитель', 'unit': 'м²', 'consumption': 1.15, 'price': 250},
    'plywood_form': {'name': 'Фанера опалубочная', 'unit': 'м²', 'consumption': 1.2, 'price': 800},
    'timber': {'name': 'Брус', 'unit': 'м³', 'consumption': 0.04, 'price': 12000},
    'nails': {'name': 'Гвозди', 'unit': 'кг', 'consumption': 0.2, 'price': 100},
    'liner': {'name': 'ПВХ пленка', 'unit': 'м²', 'consumption': 1.15, 'price': 800},
    'ceramic_tile': {'name': 'Керамогранит', 'unit': 'м²', 'consumption': 1.1, 'price': 1200},
    'mosaic': {'name': 'Мозаика', 'unit': 'м²', 'consumption': 1.1, 'price': 2500},
    'tile_adhesive': {'name': 'Плиточный клей', 'unit': 'кг', 'consumption': 7.5, 'price': 50},
    'grout': {'name': 'Затирка', 'unit': 'кг', 'consumption': 0.7, 'price': 150},
    'primer': {'name': 'Грунтовка', 'unit': 'л', 'consumption': 0.4, 'price': 200},
    'sealant': {'name': 'Герметик', 'unit': 'л', 'consumption': 0.3, 'price': 300},
    'border': {'name': 'Бордюр', 'unit': 'м.п.', 'consumption': 1.1, 'price': 400},
    'profile': {'name': 'Профиль', 'unit': 'м.п.', 'consumption': 1.1, 'price': 250},
    'plywood_18': {'name': 'Фанера 18мм', 'unit': 'м²', 'consumption': 1.2, 'price': 900}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rates')
def get_rates():
    return jsonify(materials_rates)

@app.route('/rates/<code>', methods=['PUT'])
def update_rate(code):
    try:
        if code not in materials_rates:
            return jsonify({'error': 'Материал не найден'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400
            
        if 'consumption' in data:
            try:
                consumption = float(data['consumption'])
                if consumption <= 0:
                    return jsonify({'error': 'Расход должен быть положительным числом'}), 400
                materials_rates[code]['consumption'] = consumption
            except (ValueError, TypeError):
                return jsonify({'error': 'Некорректное значение расхода'}), 400
                
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    return jsonify({'error': 'Цена не может быть отрицательной'}), 400
                materials_rates[code]['price'] = price
            except (ValueError, TypeError):
                return jsonify({'error': 'Некорректное значение цены'}), 400
                
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f'Ошибка при обновлении нормы расхода: {str(e)}')
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные для расчета'}), 400
            
        required_fields = ['length', 'width', 'shallow_depth', 'deep_depth', 'pool_type', 'finish_type', 'steps_count']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Отсутствуют обязательные поля: {", ".join(missing_fields)}'}), 400
            
        try:
            length = float(data['length'])
            width = float(data['width'])
            shallow_depth = float(data['shallow_depth'])
            deep_depth = float(data['deep_depth'])
            steps_count = int(data['steps_count'])
            
            if length <= 0 or width <= 0:
                return jsonify({'error': 'Размеры должны быть положительными числами'}), 400
            if shallow_depth <= 0 or deep_depth <= 0:
                return jsonify({'error': 'Глубина должна быть положительным числом'}), 400
            if shallow_depth > deep_depth:
                return jsonify({'error': 'Глубина мелкой части не может быть больше глубокой'}), 400
            if steps_count < 0 or steps_count > 6:
                return jsonify({'error': 'Количество ступеней должно быть от 0 до 6'}), 400
                
        except (ValueError, TypeError):
            return jsonify({'error': 'Некорректные значения размеров или количества ступеней'}), 400
            
        pool_type = data['pool_type']
        finish_type = data['finish_type']
        
        if pool_type not in ['ceramic', 'liner']:
            return jsonify({'error': 'Неверный тип бассейна'}), 400
        if pool_type == 'ceramic' and finish_type not in ['ceramic', 'mosaic']:
            return jsonify({'error': 'Неверный тип отделки'}), 400
            
        # Расчет площадей
        calculator = PoolCalculator()
        calculator.calculate_areas(length, width, shallow_depth, deep_depth, steps_count)
        
        # Расчет материалов
        results = []
        for material, quantity in calculator.calculate_materials(pool_type, finish_type).items():
            if material in materials_rates:
                rate = materials_rates[material]
                total = quantity * rate['price']
                results.append({
                    'name': rate['name'],
                    'unit': rate['unit'],
                    'quantity': round(quantity, 2),
                    'price': rate['price'],
                    'total': round(total, 2)
                })
                
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f'Ошибка при расчете: {str(e)}')
        return jsonify({'error': 'Ошибка при расчете'}), 500

@app.route('/export/excel', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные для экспорта'}), 400
            
        # Расчет как в /calculate
        calculator = PoolCalculator()
        calculator.calculate_areas(
            float(data['length']), 
            float(data['width']), 
            float(data['shallow_depth']), 
            float(data['deep_depth']), 
            int(data['steps_count'])
        )
        
        materials = calculator.calculate_materials(
            data['pool_type'],
            data['finish_type']
        )
        
        # Создаем Excel файл
        output = BytesIO()
        workbook = Workbook(output)
        worksheet = workbook.add_worksheet()
        
        # Форматирование
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        money_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '# ##0.00 ₽'
        })
        
        # Заголовки
        headers = ['Материал', 'Ед. изм.', 'Количество', 'Цена за ед.', 'Стоимость']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            
        # Данные
        row = 1
        total_cost = 0
        for material, quantity in materials.items():
            if material in materials_rates:
                rate = materials_rates[material]
                total = quantity * rate['price']
                total_cost += total
                
                worksheet.write(row, 0, rate['name'], cell_format)
                worksheet.write(row, 1, rate['unit'], cell_format)
                worksheet.write(row, 2, round(quantity, 2), cell_format)
                worksheet.write(row, 3, rate['price'], money_format)
                worksheet.write(row, 4, total, money_format)
                row += 1
                
        # Итого
        worksheet.write(row, 3, 'Итого:', header_format)
        worksheet.write(row, 4, total_cost, money_format)
        
        # Авторазмер колонок
        worksheet.autofit()
        
        workbook.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='pool_calculation.xlsx'
        )
        
    except Exception as e:
        app.logger.error(f'Ошибка при экспорте в Excel: {str(e)}')
        return jsonify({'error': 'Ошибка при экспорте в Excel'}), 500

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные для экспорта'}), 400
            
        # Расчет как в /calculate
        calculator = PoolCalculator()
        calculator.calculate_areas(
            float(data['length']), 
            float(data['width']), 
            float(data['shallow_depth']), 
            float(data['deep_depth']), 
            int(data['steps_count'])
        )
        
        materials = calculator.calculate_materials(
            data['pool_type'],
            data['finish_type']
        )
        
        # Создаем PDF
        output = BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=1,
            spaceAfter=30
        )
        
        # Элементы документа
        elements = []
        
        # Заголовок
        elements.append(Paragraph('Расчет материалов для бассейна', title_style))
        
        # Параметры бассейна
        elements.append(Paragraph(
            f'Размеры: {data["length"]/1000:.1f}м x {data["width"]/1000:.1f}м\n'
            f'Глубина: {data["shallow_depth"]/1000:.1f}м - {data["deep_depth"]/1000:.1f}м\n'
            f'Тип бассейна: {"Керамогранит" if data["pool_type"] == "ceramic" else "ПВХ пленка"}\n'
            f'Количество ступеней: {data["steps_count"]}',
            styles['Normal']
        ))
        elements.append(Spacer(1, 20))
        
        # Таблица материалов
        table_data = [['Материал', 'Ед. изм.', 'Кол-во', 'Цена', 'Стоимость']]
        total_cost = 0
        
        for material, quantity in materials.items():
            if material in materials_rates:
                rate = materials_rates[material]
                total = quantity * rate['price']
                total_cost += total
                
                table_data.append([
                    rate['name'],
                    rate['unit'],
                    f'{quantity:.2f}',
                    f'{rate["price"]:,.2f} ₽',
                    f'{total:,.2f} ₽'
                ])
                
        # Добавляем итого
        table_data.append(['', '', '', 'Итого:', f'{total_cost:,.2f} ₽'])
        
        # Создаем таблицу
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -2), 0.25, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (-2, -1), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        # Генерируем PDF
        doc.build(elements)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='pool_calculation.pdf'
        )
        
    except Exception as e:
        app.logger.error(f'Ошибка при экспорте в PDF: {str(e)}')
        return jsonify({'error': 'Ошибка при экспорте в PDF'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
