import sys
from pathlib import Path
import hashlib
import math
import random

BASE_DIR = Path(__file__).resolve().parent.parent
TASK2_DIR = BASE_DIR / "Интеграция с БД и агрегация данных (SQL + Backend)"
sys.path.insert(0, str(TASK2_DIR))

TASK1_DIR = BASE_DIR / "Разработка ядра бизнес-логики (Расчет скидки)"
sys.path.insert(0, str(TASK1_DIR))

import tkinter as tk
from tkinter import messagebox
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

ICON_COLORS = [
    '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
    '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
    '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00',
    '#F4511E', '#6D4C41', '#546E7A',
]

ICON_SHAPES = ['circle', 'square', 'diamond', 'hexagon', 'triangle', 'rounded_square']

DEMO_QUANTITIES = [5_000, 0, 25_000, 75_000, 350_000, 150_000, 12_500, 500_000]

# Реальные данные для заполнения БД (включая телефон и рейтинг)
BASE_PARTNERS = [
    (1, 'ООО "Альфа"', 'alpha@example.com', '+7 (495) 123-45-67', 8.5),
    (2, 'ИП Петров', 'petrov@example.com', '+7 (916) 987-65-43', 7.2),
    (3, 'ООО "Бета"', 'beta@example.com', '+7 (812) 111-22-33', 9.1),
    (4, 'ООО "Гамма"', 'gamma@example.com', '+7 (903) 444-55-66', 6.8),
    (5, 'ИП Сидоров', 'sidorov@example.com', '+7 (999) 777-88-99', 8.0),
    (6, 'АО "Дельта"', 'delta@example.com', '+7 (495) 321-00-00', 9.5),
    (7, 'ООО "Эпсилон"', 'epsilon@example.com', '+7 (812) 654-32-10', 7.9),
    (8, 'ИП Козлов', 'kozlov@example.com', '+7 (916) 111-00-99', 8.8),
]

def hash_string(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def seed_test_data(db_path: str, stress_test: bool = False) -> None:
    """Очищает БД и заполняет её реальными структурированными данными."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DELETE FROM sales_history")
        cursor.execute("DELETE FROM partners")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='sales_history'")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        count = 100 if stress_test else len(BASE_PARTNERS)
        partners_to_insert = []
        sales_to_insert = []
        
        for i in range(1, count + 1):
            if stress_test:
                name = f'Компания {i}'
                email = f'company{i}@example.com'
                phone = f'+7 (999) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}'
                rating = round(random.uniform(5.0, 10.0), 1)
                qty = random.randint(0, 500_000)
            else:
                idx = (i - 1) % len(BASE_PARTNERS)
                name = BASE_PARTNERS[idx][1]
                email = BASE_PARTNERS[idx][2]
                phone = BASE_PARTNERS[idx][3]
                rating = BASE_PARTNERS[idx][4]
                qty = DEMO_QUANTITIES[idx]
            
            partners_to_insert.append((i, name, email, phone, rating))
            sales_to_insert.append((i, qty))
        
        cursor.executemany(
            "INSERT INTO partners (id, name, email, phone, rating) VALUES (?, ?, ?, ?, ?);",
            partners_to_insert
        )
        cursor.executemany(
            "INSERT INTO sales_history (partner_id, quantity) VALUES (?, ?);",
            sales_to_insert
        )
        conn.commit()
    finally:
        conn.close()

def get_all_partners(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM partners ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

class CompanyIcon(tk.Canvas):
    def __init__(self, parent, company_name: str, size: int = 40):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg=STYLE['bg_card'])
        
        h = hash_string(company_name)
        color = ICON_COLORS[h % len(ICON_COLORS)]
        shape = ICON_SHAPES[(h // len(ICON_COLORS)) % len(ICON_SHAPES)]
        letter = company_name[0].upper() if company_name else '?'
        bg_color = f'#{(h >> 8) & 0xFFFFFF:06X}' if (h % 3 == 0) else STYLE['bg_card']
        border_width = 2 + (h % 3)
        
        cx, cy = size // 2, size // 2
        r = size // 2 - border_width
        
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
        
        text_color = 'white' if self._is_dark(color) else color
        self.create_text(cx, cy, text=letter, fill=text_color,
                        font=('Segoe UI', size // 2, 'bold'))
    
    @staticmethod
    def _is_dark(hex_color: str) -> bool:
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 < 128

class PartnerCard(tk.Frame):
    def __init__(self, parent, partner_data):
        super().__init__(parent, bg=STYLE['border_color'], highlightthickness=1,
                        highlightbackground=STYLE['border_color'])
        
        inner = tk.Frame(self, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        
        content = tk.Frame(inner, bg=STYLE['bg_card'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        
        top_frame = tk.Frame(content, bg=STYLE['bg_card'])
        top_frame.pack(fill='x', pady=(0, 10))
        
        name_frame = tk.Frame(top_frame, bg=STYLE['bg_card'])
        name_frame.pack(side='left')
        
        company_name = partner_data.get('name', 'Неизвестно')
        icon = CompanyIcon(name_frame, company_name, size=36)
        icon.pack(side='left', padx=(0, 10))
        
        tk.Label(
            name_frame,
            text=f"{partner_data.get('type', 'Партнер')} | {company_name}",
            font=STYLE['font_card_title'],
            bg=STYLE['bg_card'],
            fg=STYLE['text_primary'],
            anchor='w'
        ).pack(side='left')
        
        discount = partner_data.get('discount_percent', 0) or 0
        tk.Label(
            top_frame,
            text=f"{discount}%",
            font=STYLE['font_discount'],
            bg=STYLE['bg_card'],
            fg=STYLE['text_primary']
        ).pack(side='right')
        
        info_frame = tk.Frame(content, bg=STYLE['bg_card'])
        info_frame.pack(fill='x', padx=46)
        
        # Берем РЕАЛЬНЫЕ данные из БД, а не сгенерированные
        phone = partner_data.get('phone', 'Не указан')
        rating = partner_data.get('rating', 0.0)
        total_qty = partner_data.get('total_quantity', 0)
        
        for text, color in [
            (partner_data.get('position', 'Партнер'), STYLE['text_secondary']),
            (phone, STYLE['text_primary']),
            (f"Рейтинг: {rating} | Куплено: {total_qty:,} ед.", STYLE['text_secondary']),
        ]:
            tk.Label(
                info_frame,
                text=text,
                font=STYLE['font_card_text'],
                bg=STYLE['bg_card'],
                fg=color,
                anchor='w'
            ).pack(fill='x', pady=(0, 4))

class PartnerApp(tk.Tk):
    def __init__(self, stress_test: bool = False):
        super().__init__()
        
        self.title("CRM: Список партнеров и скидок")
        self.geometry("1000x700")
        self.configure(bg=STYLE['bg_main'])
        
        self.stress_test = stress_test
        self._create_app_icon()
        self._create_widgets()
        
        try:
            self._load_partners()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
            self.destroy()
    
    def _create_app_icon(self):
        self._icon_image = tk.PhotoImage(width=32, height=32)
        for x in range(32):
            for y in range(32):
                self._icon_image.put('#4CAF50', (x, y))
        try:
            self.iconphoto(True, self._icon_image)
        except:
            pass
    
    def _create_widgets(self):
        header_frame = tk.Frame(self, bg=STYLE['bg_main'])
        header_frame.pack(fill='x', padx=30, pady=25)
        
        logo = tk.Canvas(header_frame, width=50, height=50,
                        highlightthickness=0, bg=STYLE['bg_main'])
        logo.create_rectangle(2, 2, 48, 48, fill='#4CAF50', outline='#2E7D32', width=2)
        logo.create_text(25, 25, text='CRM', fill='white', font=('Segoe UI', 14, 'bold'))
        logo.pack(side='left', padx=(0, 20))
        
        tk.Label(
            header_frame,
            text="Список партнеров и скидок",
            font=STYLE['font_title'],
            bg=STYLE['bg_main'],
            fg=STYLE['text_primary']
        ).pack(side='left', pady=15)
        
        self.canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg=STYLE['bg_main'])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))
        
        self.canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scrollbar.pack(side='right', fill='y', pady=(0, 30))
        
        self.outer_frame = tk.Frame(self.scrollable_frame, bg=STYLE['border_color'],
                                    highlightthickness=1, highlightbackground=STYLE['border_color'])
        self.outer_frame.pack(fill='x')
        
        self.cards_container = tk.Frame(self.outer_frame, bg=STYLE['bg_card'])
        self.cards_container.pack(fill='both', expand=True, padx=1, pady=1)
        
        self.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        if event.widget == self:
            width = self.canvas.winfo_width()
            if width > 0:
                self.canvas.itemconfig(self.canvas_window, width=width)
    
    def _load_partners(self):
        init_db(DB_PATH)
        seed_test_data(DB_PATH, stress_test=self.stress_test)
        
        partner_ids = get_all_partners(DB_PATH)
        
        if not partner_ids:
            tk.Label(
                self.cards_container,
                text="Нет данных о партнерах",
                font=('Segoe UI', 14),
                bg=STYLE['bg_card'],
                fg=STYLE['text_secondary']
            ).pack(pady=50)
            return
        
        loaded = 0
        for partner_id in partner_ids:
            try:
                data = get_partner_with_discount(DB_PATH, partner_id)
                if 'error' in data:
                    continue
                
                # Данные 'phone', 'rating' и 'total_quantity' уже пришли РЕАЛЬНЫМИ из БД
                data['type'] = 'Партнер'
                data['position'] = 'Партнер' # Заглушка, так как в БД нет должности, но UI её ожидает
                
                PartnerCard(self.cards_container, data).pack(fill='x', pady=15, padx=20)
                loaded += 1
            except Exception as e:
                print(f"Ошибка загрузки партнера {partner_id}: {e}")
        
        print(f"Загружено {loaded} из {len(partner_ids)} партнеров")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--stress':
        print("Запуск стресс-теста (100 партнеров)...")
        PartnerApp(stress_test=True).mainloop()
    else:
        print("Запуск демонстрационной версии...")
        PartnerApp().mainloop()