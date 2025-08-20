import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo, showwarning
import requests
import sqlite3
import os.path
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import csv
import threading
import schedule
import time

# Соединяемся с базой данных (создаем новую, если её нет)
conn = sqlite3.connect('currency_history.db')
cursor = conn.cursor()

# Создаем таблицу для хранения истории конвертаций
cursor.execute('''
CREATE TABLE IF NOT EXISTS conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    amount REAL,
    source_currency TEXT,
    target_currency TEXT,
    result REAL
)
''')
conn.commit()

# Начнем с перечня доступных валют и криптовалют
ALL_CURRENCIES = [
    "USD", "EUR", "RUB", "GBP", "AUD", "CAD", "CHF", "CNY", "DKK", "HKD", "INR", "KRW", "MXN", "NZD",
    "PLN", "SEK", "TRY", "ZAR", "NOK", "ILS", "BRL", "THB", "MYR", "PHP",
    "BTC", "ETH", "LTC", "DOGE", "USDT"
]

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.schedule_update()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Вкладка 1: Конвертер
        frame1 = ttk.Frame(notebook)
        notebook.add(frame1, text="Конвертер")
        self.create_converter_frame(frame1)

        # Вкладка 2: История
        frame2 = ttk.Frame(notebook)
        notebook.add(frame2, text="История")
        self.create_history_frame(frame2)

        # Вкладка 3: График
        frame3 = ttk.Frame(notebook)
        notebook.add(frame3, text="График")
        self.create_graph_frame(frame3)

    def create_converter_frame(self, parent):
        # Интерфейс вкладки "Конвертер"
        label_amount = tk.Label(parent, text="Сумма:")
        entry_amount = tk.Entry(parent)
        label_source_currency = tk.Label(parent, text="Источник:")
        combo_source_currency = ttk.Combobox(parent, values=ALL_CURRENCIES, state="readonly")
        label_target_currency = tk.Label(parent, text="Получатель:")
        combo_target_currency = ttk.Combobox(parent, values=ALL_CURRENCIES, state="readonly")
        button_convert = tk.Button(parent, text="Конвертировать", command=lambda: self.convert(
            entry_amount.get(), combo_source_currency.get(), combo_target_currency.get()))
        label_result = tk.Label(parent, text="Результат: ")

        # Расположение элементов
        label_amount.grid(row=0, column=0, sticky=tk.W)
        entry_amount.grid(row=0, column=1)
        label_source_currency.grid(row=1, column=0, sticky=tk.W)
        combo_source_currency.grid(row=1, column=1)
        label_target_currency.grid(row=2, column=0, sticky=tk.W)
        combo_target_currency.grid(row=2, column=1)
        button_convert.grid(row=3, column=0, columnspan=2)
        label_result.grid(row=4, column=0, columnspan=2)

    def create_history_frame(self, parent):
        # Интерфейс вкладки "История"
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        # Поля для поиска
        label_search = tk.Label(search_frame, text="Поиск по истории:")
        entry_search = tk.Entry(search_frame)
        button_search = tk.Button(search_frame, text="Искать", command=lambda: self.search_history(entry_search.get()))

        # Расположение полей поиска
        label_search.grid(row=0, column=0, sticky=tk.W)
        entry_search.grid(row=0, column=1)
        button_search.grid(row=0, column=2)

        # Дерево для отображения истории
        treeview = ttk.Treeview(parent, columns=("Date", "Amount", "Source", "Target", "Result"), height=10)
        treeview.heading("#0", text="ID")
        treeview.column("#0", width=50)
        treeview.heading("Date", text="Дата")
        treeview.heading("Amount", text="Сумма")
        treeview.heading("Source", text="Источн.")
        treeview.heading("Target", text="Получ.")
        treeview.heading("Result", text="Результат")

        # Чтение данных из базы и заполнение дерева
        cursor.execute("SELECT * FROM conversions ORDER BY id DESC")
        rows = cursor.fetchall()
        for row in rows:
            treeview.insert("", "end", text=str(row[0]), values=(row[1], row[2], row[3], row[4], row[5]))

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=treeview.yview)
        treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        treeview.pack(expand=True, fill=tk.BOTH)

    def create_graph_frame(self, parent):
        # Интерфейс вкладки "График"
        # Элементы интерфейса для выбора валюты и периода
        frame_input = ttk.Frame(parent)
        frame_input.pack(fill=tk.X, padx=10, pady=10)

        # Валюта для отслеживания курса
        label_currency = tk.Label(frame_input, text="Выберите валюту:")
        combo_currency = ttk.Combobox(frame_input, values=ALL_CURRENCIES, state="readonly")
        combo_currency.current(0)

        # Период дат
        label_start_date = tk.Label(frame_input, text="Начальная дата (гггг-мм-дд):")
        start_date_entry = tk.Entry(frame_input)
        start_date_entry.insert(0, "2023-01-01")

        label_end_date = tk.Label(frame_input, text="Конечная дата (гггг-мм-дд):")
        end_date_entry = tk.Entry(frame_input)
        end_date_entry.insert(0, datetime.date.today().isoformat())

        # Кнопка построения графика
        button_plot = tk.Button(frame_input, text="Показать график", command=lambda: self.plot_graph(
            combo_currency.get(),
            start_date_entry.get(),
            end_date_entry.get()
        ))

        # Расположение элементов
        label_currency.grid(row=0, column=0, sticky=tk.W)
        combo_currency.grid(row=0, column=1)
        label_start_date.grid(row=1, column=0, sticky=tk.W)
        start_date_entry.grid(row=1, column=1)
        label_end_date.grid(row=2, column=0, sticky=tk.W)
        end_date_entry.grid(row=2, column=1)
