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

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

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
        combo_source_currency = ttk.Combobox(parent, values=[
            "USD", "EUR", "RUB", "GBP", "AUD", "CAD", "CHF", "CNY", "DKK", "HKD", "INR", "KRW", "MXN", "NZD",
            "PLN", "SEK", "TRY", "ZAR", "NOK", "ILS", "BRL", "THB", "MYR", "PHP"
        ], state="readonly")
        label_target_currency = tk.Label(parent, text="Получатель:")
        combo_target_currency = ttk.Combobox(parent, values=[
            "USD", "EUR", "RUB", "GBP", "AUD", "CAD", "CHF", "CNY", "DKK", "HKD", "INR", "KRW", "MXN", "NZD",
            "PLN", "SEK", "TRY", "ZAR", "NOK", "ILS", "BRL", "THB", "MYR", "PHP"
        ], state="readonly")
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
        combo_currency = ttk.Combobox(frame_input, values=[
            "USD", "EUR", "RUB", "GBP", "AUD", "CAD", "CHF", "CNY", "DKK", "HKD", "INR", "KRW", "MXN", "NZD",
            "PLN", "SEK", "TRY", "ZAR", "NOK", "ILS", "BRL", "THB", "MYR", "PHP"
        ], state="readonly")
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
        button_plot.grid(row=3, column=0, columnspan=2)

        # Окно графика
        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def plot_graph(self, target_currency, start_date, end_date):
        # Очистка предыдущего графика
        self.ax.clear()

        # Получаем данные с API по актуальным курсам (будем запрашивать ежедневно за указанный период)
        url = f"https://api.exchangerate-api.com/v4/timeseries/{start_date}/{end_date}?base=USD&symbols={target_currency}"
        response = requests.get(url)
        if response.status_code != 200:
            showwarning("Ошибка", "Нет связи с API.")
            return

        # Парсим данные из API
        data = response.json()
        dates = sorted(data['rates'].keys())
        rates = [data['rates'][date][target_currency] for date in dates]

        # Преобразуем даты в нужный формат
        formatted_dates = [datetime.datetime.strptime(date, "%Y-%m-%d") for date in dates]

        # Рисуем график
        self.ax.plot(formatted_dates, rates, marker='.', markersize=8, linestyle='-', color='b',
                     label=f"Курс USD к {target_currency}")

        # Оформляем график
        self.ax.set_title(f"Динамика курса USD к {target_currency}\n({start_date} - {end_date})", fontsize=14)
        self.ax.set_xlabel("Дата", fontsize=12)
        self.ax.set_ylabel("Курс", fontsize=12)
        self.ax.legend(loc='upper left')
        self.ax.grid(True, alpha=0.3)

        # Обновляем график
        self.canvas.draw()

    def convert(self, amount_str, source_currency, target_currency):
        # Преобразование суммы и валют
        try:
            amount = float(amount_str.strip())  # Преобразуем строку в число
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной.")

            # Обращаемся к внешнему API для получения курса валют
            url = f"https://api.exchangerate-api.com/v4/latest/{source_currency}"
            response = requests.get(url)
            if response.status_code != 200:
                raise ConnectionError("Проблемы с подключением к API.")

            data = response.json()
            rate = data["rates"][target_currency]
            result = amount * rate

            # Дата и время конвертации
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Сохраняем результат в базу данных
            cursor.execute("INSERT INTO conversions VALUES(NULL, ?, ?, ?, ?, ?)",
                           (current_time, amount, source_currency, target_currency, result))
            conn.commit()

            # Выводим результат пользователю
            showinfo("Результат", f"{amount} {source_currency} = {result:.2f} {target_currency}")

        except ValueError as ve:
            showwarning("Ошибка", f"Введены неправильные данные: {ve}.")
        except KeyError:
            showwarning("Ошибка", "Невозможно определить курс указанной валюты.")
        except ConnectionError as ce:
            showwarning("Ошибка", f"Соединение с API прервано: {ce}.")
        except Exception as e:
            showwarning("Ошибка", f"Возникла ошибка: {e}.")

# Создание окна и старт приложения
root = tk.Tk()
app = Application(master=root)
app.mainloop()
