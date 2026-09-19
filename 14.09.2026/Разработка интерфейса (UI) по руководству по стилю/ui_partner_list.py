import sys
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).resolve().parent.parent
TASK2_DIR = BASE_DIR / "Интеграция с БД и агрегация данных (SQL + Backend)"
sys.path.insert(0, str(TASK2_DIR))

TASK1_DIR = BASE_DIR / "Разработка ядра бизнес-логики (Расчет скидки)"
sys.path.insert(0, str(TASK1_DIR))

import tkinter as tk
import os
import sqlite3
from partner_service import get_partner_with_discount, init_db, DB_PATH

STYLE = {
    'bg_main': '#FFFFFF',
    'bg_card': '#FFFFFF',
    'border_color': '#000000',
    'text_primary': '#000000',
    'text_secondary': '#666666',
    'font_title': ('Segoe UI', 16, 'bold'),
    'font_card_title': ('Segoe UI', 13, 'bold'),
    'font_card_text': ('Segoe UI', 11),
    'font_discount': ('Segoe UI', 14, 'bold'),
}

# Палитра для иконок
ICON_COLORS = [
    '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
    '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
    '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00',
    '#F4511E', '#6D4C41', '#546E7A',
]

# Формы иконок
ICON_SHAPES = ['circle', 'square', 'diamond', 'hexagon', 'triangle', 'rounded_square']


def hash_string(s: str) -> int:
    """Возвращает хэш строки."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


class CompanyIcon(tk.Canvas):
    """Уникальная иконка компании, генерируемая из названия."""
    
    def __init__(self, parent, company_name: str, size: int = 40):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg=STYLE['bg_card'])
        
        h = hash_string(company_name)
        
        # Уникальные параметры из хэша
        color = ICON_COLORS[h % len(ICON_COLORS)]
        shape = ICON_SHAPES[(h // len(ICON_COLORS)) % len(ICON_SHAPES)]
        letter = company_name[0].upper()
        bg_color = f'#{(h >> 8) & 0xFFFFFF:06X}' if (h % 3 == 0) else STYLE['bg_card']
        border_width = 2 + (h % 3)
        
        cx, cy = size // 2, size // 2
        r = size // 2 - border_width
        
        # Рисуем форму
        if shape == 'circle':
            self.create_oval(border_width, border_width, size - border_width, size - border_width,
                           fill=bg_color, outline=color, width=border_width)
        elif shape == 'square':
            self.create_rectangle(border_width, border_width, size - border_width, size - border_width,
                                fill=bg_color, outline=color, width=border_width)
        elif shape == 'diamond':
            self.create_polygon(cx, border_width, size - border_width, cy,
                              cx, size - border_width, border_width, cy,
                              fill=bg_color, outline=color, width=border_width)
        elif shape == 'hexagon':
            points = []
            for i in range(6):
                angle = 60 * i - 30
                x = cx + r * 0.866 * (1 if i % 2 == 0 else 0.5) * (1 if i < 3 else -1)
                # Упрощённый шестиугольник
                import math
                x = cx + r * math.cos(math.radians(angle))
                y = cy + r * math.sin(math.radians(angle))
                points.extend([x, y])
            self.create_polygon(*points, fill=bg_color, outline=color, width=border_width)
        elif shape == 'triangle':
            self.create_polygon(cx, border_width, size - border_width, size - border_width,
                              border_width, size - border_width,
                              fill=bg_color, outline=color, width=border_width)
        elif shape == 'rounded_square':
            m = border_width + 4
            self.create_rectangle(m, m, size - m, size - m,
                                fill=bg_color, outline=color, width=border_width)
        
        # Рисуем букву контрастным цветом
        text_color = 'white' if self._is_dark(color) else color
        self.create_text(cx, cy, text=letter, fill=text_color,
                        font=('Segoe UI', size // 2, 'bold'))
    
    @staticmethod
    def _is_dark(hex_color: str) -> bool:
        """Проверяет, тёмный ли цвет."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 < 128


def seed_test_data(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM partners")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO partners (id, name, email) VALUES (?, ?, ?);",
                [
                    (1, 'ООО "Альфа"', 'alpha@example.com'),
                    (2, 'ИП Петров', 'petrov@example.com'),
                    (3, 'ООО "Бета"', 'beta@example.com'),
                ],
            )
            cursor.executemany(
                "INSERT INTO sales_history (partner_id, quantity) VALUES (?, ?);",
                [
                    (1, 100_000),
                    (2, 75_000),
                    (3, 200_000),
                ],
            )
            conn.commit()
    finally:
        conn.close()


class PartnerCard(tk.Frame):
    """Карточка партнера со своей рамкой."""
    
    def __init__(self, parent, partner_data):
        super().__init__(parent, bg=STYLE['border_color'], highlightthickness=1,
                        highlightbackground=STYLE['border_color'])
        
        inner = tk.Frame(self, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        
        content = tk.Frame(inner, bg=STYLE['bg_card'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Верхняя строка
        top_frame = tk.Frame(content, bg=STYLE['bg_card'])
        top_frame.pack(fill='x', pady=(0, 10))
        
        name_frame = tk.Frame(top_frame, bg=STYLE['bg_card'])
        name_frame.pack(side='left')
        
        company_name = partner_data['name']
        icon = CompanyIcon(name_frame, company_name, size=36)
        icon.pack(side='left', padx=(0, 10))
        
        title_label = tk.Label(
            name_frame,
            text=f"{partner_data.get('type', 'Тип')} | {company_name}",
            font=STYLE['font_card_title'],
            bg=STYLE['bg_card'],
            fg=STYLE['text_primary'],
            anchor='w'
        )
        title_label.pack(side='left')
        
        discount_label = tk.Label(
            top_frame,
            text=f"{partner_data['discount_percent']}%",
            font=STYLE['font_discount'],
            bg=STYLE['bg_card'],
            fg=STYLE['text_primary']
        )
        discount_label.pack(side='right')
        
        # Информация
        info_frame = tk.Frame(content, bg=STYLE['bg_card'])
        info_frame.pack(fill='x', padx=46)
        
        for text, color in [
            (partner_data.get('position', ''), STYLE['text_secondary']),
            (partner_data.get('phone', ''), STYLE['text_primary']),
            (f"Рейтинг: {partner_data.get('rating', 0)}", STYLE['text_secondary']),
        ]:
            lbl = tk.Label(
                info_frame,
                text=text,
                font=STYLE['font_card_text'],
                bg=STYLE['bg_card'],
                fg=color,
                anchor='w'
            )
            lbl.pack(fill='x', pady=(0, 4))


class PartnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("CRM: Список партнеров и скидок")
        self.geometry("1000x700")
        self.configure(bg=STYLE['bg_main'])
        
        self._create_app_icon()
        self._create_widgets()
        self._load_partners()
    
    def _create_app_icon(self):
        """Иконка приложения."""
        self._icon_image = tk.PhotoImage(width=32, height=32)
        for x in range(32):
            for y in range(32):
                self._icon_image.put('#4CAF50', (x, y))
        try:
            self.iconphoto(True, self._icon_image)
        except:
            pass
    
    def _create_widgets(self):
        # Шапка
        header_frame = tk.Frame(self, bg=STYLE['bg_main'])
        header_frame.pack(fill='x', padx=30, pady=25)
        
        # Логотип компании
        logo_canvas = tk.Canvas(header_frame, width=50, height=50,
                               highlightthickness=0, bg=STYLE['bg_main'])
        logo_canvas.create_rectangle(2, 2, 48, 48, fill='#4CAF50', outline='#2E7D32', width=2)
        logo_canvas.create_text(25, 25, text='CRM', fill='white',
                               font=('Segoe UI', 14, 'bold'))
        logo_canvas.pack(side='left', padx=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="Список партнеров и скидок",
            font=STYLE['font_title'],
            bg=STYLE['bg_main'],
            fg=STYLE['text_primary']
        )
        title_label.pack(side='left', pady=15)
        
        # Скролл на уровне окна
        self.canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=STYLE['bg_main'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scrollbar.pack(side='right', fill='y', pady=(0, 30))
        
        # Внешний контейнер с рамкой (внутри scrollable_frame)
        self.outer_frame = tk.Frame(self.scrollable_frame, bg=STYLE['border_color'],
                                    highlightthickness=1, highlightbackground=STYLE['border_color'])
        self.outer_frame.pack(fill='x', padx=0, pady=0)
        
        self.cards_container = tk.Frame(self.outer_frame, bg=STYLE['bg_card'])
        self.cards_container.pack(fill='both', expand=True, padx=1, pady=1)
        
        self.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        if event.widget == self:
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 0:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _load_partners(self):
        init_db(DB_PATH)
        seed_test_data(DB_PATH)
        
        partner_ids = [1, 2, 3]
        
        for partner_id in partner_ids:
            partner_data = get_partner_with_discount(DB_PATH, partner_id)
            
            if 'error' not in partner_data:
                partner_data['type'] = 'Партнер'
                partner_data['position'] = 'Директор'
                partner_data['phone'] = '+7 223 322 22 32'
                partner_data['rating'] = 10
                
                card = PartnerCard(self.cards_container, partner_data)
                card.pack(fill='x', pady=15, padx=20)


if __name__ == "__main__":
    app = PartnerApp()
    app.mainloop()