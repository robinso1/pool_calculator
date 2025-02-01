import json
import os
from datetime import datetime

class Project:
    def __init__(self):
        self.pool_params = None
        self.materials = []
        self.works = []
        self.modified_date = None
        
    def save(self, filename):
        """Сохранить проект в файл"""
        data = {
            'pool_params': self.pool_params,
            'materials': self.materials,
            'works': self.works,
            'modified_date': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filename):
        """Загрузить проект из файла"""
        project = cls()
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project.pool_params = data['pool_params']
        project.materials = data['materials']
        project.works = data['works']
        project.modified_date = datetime.fromisoformat(data['modified_date'])
        
        return project
    
    def update_prices(self, percentage):
        """Обновить все цены на указанный процент"""
        for material in self.materials:
            material['price'] *= (1 + percentage / 100)
            material['total'] = material['quantity'] * material['price']
        
        for work in self.works:
            work['price'] *= (1 + percentage / 100)
            work['total'] = work['quantity'] * work['price']
    
    def export_excel(self, filename):
        """Экспорт в Excel"""
        import pandas as pd
        
        # Создаем DataFrame для материалов
        materials_df = pd.DataFrame(self.materials)
        materials_df['total'] = materials_df['quantity'] * materials_df['price']
        
        # Создаем DataFrame для работ
        works_df = pd.DataFrame(self.works)
        works_df['total'] = works_df['quantity'] * works_df['price']
        
        # Создаем Excel writer
        with pd.ExcelWriter(filename) as writer:
            # Записываем параметры бассейна
            pd.DataFrame([self.pool_params]).to_excel(writer, sheet_name='Параметры', index=False)
            
            # Записываем материалы
            materials_df.to_excel(writer, sheet_name='Материалы', index=False)
            
            # Записываем работы
            works_df.to_excel(writer, sheet_name='Работы', index=False)
    
    def export_pdf(self, filename):
        """Экспорт в PDF"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Заголовок
        elements.append(Paragraph("Смета на строительство бассейна", styles['Heading1']))
        elements.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y')}", styles['Normal']))
        
        # Параметры бассейна
        elements.append(Paragraph("Параметры бассейна:", styles['Heading2']))
        params_data = [[k, str(v)] for k, v in self.pool_params.items()]
        params_table = Table(params_data)
        params_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(params_table)
        
        # Материалы
        elements.append(Paragraph("Материалы:", styles['Heading2']))
        materials_data = [['Наименование', 'Ед.изм.', 'Кол-во', 'Цена', 'Сумма']]
        for m in self.materials:
            materials_data.append([
                m['name'], m['unit'], str(m['quantity']),
                f"{m['price']:.2f}", f"{m['quantity'] * m['price']:.2f}"
            ])
        materials_table = Table(materials_data)
        materials_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(materials_table)
        
        # Работы
        elements.append(Paragraph("Работы:", styles['Heading2']))
        works_data = [['Наименование', 'Ед.изм.', 'Кол-во', 'Цена', 'Сумма']]
        for w in self.works:
            works_data.append([
                w['name'], w['unit'], str(w['quantity']),
                f"{w['price']:.2f}", f"{w['quantity'] * w['price']:.2f}"
            ])
        works_table = Table(works_data)
        works_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6)
        ]))
        elements.append(works_table)
        
        # Итоги
        total_materials = sum(m['quantity'] * m['price'] for m in self.materials)
        total_works = sum(w['quantity'] * w['price'] for w in self.works)
        elements.append(Paragraph(f"Итого материалы: {total_materials:.2f}", styles['Heading2']))
        elements.append(Paragraph(f"Итого работы: {total_works:.2f}", styles['Heading2']))
        elements.append(Paragraph(f"ВСЕГО: {(total_materials + total_works):.2f}", styles['Heading1']))
        
        # Строим документ
        doc.build(elements)
