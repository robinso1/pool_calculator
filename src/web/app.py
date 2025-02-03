from flask import Flask, request, jsonify, render_template, send_file
from utils.calculator import PoolCalculator
import logging
import json
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = app.logger

# Коэффициенты и цены на материалы
materials_rates = {
    # Основные материалы
    'sand': {'name': 'Песок', 'unit': 'м³', 'price': 800},
    'gravel': {'name': 'Щебень', 'unit': 'м³', 'price': 1200},
    'concrete_200': {'name': 'Бетон М200', 'unit': 'м³', 'price': 4500},
    'concrete_300': {'name': 'Бетон М300', 'unit': 'м³', 'price': 5000},
    'rebar_12': {'name': 'Арматура 12мм', 'unit': 'м.п.', 'price': 80},
    'wire': {'name': 'Проволока вязальная', 'unit': 'кг', 'price': 100},
    'plywood_18': {'name': 'Фанера 18мм', 'unit': 'м²', 'price': 1200},
    'timber_50x50': {'name': 'Брус 50х50', 'unit': 'м.п.', 'price': 80},
    
    # Гидроизоляция
    'geotextile': {'name': 'Геотекстиль', 'unit': 'м²', 'price': 50},
    'waterproofing': {'name': 'Гидроизоляция', 'unit': 'м²', 'price': 300},
    'coverflex': {'name': 'CoverFlex', 'unit': 'кг', 'price': 400},
    'fiberglass_mesh': {'name': 'Стеклосетка', 'unit': 'м²', 'price': 60},
    'litoband': {'name': 'Лента Литобанд', 'unit': 'м.п.', 'price': 200},
    
    # Отделочные материалы
    'liner': {'name': 'ПВХ лайнер', 'unit': 'м²', 'price': 800},
    'ceramic_tile': {'name': 'Керамогранит', 'unit': 'м²', 'price': 1500},
    'mosaic': {'name': 'Мозаика', 'unit': 'м²', 'price': 2500},
    'tile_adhesive': {'name': 'Клей для керамогранита', 'unit': 'кг', 'price': 50},
    'mosaic_adhesive': {'name': 'Клей для мозаики', 'unit': 'кг', 'price': 80},
    'epoxy_grout': {'name': 'Затирка эпоксидная', 'unit': 'кг', 'price': 1200},
    
    # Бортовые материалы
    'coping_stone': {'name': 'Копинговый камень', 'unit': 'м.п.', 'price': 1800},
    'adhesive_80': {'name': 'Клей для копинга', 'unit': 'кг', 'price': 80},
    'grout': {'name': 'Затирка для копинга', 'unit': 'кг', 'price': 150},
    'sealant': {'name': 'Герметик', 'unit': 'шт', 'price': 400},
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные для расчета'}), 400
            
        required_fields = ['length', 'width', 'shallow_depth', 'deep_depth', 
                         'pool_type', 'finish_type', 'steps_count']
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
            
        # Расчет размеров и площадей
        calculator = PoolCalculator()
        calculator.calculate_dimensions(length, width, shallow_depth, deep_depth)
        calculator.calculate_areas(steps_count)
        calculator.calculate_volumes()
        
        # Расчет материалов
        if pool_type == 'liner':
            materials = calculator.calculate_materials_liner()
        else:
            materials = calculator.calculate_materials_ceramic(finish_type)
            
        # Формирование результата
        results = []
        for material, quantity in materials.items():
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
        calculator.calculate_dimensions(
            float(data['length']), 
            float(data['width']), 
            float(data['shallow_depth']), 
            float(data['deep_depth'])
        )
        calculator.calculate_areas(int(data['steps_count']))
        calculator.calculate_volumes()
        
        if data['pool_type'] == 'liner':
            materials = calculator.calculate_materials_liner()
        else:
            materials = calculator.calculate_materials_ceramic(data['finish_type'])
            
        # Создание Excel
        results = []
        total_sum = 0
        for material, quantity in materials.items():
            if material in materials_rates:
                rate = materials_rates[material]
                total = quantity * rate['price']
                total_sum += total
                results.append({
                    'Материал': rate['name'],
                    'Ед.изм.': rate['unit'],
                    'Количество': round(quantity, 2),
                    'Цена': rate['price'],
                    'Стоимость': round(total, 2)
                })
                
        df = pd.DataFrame(results)
        df.loc[len(df)] = ['ИТОГО:', '', '', '', round(total_sum, 2)]
        
        # Сохранение в буфер
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Расчет', index=False)
            worksheet = writer.sheets['Расчет']
            
            # Форматирование
            workbook = writer.book
            money_fmt = workbook.add_format({'num_format': '#,##0.00'})
            worksheet.set_column('A:A', 30)  # Материал
            worksheet.set_column('B:B', 10)  # Ед.изм.
            worksheet.set_column('C:C', 15)  # Количество
            worksheet.set_column('D:D', 15, money_fmt)  # Цена
            worksheet.set_column('E:E', 15, money_fmt)  # Стоимость
            
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'pool_calculation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
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
        calculator.calculate_dimensions(
            float(data['length']), 
            float(data['width']), 
            float(data['shallow_depth']), 
            float(data['deep_depth'])
        )
        calculator.calculate_areas(int(data['steps_count']))
        calculator.calculate_volumes()
        
        if data['pool_type'] == 'liner':
            materials = calculator.calculate_materials_liner()
        else:
            materials = calculator.calculate_materials_ceramic(data['finish_type'])
            
        # Создание PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Заголовок
        elements.append(Paragraph('Расчет стоимости бассейна', styles['Title']))
        elements.append(Paragraph(f'Дата: {datetime.now().strftime("%d.%m.%Y")}', styles['Normal']))
        
        # Параметры бассейна
        elements.append(Paragraph(
            f'Размеры: {data["length"]/1000:.1f}м x {data["width"]/1000:.1f}м\n'
            f'Глубина: {data["shallow_depth"]/1000:.1f}м - {data["deep_depth"]/1000:.1f}м\n'
            f'Тип бассейна: {"Керамогранит" if data["pool_type"] == "ceramic" else "ПВХ пленка"}\n'
            f'Количество ступеней: {data["steps_count"]}',
            styles['Normal']
        ))
        
        # Таблица материалов
        table_data = [['Материал', 'Ед.изм.', 'Кол-во', 'Цена', 'Стоимость']]
        total_sum = 0
        
        for material, quantity in materials.items():
            if material in materials_rates:
                rate = materials_rates[material]
                total = quantity * rate['price']
                total_sum += total
                table_data.append([
                    rate['name'],
                    rate['unit'],
                    f'{quantity:.2f}',
                    f'{rate["price"]:.2f}',
                    f'{total:.2f}'
                ])
                
        table_data.append(['ИТОГО:', '', '', '', f'{total_sum:.2f}'])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'pool_calculation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        app.logger.error(f'Ошибка при экспорте в PDF: {str(e)}')
        return jsonify({'error': 'Ошибка при экспорте в PDF'}), 500

if __name__ == '__main__':
    app.run(debug=True)
