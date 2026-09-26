import sys
from pathlib import Path
import hashlib
import math
import random

# ==========================================
# НАСТРОЙКА ПУТЕЙ
# Файл лежит в: 21.09.2026/Разработка формы добавления/редактирования партнера/
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
STAGE2_DIR = REPO_ROOT / "14.09.2026" / "Интеграция с БД и агрегация данных (SQL + Backend)"
STAGE1_DIR = REPO_ROOT / "14.09.2026" / "Разработка ядра бизнес-логики (Расчет скидки)"
sys.path.insert(0, str(STAGE2_DIR))
sys.path.insert(0, str(STAGE1_DIR))

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from partner_service import get_partner_with_discount, init_db, DB_PATH

# ==========================================
# СТИЛИ И КОНСТАНТЫ
# ==========================================
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
    'font_label': ('Segoe UI', 11),
    'font_entry': ('Segoe UI', 11),
    'font_btn': ('Segoe UI', 11, 'bold'),
}

ICON_COLORS = [
    '#E53935', '#D81B60', '#8E24AA', '#5E35B1', '#3949AB',
    '#1E88E5', '#039BE5', '#00ACC1', '#00897B', '#43A047',
    '#7CB342', '#C0CA33', '#FDD835', '#FFB300', '#FB8C00',
    '#F4511E', '#6D4C41', '#546E7A',
]
ICON_SHAPES = ['circle', 'square', 'diamond', 'hexagon', 'triangle', 'rounded_square']

PARTNER_TYPES = ["ООО", "ЗАО", "АО", "ПАО", "ОАО", "ИП"]

DEMO_QUANTITIES = [5_000, 0, 25_000, 75_000, 350_000, 150_000, 12_500, 500_000]

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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================
def hash_string(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def extend_db_schema(db_path: str) -> None:
    """Добавляет колонки, которых нет в базовой схеме partner_service,
    но которые требует форма редактирования (Задача 2)."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(partners)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        for col, col_type, default in [
            ('partner_type', 'TEXT', "'ООО'"),
            ('address', 'TEXT', "''"),
            ('director_name', 'TEXT', "''"),
        ]:
            if col not in existing_cols:
                cursor.execute(f"ALTER TABLE partners ADD COLUMN {col} {col_type} DEFAULT {default}")
        conn.commit()
    finally:
        conn.close()

def seed_test_data(db_path: str, stress_test: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DELETE FROM sales_history")
        cursor.execute("DELETE FROM partners")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='sales_history'")
        cursor.execute("PRAGMA foreign_keys = ON")

        count = 100 if stress_test else len(BASE_PARTNERS)
        for i in range(1, count + 1):
            if stress_test:
                vals = (i, f'Компания {i}', f'company{i}@example.com',
                        f'+7 (999) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                        round(random.uniform(5.0, 10.0), 1),
                        random.choice(PARTNER_TYPES), f'г. Город, ул. Улица, {i}', f'Директор {i}')
                qty = random.randint(0, 500_000)
            else:
                idx = (i - 1) % len(BASE_PARTNERS)
                bp = BASE_PARTNERS[idx]
                vals = (i, bp[1], bp[2], bp[3], bp[4], bp[5], bp[6], bp[7])
                qty = DEMO_QUANTITIES[idx]

            cursor.execute(
                "INSERT INTO partners (id, name, email, phone, rating, partner_type, address, director_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?);", vals
            )
            cursor.execute("INSERT INTO sales_history (partner_id, quantity) VALUES (?, ?);", (i, qty))
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

def save_partner(db_path: str, partner_data: dict) -> None:
    """Сохраняет нового партнера или обновляет существующего."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        pid = partner_data.get('id')
        if pid:
            cursor.execute("""
                UPDATE partners SET name=?, email=?, phone=?, rating=?,
                       partner_type=?, address=?, director_name=?
                WHERE id=?
            """, (partner_data['name'], partner_data['email'], partner_data['phone'],
                  partner_data['rating'], partner_data['partner_type'],
                  partner_data['address'], partner_data['director_name'], pid))
        else:
            cursor.execute("""
                INSERT INTO partners (name, email, phone, rating, partner_type, address, director_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (partner_data['name'], partner_data['email'], partner_data['phone'],
                  partner_data['rating'], partner_data['partner_type'],
                  partner_data['address'], partner_data['director_name']))
            new_id = cursor.lastrowid
            cursor.execute("INSERT INTO sales_history (partner_id, quantity) VALUES (?, 0);", (new_id,))
        conn.commit()
    finally:
        conn.close()

# ==========================================
# ПЛЕЙСХОЛДЕР-ВИДЖЕТ
# ==========================================
class PlaceholderEntry(tk.Entry):
    """Entry с серым текстом-подсказкой, который исчезает при фокусе."""
    def __init__(self, parent, placeholder: str, **kwargs):
        super().__init__(parent, **kwargs)
        self._placeholder = placeholder
        self._placeholder_active = False
        self._normal_fg = kwargs.get('fg', STYLE['text_primary'])
        self._placeholder_fg = '#AAAAAA'

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        if not self.get():
            self._placeholder_active = True
            self.config(fg=self._placeholder_fg)
            self.insert(0, self._placeholder)

    def _on_focus_in(self, _event):
        if self._placeholder_active:
            self.delete(0, tk.END)
            self.config(fg=self._normal_fg)
            self._placeholder_active = False

    def _on_focus_out(self, _event):
        if not self.get():
            self._show_placeholder()

    def get_value(self) -> str:
        """Возвращает текст без плейсхолдера."""
        return '' if self._placeholder_active else self.get()

# ==========================================
# UI КОМПОНЕНТЫ
# ==========================================
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

        if shape == 'circle':
            self.create_oval(bw, bw, size-bw, size-bw, fill=bg_color, outline=color, width=bw)
        elif shape == 'square':
            self.create_rectangle(bw, bw, size-bw, size-bw, fill=bg_color, outline=color, width=bw)
        elif shape == 'diamond':
            self.create_polygon(cx, bw, size-bw, cy, cx, size-bw, bw, cy, fill=bg_color, outline=color, width=bw)
        elif shape == 'hexagon':
            pts = []
            for i in range(6):
                a = 60 * i - 30
                pts.extend([cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))])
            self.create_polygon(*pts, fill=bg_color, outline=color, width=bw)
        elif shape == 'triangle':
            self.create_polygon(cx, bw, size-bw, size-bw, bw, size-bw, fill=bg_color, outline=color, width=bw)
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
    def __init__(self, parent, partner_data):
        super().__init__(parent, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
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
        tk.Label(name_frame, text=f"{partner_data.get('type', 'Партнер')} | {company_name}",
                 font=STYLE['font_card_title'], bg=STYLE['bg_card'], fg=STYLE['text_primary'], anchor='w').pack(side='left')

        discount = partner_data.get('discount_percent', 0) or 0
        tk.Label(top_frame, text=f"{discount}%", font=STYLE['font_discount'],
                 bg=STYLE['bg_card'], fg=STYLE['text_primary']).pack(side='right')

        info_frame = tk.Frame(content, bg=STYLE['bg_card'])
        info_frame.pack(fill='x', padx=46)
        for text, color in [
            (partner_data.get('position', 'Партнер'), STYLE['text_secondary']),
            (partner_data.get('phone', 'Не указан'), STYLE['text_primary']),
            (f"Рейтинг: {partner_data.get('rating', 0.0)} | Куплено: {partner_data.get('total_quantity', 0):,} ед.", STYLE['text_secondary']),
        ]:
            tk.Label(info_frame, text=text, font=STYLE['font_card_text'],
                     bg=STYLE['bg_card'], fg=color, anchor='w').pack(fill='x', pady=(0, 4))

# ==========================================
# СТРАНИЦЫ
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

        tk.Label(hf, text="Список партнеров и скидок", font=STYLE['font_title'],
                 bg=STYLE['bg_main'], fg=STYLE['text_primary']).pack(side='left', pady=15)

        tk.Button(hf, text="➕ Добавить партнера", font=STYLE['font_btn'],
                  bg='#4CAF50', fg='white', relief='flat', padx=15, pady=8, cursor='hand2',
                  command=lambda: self.controller.show_frame("PartnerEditWindow")).pack(side='right')

    def _create_content_area(self):
        self.canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=STYLE['bg_main'])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scrollbar.pack(side='right', fill='y', pady=(0, 30))

        self.outer_frame = tk.Frame(self.scrollable_frame, bg=STYLE['border_color'],
                                    highlightthickness=1, highlightbackground=STYLE['border_color'])
        self.outer_frame.pack(fill='x')
        self.cards_container = tk.Frame(self.outer_frame, bg=STYLE['bg_card'])
        self.cards_container.pack(fill='both', expand=True, padx=1, pady=1)
        self.canvas.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        w = self.canvas.winfo_width()
        if w > 0:
            self.canvas.itemconfig(self.canvas_window, width=w)

    def refresh_data(self):
        for w in self.cards_container.winfo_children():
            w.destroy()
        init_db(DB_PATH)
        extend_db_schema(DB_PATH)
        seed_test_data(DB_PATH)
        ids = get_all_partners(DB_PATH)
        if not ids:
            tk.Label(self.cards_container, text="Нет данных о партнерах",
                     font=('Segoe UI', 14), bg=STYLE['bg_card'], fg=STYLE['text_secondary']).pack(pady=50)
            return
        for pid in ids:
            try:
                data = get_partner_with_discount(DB_PATH, pid)
                if 'error' in data:
                    continue
                data['type'] = 'Партнер'
                data['position'] = 'Партнер'
                PartnerCard(self.cards_container, data).pack(fill='x', pady=15, padx=20)
            except Exception as e:
                print(f"Ошибка: {e}")


class PartnerEditWindow(tk.Frame):
    """Форма добавления/редактирования партнера с полями из ТЗ."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=STYLE['bg_main'])
        self.controller = controller
        self._editing_id = None
        self._create_header()
        self._create_form()

    def _create_header(self):
        hf = tk.Frame(self, bg=STYLE['bg_main'])
        hf.pack(fill='x', padx=30, pady=25)

        tk.Button(hf, text="← Назад", font=STYLE['font_btn'],
                  bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat',
                  padx=15, pady=8, cursor='hand2',
                  command=lambda: self.controller.show_frame("MainWindow")).pack(side='left')

        self._header_label = tk.Label(hf, text="Новый партнер", font=STYLE['font_title'],
                                      bg=STYLE['bg_main'], fg=STYLE['text_primary'])
        self._header_label.pack(side='left', padx=20)

    def _create_form(self):
        scroll_canvas = tk.Canvas(self, bg=STYLE['bg_main'], highlightthickness=0, bd=0)
        scroll_sb = tk.Scrollbar(self, orient='vertical', command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg=STYLE['bg_main'])
        scroll_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        scroll_canvas.configure(yscrollcommand=scroll_sb.set)
        scroll_canvas.bind_all("<MouseWheel>", lambda e: scroll_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        scroll_canvas.pack(side='left', fill='both', expand=True, padx=30, pady=(0, 30))
        scroll_sb.pack(side='right', fill='y', pady=(0, 30))

        # Рамка формы
        outer = tk.Frame(scroll_frame, bg=STYLE['border_color'], highlightthickness=1, highlightbackground=STYLE['border_color'])
        outer.pack(fill='x', pady=10)
        inner = tk.Frame(outer, bg=STYLE['bg_card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)
        form = tk.Frame(inner, bg=STYLE['bg_card'])
        form.pack(fill='x', padx=40, pady=30)

        # --- Поля формы ---
        self._fields = {}

        # Наименование
        self._add_field(form, "Наименование *", "name", placeholder='Например: ООО "Ромашка"')

        # Тип партнера (ComboBox — строго из списка)
        row = tk.Frame(form, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text="Тип партнера *", font=STYLE['font_label'],
                 bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=20, anchor='w').pack(side='left')
        self._type_var = tk.StringVar(value="ООО")
        type_cb = ttk.Combobox(row, textvariable=self._type_var, values=PARTNER_TYPES,
                               state='readonly', font=STYLE['font_entry'], width=30)
        type_cb.pack(side='left')
        self._fields['partner_type'] = type_cb

        # Рейтинг
        self._add_field(form, "Рейтинг *", "rating", placeholder='Целое число от 0 до 10')

        # Адрес
        self._add_field(form, "Адрес", "address", placeholder='г. Москва, ул. Примерная, д. 1')

        # ФИО директора
        self._add_field(form, "ФИО директора", "director_name", placeholder='Иванов Иван Иванович')

        # Телефон (с плейсхолдером-маской)
        self._add_field(form, "Телефон", "phone", placeholder='+7 (XXX) XXX-XX-XX')

        # Email (с плейсхолдером-маской)
        self._add_field(form, "Email *", "email", placeholder='example@company.ru')

        # --- Кнопки ---
        btn_frame = tk.Frame(form, bg=STYLE['bg_card'])
        btn_frame.pack(fill='x', pady=(25, 0))

        tk.Button(btn_frame, text="💾 Сохранить", font=STYLE['font_btn'],
                  bg='#4CAF50', fg='white', relief='flat', padx=25, pady=10, cursor='hand2',
                  command=self._on_save).pack(side='left', padx=(0, 15))

        tk.Button(btn_frame, text="Отмена", font=STYLE['font_btn'],
                  bg='#f0f0f0', fg=STYLE['text_primary'], relief='flat', padx=25, pady=10, cursor='hand2',
                  command=lambda: self.controller.show_frame("MainWindow")).pack(side='left')

    def _add_field(self, parent, label_text: str, key: str, placeholder: str = ''):
        """Создаёт строку «лейбл + поле ввода» и сохраняет ссылку в self._fields."""
        row = tk.Frame(parent, bg=STYLE['bg_card'])
        row.pack(fill='x', pady=8)
        tk.Label(row, text=label_text, font=STYLE['font_label'],
                 bg=STYLE['bg_card'], fg=STYLE['text_primary'], width=20, anchor='w').pack(side='left')
        entry = PlaceholderEntry(row, placeholder=placeholder, font=STYLE['font_entry'], width=35,
                                 fg=STYLE['text_primary'], bg='#FAFAFA', relief='solid', bd=1)
        entry.pack(side='left')
        self._fields[key] = entry

    def reset_form(self, partner_id: int = None):
        """Очищает форму или заполняет её данными существующего партнера."""
        self._editing_id = partner_id
        self._header_label.config(
            text="Редактирование партнера" if partner_id else "Новый партнер"
        )
        # Сбрасываем все текстовые поля
        for key, widget in self._fields.items():
            if key == 'partner_type':
                widget.set("ООО")
            else:
                widget.delete(0, tk.END)
                widget._show_placeholder()

        if partner_id:
            conn = sqlite3.connect(DB_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name, email, phone, rating, partner_type, address, director_name "
                    "FROM partners WHERE id=?", (partner_id,)
                )
                row = cursor.fetchone()
            finally:
                conn.close()
            if row:
                self._set_field('name', row[0])
                self._set_field('email', row[1])
                self._set_field('phone', row[2])
                self._set_field('rating', str(row[3]) if row[3] is not None else '')
                self._fields['partner_type'].set(row[4] if row[4] else 'ООО')
                self._set_field('address', row[5])
                self._set_field('director_name', row[6])

    def _set_field(self, key: str, value: str):
        """Заполняет поле реальным значением, убирая плейсхолдер."""
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

        # Валидация обязательных полей
        if not name:
            messagebox.showwarning("Ошибка", "Наименование обязательно для заполнения.")
            return
        if not email:
            messagebox.showwarning("Ошибка", "Email обязателен для заполнения.")
            return

        # Валидация рейтинга — целое неотрицательное число
        try:
            rating = int(rating_str) if rating_str else 0
            if rating < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Ошибка", "Рейтинг должен быть целым неотрицательным числом.")
            return

        save_partner(DB_PATH, {
            'id': self._editing_id,
            'name': name,
            'email': email,
            'phone': phone,
            'rating': rating,
            'partner_type': partner_type,
            'address': address,
            'director_name': director,
        })

        messagebox.showinfo("Успех", "Партнер успешно сохранён!")
        self.controller.show_frame("MainWindow")

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
        for F in (MainWindow, PartnerEditWindow):
            page = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("MainWindow")
        self._create_app_icon()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if page_name == "MainWindow":
            self.title("CRM: Реестр партнеров")
            frame.refresh_data()
        elif page_name == "PartnerEditWindow":
            self.title("CRM: Карточка партнера [Редактирование]")
            # Сбрасываем форму в режим «Новый партнер» при каждом открытии
            frame.reset_form(partner_id=None)

    def _create_app_icon(self):
        self._icon_image = tk.PhotoImage(width=32, height=32)
        for x in range(32):
            for y in range(32):
                self._icon_image.put('#4CAF50', (x, y))
        try:
            self.iconphoto(True, self._icon_image)
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--stress':
        print("Запуск стресс-теста...")
        CRMApp(stress_test=True).mainloop()
    else:
        print("Запуск CRM (Этап 3, Задача 2 — Форма редактирования)...")
        CRMApp().mainloop()