import sys
from pathlib import Path
import hashlib
import math
import random
import sqlite3
import logging
from datetime import datetime, timedelta

# ==========================================
# НАСТРОЙКА ПУТЕЙ (28.09.2026)
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
STAGE2_DIR = REPO_ROOT / "14.09.2026" / "Интеграция с БД и агрегация данных (SQL + Backend)"
STAGE1_DIR = REPO_ROOT / "14.09.2026" / "Разработка ядра бизнес-логики (Расчет скидки)"
MATERIAL_DIR = REPO_ROOT / "28.09.2026" / "Разработка ядра алгоритма расчета материалов"

sys.path.insert(0, str(STAGE1_DIR))
sys.path.insert(0, str(STAGE2_DIR))
sys.path.insert(0, str(MATERIAL_DIR))

import tkinter as tk
from tkinter import ttk, messagebox
from partner_service import get_partner_with_discount, init_db, DB_PATH
from f4_2_material_calculator import (
    calculate_material_required,
    ensure_materials_tables,
    seed_materials_data,
)

# ==========================================
# ЛОГИРОВАНИЕ (Аудит безопасности и ошибок)
# ==========================================
LOG_FILE = "app.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CRM_App")

# ==========================================
# СТИЛИ И КОНСТАНТЫ
# ==========================================
STYLE = {
    'bg_main': '#FFFFFF', 'bg_card': '#FFFFFF', 'border_color': '#000000',
    'text_primary': '#000000', 'text_secondary': '#666666',
    'bg_result_success': '#E8F5E9', 'bg_result_error': '#FFEBEE',
    'text_success': '#2E7D32', 'text_error': '#C62828',
    'font_title': ('Segoe UI', 16, 'bold'), 'font_card_title': ('Segoe UI', 13, 'bold'),
    'font_card_text': ('Segoe UI', 11), 'font_discount': ('Segoe UI', 14, 'bold'),
    'font_label': ('Segoe UI', 11), 'font_entry': ('Segoe UI', 11),
    'font_btn': ('Segoe UI', 11, 'bold'), 'font_result_number': ('Segoe UI', 28, 'bold'),
}

ICON_COLORS = ['#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB', '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047', '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00', '#F4511E', '#6D4C41', '#546E7A']
ICON_SHAPES = ['circle', 'square', 'diamond', 'hexagon', 'triangle', 'rounded_square']
PARTNER_TYPES = ["ООО", "ЗАО", "АО", "ПАО", "ОАО", "ИП"]
DEMO_QUANTITIES = [5_000, 0, 25_000, 75_000, 350_000, 150_000, 12_500, 500_000]
DEMO_PRODUCTS = [(1, 'Стиральный порошок "Альфа"', 500.00), (2, 'Мыло жидкое "Стандарт"', 90.00), (3, 'Кондиционер для белья', 350.00), (4, 'Шампунь "Премиум"', 280.00), (5, 'Гель для душа "Свежесть"', 180.00)]
BASE_PARTNERS = [
    (1, 'ООО "Альфа"', 'alpha@example.com', '+7 (495) 123-45-67', 8.5, 'ООО', 'г. Москва, ул. Ленина, 1', 'Иванов И.И.'),
    (2, 'ИП Петров', 'petrov@example.com', '+7 (916) 987-65-43', 7.2, 'ИП', 'г. Санкт-Петербург, пр. Невский, 10', 'Петров П.П.'),
    (3, 'ООО "Бета"', 'beta@example.com', '+7 (812) 111-22-33', 9.1, 'ООО', 'г. Казань, ул. Баумана, 5', 'Сидоров С.С.'),
    (4, 'ООО "Гамма"', 'gamma@example.com', '+7 (903) 444-55-66', 6.8, 'ЗАО', 'г. Новосибирск, ул. Красный пр., 20', 'Козлов К.К.'),
    (5, 'ИП Сидоров', 'sidorov@example.com', '+7 (999) 777-88-99', 8.0, 'ИП', 'г. Екатеринбург, ул. Малышева, 15', 'Сидоров А.В.'),
    (6, 'АО "Дельта"', 'delta@example.com', '+7 (495) 321-00-00', 9.5, 'АО', 'г. Москва, ул. Тверская, 8', 'Морозов М.М.'),
    (7, 'ООО "Эпсилон"', 'epsilon@example.com', '+7 (812) 654-32-10', 7.9, 'ООО', 'г. Самара, ул. Куйбышева, 3', 'Волков В.В.'),
    (8, 'ИП Козлов', 'kozlov@example.com', '+7 (916) 111-00-99', 8.8, 'ИП', 'г. Ростов-на-Дону, ул. Большая, 7', 'Козлов Д.Д.'),
]

# ==========================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ БД
# ==========================================
def hash_string(s: str) -> int: return int(hashlib.md5(s.encode()).hexdigest(), 16)

def extend_db_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit_price REAL NOT NULL DEFAULT 0)")
        cursor.execute("PRAGMA table_info(sales_history)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if 'product_id' not in existing_cols: cursor.execute("ALTER TABLE sales_history ADD COLUMN product_id INTEGER DEFAULT 1")
        if 'sale_date' not in existing_cols: cursor.execute("ALTER TABLE sales_history ADD COLUMN sale_date TEXT DEFAULT '2026-01-01'")
        cursor.execute("PRAGMA table_info(partners)")
        partner_cols = {row[1] for row in cursor.fetchall()}
        for col, col_type, default in [('partner_type', 'TEXT', "'ООО'"), ('address', 'TEXT', "''"), ('director_name', 'TEXT', "''")]:
            if col not in partner_cols: cursor.execute(f"ALTER TABLE partners ADD COLUMN {col} {col_type} DEFAULT {default}")
        conn.commit()
    finally: conn.close()

def is_db_empty(db_path: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM partners")
        return cursor.fetchone()[0] == 0
    except sqlite3.OperationalError: return True
    finally: conn.close()

def seed_test_data(db_path: str, stress_test: bool = False) -> None:
    if not is_db_empty(db_path) and not stress_test: return
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DELETE FROM sales_history")
        cursor.execute("DELETE FROM partners")
        cursor.execute("DELETE FROM products")
        try: cursor.execute("DELETE FROM sqlite_sequence WHERE name='sales_history'")
        except sqlite3.OperationalError: pass
        cursor.execute("PRAGMA foreign_keys = ON")
        for pid, name, price in DEMO_PRODUCTS: cursor.execute("INSERT INTO products (id, name, unit_price) VALUES (?, ?, ?)", (pid, name, price))
        count = 100 if stress_test else len(BASE_PARTNERS)
        base_date = datetime(2026, 1, 1)
        for i in range(1, count + 1):
            if stress_test:
                name, email, phone, rating, ptype, address, director = f'Компания {i}', f'company{i}@example.com', f'+7 (999) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}', round(random.uniform(5.0, 10.0), 1), random.choice(PARTNER_TYPES), f'г. Город, ул. Улица, {i}', f'Директор {i}'
                qty, product_id, sale_date = random.randint(100, 500_000), random.randint(1, len(DEMO_PRODUCTS)), (base_date + timedelta(days=random.randint(0, 270))).strftime('%Y-%m-%d')
            else:
                idx = (i - 1) % len(BASE_PARTNERS)
                bp = BASE_PARTNERS[idx]
                name, email, phone, rating, ptype, address, director = bp[1], bp[2], bp[3], bp[4], bp[5], bp[6], bp[7]
                qty, product_id, sale_date = DEMO_QUANTITIES[idx], (i % len(DEMO_PRODUCTS)) + 1, (base_date + timedelta(days=idx * 30)).strftime('%Y-%m-%d')
            cursor.execute("INSERT INTO partners (id, name, email, phone, rating, partner_type, address, director_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", (i, name, email, phone, rating, ptype, address, director))
            cursor.execute("INSERT INTO sales_history (partner_id, quantity, product_id, sale_date) VALUES (?, ?, ?, ?);", (i, qty, product_id, sale_date))
        conn.commit()
    finally: conn.close()

def get_all_partners(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM partners ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    finally: conn.close()

def get_partner_sales_history(db_path: str, partner_id: int) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(p.name, 'Товар не указан') AS product_name, s.quantity, strftime('%d.%m.%Y', s.sale_date) AS sale_date FROM sales_history s LEFT JOIN products p ON s.product_id = p.id WHERE s.partner_id = ? ORDER BY s.sale_date DESC, s.id DESC", (partner_id,))
        return cursor.fetchall()
    finally: conn.close()

def get_partner_name(db_path: str, partner_id: int) -> str:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM partners WHERE id=?", (partner_id,))
        row = cursor.fetchone()
        return row[0] if row else "Неизвестный партнер"
    finally: conn.close()

def get_all_product_types(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM product_types ORDER BY id")
        return cursor.fetchall()
    except sqlite3.OperationalError: return []
    finally: conn.close()

def get_all_material_types(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM material_types ORDER BY id")
        return cursor.fetchall()
    except sqlite3.OperationalError: return []
    finally: conn.close()

def save_partner(db_path: str, partner_data: dict) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        pid = partner_data.get('id')
        if pid:
            cursor.execute("UPDATE partners SET name=?, email=?, phone=?, rating=?, partner_type=?, address=?, director_name=? WHERE id=?", (partner_data['name'], partner_data['email'], partner_data['phone'], partner_data['rating'], partner_data['partner_type'], partner_data['address'], partner_data['director_name'], pid))
        else:
            cursor.execute("INSERT INTO partners (name, email, phone, rating, partner_type, address, director_name) VALUES (?, ?, ?, ?, ?, ?, ?)", (partner_data['name'], partner_data['email'], partner_data['phone'], partner_data['rating'], partner_data['partner_type'], partner_data['address'], partner_data['director_name']))
            new_id = cursor.lastrowid
            cursor.execute("INSERT INTO sales_history (partner_id, quantity, product_id, sale_date) VALUES (?, 0, 1, ?);", (new_id, datetime.now().strftime('%Y-%m-%d')))
        conn.commit()
    finally: conn.close()

# ==========================================
# UI КОМПОНЕНТЫ
# ==========================================
class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder: str, **kwargs):
        super().__init__(parent, **kwargs)
        self._placeholder = placeholder
        self._placeholder_active = False
        self._normal_fg = kwargs.get('fg', STYLE['text_primary'])
        self._placeholder_fg = '#AAAAAA'
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.config(highlightthickness=1, highlightbackground='#DDDDDD', highlightcolor='#4CAF50', insertbackground=STYLE['text_primary'])
        self._show_placeholder()
    def _show_placeholder(self):
        if not self.get():
            self._placeholder_active = True
            self.config(fg=self._placeholder_fg)
            self.insert(0, self._placeholder)
    def _on_focus_in(self, _event):
        self.config(highlightbackground='#4CAF50', highlightthickness=2)
        if self._placeholder_active:
            self.delete(0, tk.END)
            self.config(fg=self._normal_fg)
            self._placeholder_active = False
    def _on_focus_out(self, _event):
        self.config(highlightbackground='#DDDDDD', highlightthickness=1)
        if not self.get(): self._show_placeholder()
    def get_value(self) -> str: return '' if self._placeholder_active else self.get()

class CompanyIcon(tk.Canvas):
    def __init__(self, parent, company_name: str, size: int = 40):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg=STYLE['bg_card'])
        h = hash_string(company_name)
        color = ICON_COLORS[h % len(ICON_COLORS)]
        shape = ICON_SHAPES[(h // len(ICON_COLORS)) % len(ICON_SHAPES)]
        letter = company_name[0].upper() if company_name else '?'
        bg_color = f'#{(h >> 8) & 0xFFFFFF:06X}' if (h % 3 == 0) else STYLE['bg_card']
        bw = 2 + (h % 3)
        cx, cy = size // 2, size // 2
        r = size // 2 - bw
        if shape == 'circle': self.create_oval(bw, bw, size-bw, size-bw, fill=bg_color, outline=color, width=bw)
        elif shape == 'square': self.create_rectangle(bw, bw, size-bw, size-bw, fill=bg_color, outline=color, width=bw)
        elif shape == 'diamond': self.create_polygon(cx, bw, size-bw, cy, cx, size-bw, bw, cy, fill=bg_color, outline=color, width=bw)
        elif shape == 'hexagon':
            pts = []
            for i in range(6):
                a = 60 * i - 30
                pts.extend([cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))])
            self.create_polygon(*pts, fill=bg_color, outline=color, width=bw)
        elif shape == 'triangle': self.create_polygon(cx, bw, size-bw, size-bw, bw, size-bw, fill=bg_color, outline=color, width=bw)
        elif shape == 'rounded_square':
            m = bw + 4
            self.create_rectangle(m, m, size-m, size-m, fill=bg_color, outline=color, width=bw)
        text_color = 'white' if self._is_dark(color) else color
        self.create_text(cx, cy, text=letter, fill=text_color, font=('Segoe UI', size // 2, 'bold'))
    @staticmethod
    def _is_dark(hex_color: str) -> bool:
        c = hex_color.lstrip('#')
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return (r * 299 + g * 587 + b * 114) / 1000 < 128

class PartnerCard(tk.Frame):
    def __init__(self, parent, partner_data, on_edit_callback, on_history_callback):
        super().__init__(parent, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        self.partner_id = partner_data.get('id')
        self.on_edit_callback = on_edit_callback
        self.on_history_callback = on_history_callback
        inner = tk.Frame(self, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        content = tk.Frame(inner, bg=STYLE['bg_card'])
        content.pack(fill='both', expand=True, padx=20, pady=15)
        top_frame = tk.Frame(content, bg=STYLE['bg_card'])
        top_frame.pack(fill='x', pady=(0, 10))
        name_frame = tk.Frame(top_frame, bg=STYLE['bg_card'])
        name_frame.pack(side='left')
        company_name = partner_data.get('name', 'Неизвестно')
        CompanyIcon(name_frame, company_name, size=36).pack(side='left', padx=(0, 10))
        tk.Label(name_frame, text=f"{partner_data.get('type', 'Партнер')} | {company_name}", font=STYLE['font_card_title'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], anchor='w').pack(side='left')
        discount = partner_data.get('discount_percent', 0) or 0
        tk.Label(top_frame, text=f"{discount}%", font=STYLE['font_discount'], bg=STYLE['bg_card'], fg=STYLE['text_primary']).pack(side='right')
        info_frame = tk.Frame(content, bg=STYLE['bg_card'])
        info_frame.pack(fill='x', padx=46)
        for text, color in [(partner_data.get('position', 'Партнер'), STYLE['text_secondary']), (partner_data.get('phone', 'Не указан'), STYLE['text_primary']), (f"Рейтинг: {partner_data.get('rating', 0.0)} | Куплено: {partner_data.get('total_quantity', 0):,} ед.", STYLE['text_secondary'])]:
            tk.Label(info_frame, text=text, font=STYLE['font_card_text'], bg=STYLE['bg_card'], fg=color, anchor='w').pack(fill='x', pady=(0, 4))
        bottom_frame = tk.Frame(content, bg=STYLE['bg_card'])
        bottom_frame.pack(fill='x', pady=(10, 0))
        tk.Label(bottom_frame, text="💡 Дважды кликните для редактирования", font=('Segoe UI', 9, 'italic'), bg=STYLE['bg_card'], fg='#999999').pack(side='left')
        btn_history = tk.Button(bottom_frame, text="📊 История продаж", font=('Segoe UI', 10), bg='#1E88E5', fg='white', relief='flat', padx=12, pady=5, cursor='hand2', command=self._on_history_click)
        btn_history.pack(side='right')
        btn_history.bind("<Double-Button-1>", lambda e: "break")
        self._bind_recursive(self)
        self.config(cursor='hand2')
    def _on_history_click(self):
        if self.on_history_callback: self.on_history_callback(self.partner_id)
    def _bind_recursive(self, widget):
        widget.bind("<Double-Button-1>", self._on_double_click)
        try: widget.config(cursor='hand2')
        except tk.TclError: pass
        for child in widget.winfo_children():
            if isinstance(child, tk.Button): continue
            self._bind_recursive(child)
    def _on_double_click(self, event):
        if self.on_edit_callback: self.on_edit_callback(self.partner_id)

# ==========================================
# СТРАНИЦЫ (ОКНА)
# ==========================================
class MainWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=STYLE['bg_main'])
        self.controller = controller
        self._create_header()
        self._create_content_area()
    def _create_header(self):
        hf = tk.Frame(self, bg=STYLE['bg_main'])
        hf.pack(fill='x', padx=30, pady=25)
        logo = tk.Canvas(hf, width=50, height=50, highlightthickness=0, bg=STYLE['bg_main'])
        logo.create_rectangle(2, 2, 48, 48, fill='#4CAF50', outline='#2E7D32', width=2)
        logo.create_text(25, 25, text='CRM', fill='white', font=('Segoe UI', 14, 'bold'))
        logo.pack(side='left', padx=(0, 20))
        tk.Label(hf, text="Список партнеров и скидок", font=STYLE['font_title'], bg=STYLE['bg_main'], fg=STYLE['text_primary']).pack(side='left', pady=15)
        tk.Button(hf, text="🧮 Калькулятор материалов", font=STYLE['font_btn'], bg='#FF9800', fg='white', relief='flat', padx=15, pady=8, cursor='hand2', command=lambda: self.controller.show_frame("MaterialCalculatorWindow")).pack(side='right', padx=(10, 0))
        tk.Button(hf, text="➕ Добавить партнера", font=STYLE['font_btn'], bg='#4CAF50', fg='white', relief='flat', padx=15, pady=8, cursor='hand2', command=lambda: self.controller.show_frame("PartnerEditWindow", partner_id=None)).pack(side='right')
    def _create_content_area(self):
        self.canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=STYLE['bg_main'])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scrollbar.pack(side='right', fill='y', pady=(0, 30))
        self.outer_frame = tk.Frame(self.scrollable_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        self.outer_frame.pack(fill='x')
        self.cards_container = tk.Frame(self.outer_frame, bg=STYLE['bg_card'])
        self.cards_container.pack(fill='both', expand=True, padx=1, pady=1)
        self.canvas.bind('<Configure>', self._on_resize)
    def _on_resize(self, event):
        w = self.canvas.winfo_width()
        if w > 0: self.canvas.itemconfig(self.canvas_window, width=w)
    def refresh_data(self):
        for w in self.cards_container.winfo_children(): w.destroy()
        try:
            init_db(DB_PATH)
            extend_db_schema(DB_PATH)
            ensure_materials_tables(DB_PATH)
            seed_materials_data(DB_PATH)
            seed_test_data(DB_PATH)
            ids = get_all_partners(DB_PATH)
        except sqlite3.Error as e:
            logger.error(f"DB error in MainWindow refresh: {e}")
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить данные:\n{e}")
            return
        if not ids:
            tk.Label(self.cards_container, text="Нет данных о партнерах", font=('Segoe UI', 14), bg=STYLE['bg_card'], fg=STYLE['text_secondary']).pack(pady=50)
            return
        for pid in ids:
            try:
                data = get_partner_with_discount(DB_PATH, pid)
                if 'error' in data: continue
                data['type'] = 'Партнер'
                data['position'] = 'Партнер'
                PartnerCard(self.cards_container, data, self._on_partner_edit, self._on_partner_history).pack(fill='x', pady=15, padx=20)
            except Exception as e:
                logger.error(f"Error loading partner {pid}: {e}")
    def _on_partner_edit(self, partner_id: int): self.controller.show_frame("PartnerEditWindow", partner_id=partner_id)
    def _on_partner_history(self, partner_id: int): self.controller.show_frame("PartnerHistoryWindow", partner_id=partner_id)

class PartnerEditWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=STYLE['bg_main'])
        self.controller = controller
        self._editing_id = None
        self._initial_state = {}
        self._create_header()
        self._create_form()
    def _create_header(self):
        hf = tk.Frame(self, bg=STYLE['bg_main'])
        hf.pack(fill='x', padx=30, pady=25)
        tk.Button(hf, text="← Назад", font=STYLE['font_btn'], bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=15, pady=8, cursor='hand2', command=self._on_cancel).pack(side='left')
        self._header_label = tk.Label(hf, text="Новый партнер", font=STYLE['font_title'], bg=STYLE['bg_main'], fg=STYLE['text_primary'])
        self._header_label.pack(side='left', padx=20)
    def _create_form(self):
        self.scroll_canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scroll_sb = tk.Scrollbar(self, orient='vertical', command=self.scroll_canvas.yview)
        scroll_frame = tk.Frame(self.scroll_canvas, bg=STYLE['bg_main'])
        scroll_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        self.scroll_canvas_window = self.scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        self.scroll_canvas.configure(yscrollcommand=scroll_sb.set)
        self.scroll_canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scroll_sb.pack(side='right', fill='y', pady=(0, 30))
        self.scroll_canvas.bind('<Configure>', self._on_resize)
        outer = tk.Frame(scroll_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        outer.pack(fill='x', pady=10)
        inner = tk.Frame(outer, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        form = tk.Frame(inner, bg=STYLE['bg_card'])
        form.pack(fill='x', padx=40, pady=30)
        self._fields = {}
        self._add_field(form, "Наименование *", "name", placeholder='Например: ООО "Ромашка"')
        
        # Прямое создание ComboBox (без _add_combobox)
        row = tk.Frame(form, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text="Тип партнера *", font=STYLE['font_label'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=20, anchor='w').pack(side='left')
        self._type_var = tk.StringVar(value="ООО")
        type_cb = ttk.Combobox(row, textvariable=self._type_var, values=PARTNER_TYPES, state='readonly', font=STYLE['font_entry'], width=30)
        type_cb.pack(side='left')
        self._fields['partner_type'] = type_cb
        
        self._add_field(form, "Рейтинг *", "rating", placeholder='Целое число от 0 до 10')
        self._add_field(form, "Адрес", "address", placeholder='г. Москва, ул. Примерная, д. 1')
        self._add_field(form, "ФИО директора", "director_name", placeholder='Иванов Иван Иванович')
        self._add_field(form, "Телефон", "phone", placeholder='+7 (XXX) XXX-XX-XX')
        self._add_field(form, "Email *", "email", placeholder='example@company.ru')
        btn_frame = tk.Frame(form, bg=STYLE['bg_card'])
        btn_frame.pack(fill='x', pady=(25, 0))
        tk.Button(btn_frame, text="💾 Сохранить", font=STYLE['font_btn'], bg='#4CAF50', fg='white', relief='flat', padx=25, pady=10, cursor='hand2', command=self._on_save).pack(side='left', padx=(0, 15))
        tk.Button(btn_frame, text="Отмена", font=STYLE['font_btn'], bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=25, pady=10, cursor='hand2', command=self._on_cancel).pack(side='left')
    def _on_resize(self, event):
        w = self.scroll_canvas.winfo_width()
        if w > 0: self.scroll_canvas.itemconfig(self.scroll_canvas_window, width=w)
    def _add_field(self, parent, label_text: str, key: str, placeholder: str = ''):
        row = tk.Frame(parent, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text=label_text, font=STYLE['font_label'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=20, anchor='w').pack(side='left')
        entry = PlaceholderEntry(row, placeholder=placeholder, font=STYLE['font_entry'], width=35, fg=STYLE['text_primary'], bg='#FAFAFA', relief='solid', bd=1)
        entry.pack(side='left')
        self._fields[key] = entry
    def _get_current_state(self) -> dict:
        state = {}
        for key, widget in self._fields.items():
            if key == 'partner_type': state[key] = widget.get()
            else: state[key] = widget.get_value()
        return state
    def _has_changes(self) -> bool: return self._get_current_state() != self._initial_state
    def _on_cancel(self):
        if self._has_changes():
            result = messagebox.askyesno("Подтверждение выхода", "Вы изменили данные, но не сохранили их.\n\nВсе несохранённые изменения будут потеряны.\nВы уверены, что хотите вернуться назад?", icon='warning')
            if not result: return
        self.controller.show_frame("MainWindow")
    def reset_form(self, partner_id: int = None):
        self._editing_id = partner_id
        self._header_label.config(text="Редактирование партнера" if partner_id else "Новый партнер")
        for key, widget in self._fields.items():
            if key == 'partner_type': widget.set("ООО")
            else:
                widget.delete(0, tk.END)
                widget._show_placeholder()
        if partner_id:
            conn = sqlite3.connect(DB_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name, email, phone, rating, partner_type, address, director_name FROM partners WHERE id=?", (partner_id,))
                row = cursor.fetchone()
            finally: conn.close()
            if row:
                self._set_field('name', row[0])
                self._set_field('email', row[1])
                self._set_field('phone', row[2])
                self._set_field('rating', str(row[3]) if row[3] is not None else '')
                self._fields['partner_type'].set(row[4] if row[4] else 'ООО')
                self._set_field('address', row[5])
                self._set_field('director_name', row[6])
        self._initial_state = self._get_current_state()
    def _set_field(self, key: str, value: str):
        w = self._fields[key]
        w.delete(0, tk.END)
        w.config(fg=STYLE['text_primary'])
        w._placeholder_active = False
        w.insert(0, value or '')
    def _on_save(self):
        name = self._fields['name'].get_value().strip()
        email = self._fields['email'].get_value().strip()
        phone = self._fields['phone'].get_value().strip()
        rating_str = self._fields['rating'].get_value().strip()
        partner_type = self._fields['partner_type'].get()
        address = self._fields['address'].get_value().strip()
        director = self._fields['director_name'].get_value().strip()
        if not name:
            messagebox.showerror("Ошибка валидации", "Поле 'Наименование' обязательно для заполнения.")
            self._fields['name'].focus_set()
            return
        if not email:
            messagebox.showerror("Ошибка валидации", "Поле 'Email' обязательно для заполнения.")
            self._fields['email'].focus_set()
            return
        try:
            rating = int(rating_str) if rating_str else 0
            if rating < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка валидации", "Рейтинг должен быть целым неотрицательным числом.")
            self._fields['rating'].focus_set()
            return
        try:
            save_partner(DB_PATH, {'id': self._editing_id, 'name': name, 'email': email, 'phone': phone, 'rating': rating, 'partner_type': partner_type, 'address': address, 'director_name': director})
            logger.info(f"Partner saved successfully: ID={self._editing_id}, Name={name}")
        except sqlite3.Error as e:
            logger.error(f"Database error during save: {e}")
            messagebox.showerror("Ошибка базы данных", f"Не удалось сохранить данные:\n{e}")
            return
        except Exception as e:
            logger.error(f"Unexpected error during save: {e}")
            messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка:\n{e}")
            return
        mode = "обновлён" if self._editing_id else "добавлен"
        messagebox.showinfo("Операция выполнена успешно", f"Партнер '{name}' успешно {mode}.")
        self.controller.show_frame("MainWindow")

class PartnerHistoryWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=STYLE['bg_main'])
        self.controller = controller
        self._partner_id = None
        self._partner_name = ""
        self._create_header()
        self._create_content()
    def _create_header(self):
        hf = tk.Frame(self, bg=STYLE['bg_main'])
        hf.pack(fill='x', padx=30, pady=25)
        logo = tk.Canvas(hf, width=50, height=50, highlightthickness=0, bg=STYLE['bg_main'])
        logo.create_rectangle(2, 2, 48, 48, fill='#4CAF50', outline='#2E7D32', width=2)
        logo.create_text(25, 25, text='CRM', fill='white', font=('Segoe UI', 14, 'bold'))
        logo.pack(side='left', padx=(0, 20))
        self._header_label = tk.Label(hf, text="История реализации продукции", font=STYLE['font_title'], bg=STYLE['bg_main'], fg=STYLE['text_primary'])
        self._header_label.pack(side='left', padx=(0, 20))
        tk.Button(hf, text="← Назад к списку", font=STYLE['font_btn'], bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=15, pady=8, cursor='hand2', command=lambda: self.controller.show_frame("MainWindow")).pack(side='right')
    def _create_content(self):
        content_frame = tk.Frame(self, bg=STYLE['bg_main'])
        content_frame.pack(fill='both', expand=True, padx=30, pady=(0, 30))
        self._info_label = tk.Label(content_frame, text="", font=('Segoe UI', 12, 'italic'), bg='#E3F2FD', fg='#1565C0', padx=15, pady=10, anchor='w')
        self._info_label.pack(fill='x', pady=(0, 15))
        outer = tk.Frame(content_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        outer.pack(fill='both', expand=True)
        inner = tk.Frame(outer, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        columns = ("product_name", "quantity", "sale_date")
        self.tree = ttk.Treeview(inner, columns=columns, show='headings', height=20)
        self.tree.heading("product_name", text="Наименование продукции", anchor='w')
        self.tree.heading("quantity", text="Количество (шт.)", anchor='center')
        self.tree.heading("sale_date", text="Дата продажи", anchor='center')
        self.tree.column("product_name", width=450, anchor='w')
        self.tree.column("quantity", width=180, anchor='center')
        self.tree.column("sale_date", width=180, anchor='center')
        tree_scroll = tk.Scrollbar(inner, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side='left', fill='both', expand=True, padx=15, pady=15)
        tree_scroll.pack(side='right', fill='y', pady=15)
        self._status_label = tk.Label(content_frame, text="", font=('Segoe UI', 10), bg=STYLE['bg_card'], fg=STYLE['text_secondary'], anchor='w', padx=10, pady=5)
        self._status_label.pack(fill='x', pady=(10, 0))
    def load_history(self, partner_id: int):
        self._partner_id = partner_id
        self._partner_name = get_partner_name(DB_PATH, partner_id)
        self.controller.title(f"CRM: История реализации продукции — {self._partner_name}")
        self._info_label.config(text=f" Партнер: {self._partner_name}")
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            history = get_partner_sales_history(DB_PATH, partner_id)
        except sqlite3.Error as e:
            logger.error(f"Error loading history for partner {partner_id}: {e}")
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить историю продаж:\n{e}")
            self._status_label.config(text="❌ Ошибка загрузки данных")
            return
        if not history:
            self._status_label.config(text="ℹ️ У данного партнера пока нет истории продаж")
            return
        total_qty = 0
        for product_name, quantity, sale_date in history:
            self.tree.insert('', 'end', values=(product_name, f"{quantity:,}", sale_date))
            total_qty += quantity
        self._status_label.config(text=f"📊 Всего записей: {len(history)} | Общий объём реализации: {total_qty:,} шт.")

class MaterialCalculatorWindow(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=STYLE['bg_main'])
        self.controller = controller
        self._product_types = []
        self._material_types = []
        self._create_header()
        self._create_form()
        self._create_result_panel()
    def _create_header(self):
        hf = tk.Frame(self, bg=STYLE['bg_main'])
        hf.pack(fill='x', padx=30, pady=25)
        logo = tk.Canvas(hf, width=50, height=50, highlightthickness=0, bg=STYLE['bg_main'])
        logo.create_rectangle(2, 2, 48, 48, fill='#FF9800', outline='#E65100', width=2)
        logo.create_text(25, 25, text='CALC', fill='white', font=('Segoe UI', 12, 'bold'))
        logo.pack(side='left', padx=(0, 20))
        tk.Label(hf, text="Калькулятор расхода материалов", font=STYLE['font_title'], bg=STYLE['bg_main'], fg=STYLE['text_primary']).pack(side='left')
        tk.Button(hf, text="← Назад к списку", font=STYLE['font_btn'], bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=15, pady=8, cursor='hand2', command=lambda: self.controller.show_frame("MainWindow")).pack(side='right')
    def _create_form(self):
        # Гарантируем инициализацию справочников перед загрузкой в ComboBox
        ensure_materials_tables(DB_PATH)
        seed_materials_data(DB_PATH)
        scroll_canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scroll_frame = tk.Frame(scroll_canvas, bg=STYLE['bg_main'])
        scroll_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        self._scroll_window = scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_canvas.pack(side='top', fill='both', expand=True, padx=30, pady=(0, 30))
        scroll_canvas.bind('<Configure>', self._on_resize)
        outer = tk.Frame(scroll_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        outer.pack(fill='x', pady=10)
        inner = tk.Frame(outer, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        form = tk.Frame(inner, bg=STYLE['bg_card'])
        form.pack(fill='x', padx=40, pady=30)
        self._product_types = get_all_product_types(DB_PATH)
        self._material_types = get_all_material_types(DB_PATH)
        product_names = [f"{pid}. {name}" for pid, name in self._product_types]
        material_names = [f"{mid}. {name}" for mid, name in self._material_types]
        self._add_combobox(form, "Тип продукции *", product_names, "product_type")
        self._add_combobox(form, "Тип материала *", material_names, "material_type")
        self._add_entry(form, "Количество (шт.) *", "quantity", placeholder='Например: 100')
        self._add_entry(form, "Параметр изделия 1 *", "param_1", placeholder='Например: 2.5')
        self._add_entry(form, "Параметр изделия 2 *", "param_2", placeholder='Например: 4.0')
        btn_frame = tk.Frame(form, bg=STYLE['bg_card'])
        btn_frame.pack(fill='x', pady=(25, 0))
        tk.Button(btn_frame, text=" Рассчитать", font=STYLE['font_btn'], bg='#FF9800', fg='white', relief='flat', padx=25, pady=10, cursor='hand2', command=self._on_calculate).pack(side='left', padx=(0, 15))
        tk.Button(btn_frame, text="Очистить", font=STYLE['font_btn'], bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=25, pady=10, cursor='hand2', command=self._on_clear).pack(side='left')
    def _add_combobox(self, parent, label_text: str, values: list, key: str):
        row = tk.Frame(parent, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text=label_text, font=STYLE['font_label'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=22, anchor='w').pack(side='left')
        var = tk.StringVar()
        if values: var.set(values[0])
        cb = ttk.Combobox(row, textvariable=var, values=values, state='readonly', font=STYLE['font_entry'], width=35)
        cb.pack(side='left')
        setattr(self, f"_{key}_var", var)
        setattr(self, f"_{key}_values", values)
    def _add_entry(self, parent, label_text: str, key: str, placeholder: str = ''):
        row = tk.Frame(parent, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text=label_text, font=STYLE['font_label'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=22, anchor='w').pack(side='left')
        entry = PlaceholderEntry(row, placeholder=placeholder, font=STYLE['font_entry'], width=37, fg=STYLE['text_primary'], bg='#FAFAFA', relief='solid', bd=1)
        entry.pack(side='left')
        setattr(self, f"_{key}_entry", entry)
    def _create_result_panel(self):
        self._result_frame = tk.Frame(self, bg=STYLE['bg_main'])
        self._result_frame.pack(fill='x', padx=30, pady=(0, 30))
        outer = tk.Frame(self._result_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        outer.pack(fill='x')
        inner = tk.Frame(outer, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        self._result_inner = tk.Frame(inner, bg=STYLE['bg_card'])
        self._result_inner.pack(fill='x', padx=30, pady=25)
        self._result_title = tk.Label(self._result_inner, text="", font=('Segoe UI', 14, 'bold'), bg=STYLE['bg_card'])
        self._result_title.pack()
        self._result_value = tk.Label(self._result_inner, text="", font=STYLE['font_result_number'], bg=STYLE['bg_card'])
        self._result_value.pack(pady=(5, 10))
        self._result_details = tk.Label(self._result_inner, text="", font=('Segoe UI', 11), bg=STYLE['bg_card'], fg=STYLE['text_secondary'], justify='left')
        self._result_details.pack()
        self._result_frame.pack_forget()
    def _on_resize(self, event):
        w = event.widget.winfo_width()
        if w > 0: event.widget.itemconfig(self._scroll_window, width=w)
    def _extract_id_from_choice(self, choice: str) -> int:
        if not choice: return -1
        try: return int(choice.split('.', 1)[0])
        except (ValueError, IndexError): return -1
    def _on_clear(self):
        self._quantity_entry.delete(0, tk.END)
        self._quantity_entry._show_placeholder()
        self._param_1_entry.delete(0, tk.END)
        self._param_1_entry._show_placeholder()
        self._param_2_entry.delete(0, tk.END)
        self._param_2_entry._show_placeholder()
        if self._product_types: self._product_type_var.set(self._product_type_values[0])
        if self._material_types: self._material_type_var.set(self._material_type_values[0])
        self._result_frame.pack_forget()
    def _on_calculate(self):
        product_id = self._extract_id_from_choice(self._product_type_var.get())
        material_id = self._extract_id_from_choice(self._material_type_var.get())
        quantity_str = self._quantity_entry.get_value().strip()
        param_1_str = self._param_1_entry.get_value().strip()
        param_2_str = self._param_2_entry.get_value().strip()
        if not quantity_str:
            self._show_error("Поле 'Количество' обязательно для заполнения.\n\nВведите целое положительное число.")
            self._quantity_entry.focus_set()
            return
        if not param_1_str or not param_2_str:
            self._show_error("Параметры изделия обязательны для заполнения.\n\nВведите положительные числа (например: 2.5).")
            return
        try:
            quantity = int(quantity_str)
            param_1 = float(param_1_str)
            param_2 = float(param_2_str)
        except ValueError:
            self._show_error("Некорректный формат чисел.\n\n• Количество — целое число (например: 100)\n• Параметры — вещественные числа (например: 2.5)")
            return
        try:
            result = calculate_material_required(product_type_id=product_id, material_type_id=material_id, quantity=quantity, param_1=param_1, param_2=param_2, db_path=DB_PATH)
        except Exception as e:
            logger.error(f"Unexpected error in calculator logic: {e}")
            self._show_error(f"Непредвиденная ошибка алгоритма:\n{e}\n\nОбратитесь к администратору.")
            return
        if result == -1:
            logger.warning(f"Calculation returned -1 for inputs: qty={quantity}, p1={param_1}, p2={param_2}")
            self._show_error("Расчёт невозможен: некорректные входные данные.\n\nВозможные причины:\n• Количество должно быть положительным целым числом\n• Параметры изделия должны быть положительными числами\n• Выбранные типы продукции/материала не найдены в справочнике")
            return
        self._show_success(result, quantity, product_id, material_id, param_1, param_2)
    def _show_success(self, result: int, quantity: int, product_id: int, material_id: int, param_1: float, param_2: float):
        product_name = next((n for pid, n in self._product_types if pid == product_id), f"Тип {product_id}")
        material_name = next((n for mid, n in self._material_types if mid == material_id), f"Материал {material_id}")
        self._result_inner.config(bg=STYLE['bg_result_success'])
        self._result_title.config(text="✅ Расчёт выполнен успешно", bg=STYLE['bg_result_success'], fg=STYLE['text_success'])
        self._result_value.config(text=f"{result:,} ед.", bg=STYLE['bg_result_success'], fg=STYLE['text_success'])
        self._result_details.config(text=f"📦 Тип продукции: {product_name}\n🔧 Материал: {material_name}\n📋 Количество изделий: {quantity:,} шт.\n📐 Параметры: {param_1} × {param_2}\n\nЗначение включает коэффициент типа продукции и процент брака материала.", bg=STYLE['bg_result_success'], fg=STYLE['text_primary'])
        self._result_frame.pack(fill='x', padx=30, pady=(0, 30))
    def _show_error(self, message: str):
        self._result_inner.config(bg=STYLE['bg_result_error'])
        self._result_title.config(text="❌ Ошибка расчёта", bg=STYLE['bg_result_error'], fg=STYLE['text_error'])
        self._result_value.config(text="—", bg=STYLE['bg_result_error'], fg=STYLE['text_error'])
        self._result_details.config(text=message, bg=STYLE['bg_result_error'], fg=STYLE['text_primary'])
        self._result_frame.pack(fill='x', padx=30, pady=(0, 30))

# ==========================================
# КОНТРОЛЛЕР
# ==========================================
class CRMApp(tk.Tk):
    def __init__(self, stress_test: bool = False):
        super().__init__()
        self.stress_test = stress_test
        self.title("CRM: Реестр партнеров")
        self.geometry("1000x700")
        self.configure(bg=STYLE['bg_main'])
        self.container = tk.Frame(self, bg=STYLE['bg_main'])
        self.container.pack(fill='both', expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (MainWindow, PartnerEditWindow, PartnerHistoryWindow, MaterialCalculatorWindow):
            page = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self._current_page = None
        self.show_frame("MainWindow")
        self._create_app_icon()
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", lambda e: self._on_mousewheel_step(-3))
        self.bind_all("<Button-5>", lambda e: self._on_mousewheel_step(3))
    def _find_canvas_in(self, widget):
        if isinstance(widget, tk.Canvas):
            try:
                if widget.cget('scrollregion'): return widget
            except tk.TclError: pass
        for child in widget.winfo_children():
            result = self._find_canvas_in(child)
            if result: return result
        return None
    def _on_mousewheel(self, event):
        if self._current_page and self._current_page in self.frames:
            canvas = self._find_canvas_in(self.frames[self._current_page])
            if canvas: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _on_mousewheel_step(self, steps):
        if self._current_page and self._current_page in self.frames:
            canvas = self._find_canvas_in(self.frames[self._current_page])
            if canvas: canvas.yview_scroll(steps, "units")
    def show_frame(self, page_name, partner_id=None):
        frame = self.frames[page_name]
        frame.tkraise()
        self._current_page = page_name
        if page_name == "MainWindow":
            self.title("CRM: Реестр партнеров")
            frame.refresh_data()
        elif page_name == "PartnerEditWindow":
            self.title("CRM: Карточка партнера [Редактирование]" if partner_id else "CRM: Карточка партнера [Создание]")
            frame.reset_form(partner_id=partner_id)
        elif page_name == "PartnerHistoryWindow":
            self.title("CRM: История реализации продукции")
            if partner_id: frame.load_history(partner_id)
        elif page_name == "MaterialCalculatorWindow":
            self.title("CRM: Калькулятор расхода материалов")
    def _create_app_icon(self):
        self._icon_image = tk.PhotoImage(width=32, height=32)
        for x in range(32):
            for y in range(32): self._icon_image.put('#4CAF50', (x, y))
        try: self.iconphoto(True, self._icon_image)
        except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--stress':
        print("Запуск стресс-теста...")
        CRMApp(stress_test=True).mainloop()
    else:
        print("Запуск CRM (Этап 4, Задача 4 — Тестирование и аудит)...")
        CRMApp().mainloop()