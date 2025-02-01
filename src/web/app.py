import sys
import os
import io
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, render_template, request, jsonify, send_file
from src.utils.calculator import PoolCalculator
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Разрешаем доступ с любого хоста
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        # Преобразуем строковые значения в числовые
        params = {
            'length': int(data.get('length', 0)),
            'width': int(data.get('width', 0)),
            'depth': int(data.get('depth', 0)),
            'shape': data.get('shape', 'Прямоугольный'),
            'finish_type': data.get('finish_type', 'Плитка')
        }
        
        # Добавляем параметры L-образного бассейна если нужно
        if params['shape'] == 'L-образный':
            params.update({
                'l_length': int(data.get('l_length', 0)),
                'l_width': int(data.get('l_width', 0))
            })
            
        # Добавляем параметры ступеней
        stairs_data = data.get('stairs', [])
        params['stairs'] = [
            {
                'width': int(stair.get('width', 300)),
                'height': int(stair.get('height', 150))
            }
            for stair in stairs_data
        ]
        
        # Рассчитываем материалы
        calculator = PoolCalculator()
        materials = calculator.calculate_materials(params)
        
        return jsonify({
            'success': True,
            'materials': materials
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        calculator = PoolCalculator()
        materials = calculator.calculate_materials(data)
        
        # Создаем PDF в памяти
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        
        # Стили
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontName = 'Helvetica'
        title_style.fontSize = 16
        title_style.spaceAfter = 30
        
        # Добавляем заголовок
        elements.append(Paragraph("Расчет материалов для бассейна", title_style))
        
        # Информация о бассейне
        info_data = [
            ['Дата:', datetime.now().strftime('%d.%m.%Y')],
            ['Форма:', data['shape']],
            ['Размеры:', f"{data['length']}x{data['width']}x{data['depth']} мм"],
        ]
        
        # Создаем таблицу с информацией
        info_table = Table(info_data, colWidths=[100, 300])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Выравнивание меток по левому краю
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Выравнивание значений по левому краю
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Жирный шрифт для меток
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),  # Обычный шрифт для значений
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Создаем таблицу материалов
        table_data = [['Материал', 'Количество', 'Ед. изм.', 'Цена', 'Сумма']]
        total = 0
        
        for material in materials:
            sum_price = material['quantity'] * material['price']
            total += sum_price
            table_data.append([
                material['name'],
                f"{material['quantity']:.1f}",
                material['unit'],
                f"{material['price']:,.0f} ₽",
                f"{sum_price:,.0f} ₽"
            ])
        
        # Добавляем итоговую строку
        table_data.append(['Итого:', '', '', '', f"{total:,.0f} ₽"])
        
        # Создаем таблицу с правильными размерами колонок
        table = Table(table_data, colWidths=[200, 70, 50, 85, 95])
        table.setStyle(TableStyle([
            # Стиль заголовка
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Стиль данных
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Названия материалов по левому краю
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),   # Числа по правому краю
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            
            # Стиль итоговой строки
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F0F0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Сетка и границы
            ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
            ('BOX', (0, -1), (-1, -1), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Жирная линия под заголовком
            
            # Отступы
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        
        # Генерируем PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='расчет_бассейна.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/export/excel', methods=['POST'])
def export_excel():
    try:
        print("Starting Excel export...")
        data = request.get_json()
        calculator = PoolCalculator()
        materials = calculator.calculate_materials(data)
        print(f"Materials calculated: {materials}")
        
        # Создаем DataFrame
        df = pd.DataFrame(materials)
        print(f"DataFrame created with columns: {df.columns}")
        
        # Вычисляем сумму для каждого материала
        df['Сумма'] = df['quantity'] * df['price']
        print("Sum calculated")
        
        # Переименовываем колонки
        df = df.rename(columns={
            'name': 'Материал',
            'quantity': 'Количество',
            'unit': 'Ед. изм.',
            'price': 'Цена'
        })
        print(f"Columns renamed. New columns: {df.columns}")
        
        # Создаем Excel в памяти
        buffer = io.BytesIO()
        print("Created BytesIO buffer")
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            print("Created ExcelWriter")
            # Добавляем информацию о бассейне
            info_df = pd.DataFrame([
                ['Дата:', datetime.now().strftime('%d.%m.%Y')],
                ['Форма:', data['shape']],
                ['Размеры:', f"{data['length']}x{data['width']}x{data['depth']} мм"],
            ], columns=['', ''])
            print("Created info DataFrame")
            
            # Записываем информацию и материалы
            info_df.to_excel(writer, sheet_name='Расчет', index=False, header=False)
            print("Wrote info to Excel")
            df.to_excel(writer, sheet_name='Расчет', startrow=5, index=False)
            print("Wrote materials to Excel")
            
            # Получаем рабочий лист
            worksheet = writer.sheets['Расчет']
            workbook = writer.book
            print("Got worksheet and workbook")
            
            # Форматы
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D3D3D3',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            info_format = workbook.add_format({
                'bold': True,
                'align': 'left'
            })
            
            info_value_format = workbook.add_format({
                'align': 'left'
            })
            
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            number_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'num_format': '0.0',
                'valign': 'vcenter'
            })
            
            money_format = workbook.add_format({
                'border': 1,
                'align': 'right',
                'num_format': '#,##0 ₽',
                'valign': 'vcenter'
            })
            
            total_format = workbook.add_format({
                'bold': True,
                'border': 1,
                'align': 'right',
                'num_format': '#,##0 ₽',
                'bg_color': '#F0F0F0',
                'valign': 'vcenter'
            })
            print("Created all formats")
            
            # Форматируем информацию о бассейне
            for row in range(3):
                worksheet.write(row, 0, info_df.iloc[row, 0], info_format)
                worksheet.write(row, 1, info_df.iloc[row, 1], info_value_format)
            print("Formatted pool info")
            
            # Устанавливаем ширину колонок
            worksheet.set_column('A:A', 40)  # Материал
            worksheet.set_column('B:B', 15)  # Количество
            worksheet.set_column('C:C', 10)  # Ед. изм.
            worksheet.set_column('D:D', 15)  # Цена
            worksheet.set_column('E:E', 15)  # Сумма
            print("Set column widths")
            
            # Форматируем заголовки
            for col, header in enumerate(df.columns):
                worksheet.write(5, col, header, header_format)
            print("Formatted headers")
            
            # Форматируем данные
            for row in range(len(df)):
                worksheet.write(row + 6, 0, df.iloc[row]['Материал'], cell_format)
                worksheet.write_number(row + 6, 1, df.iloc[row]['Количество'], number_format)
                worksheet.write(row + 6, 2, df.iloc[row]['Ед. изм.'], cell_format)
                worksheet.write_number(row + 6, 3, df.iloc[row]['Цена'], money_format)
                worksheet.write_formula(row + 6, 4, f'=B{row+7}*D{row+7}', money_format)
            print("Formatted data rows")
            
            # Добавляем итоговую строку
            total_row = 6 + len(df)
            worksheet.write(total_row, 0, 'Итого:', total_format)
            worksheet.write_formula(total_row, 4, f'=SUM(E7:E{total_row})', total_format)
            print("Added total row")
            
            # Устанавливаем высоту строк
            worksheet.set_default_row(20)
            worksheet.set_row(5, 30)  # Заголовок повыше
            print("Set row heights")
            
            # Убираем сетку после данных
            worksheet.conditional_format(total_row + 1, 0, 1000, 4, {
                'type': 'no_blanks',
                'format': workbook.add_format({'border': 0})
            })
            print("Removed grid after data")
        
        print("Finished writing Excel")
        buffer.seek(0)
        print("Buffer seeked to 0")
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='расчет_бассейна.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Error in Excel export: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
