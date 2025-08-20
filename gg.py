import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import schedule
import time

class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют и криптовалют")
        self.root.geometry("900x700")
        
        # API ключи (можно установить через настройки)
        self.fiat_api_key = None
        self.crypto_api_key = None
        self.email_settings = {}
        
        # История операций
        self.history = []
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Запускаем обновление курсов
        self.schedule_updates()
    
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка конвертера
        self.create_converter_tab()
        
        # Вкладка истории
        self.create_history_tab()
        
        # Вкладка графиков
        self.create_chart_tab()
        
        # Вкладка настроек
        self.create_settings_tab()
    
    def create_converter_tab(self):
        """Вкладка конвертации валют"""
        converter_frame = ttk.Frame(self.notebook)
        self.notebook.add(converter_frame, text="Конвертер")
        
        # Выбор типа валюты
        currency_type_frame = ttk.Frame(converter_frame)
        currency_type_frame.pack(pady=10)
        
        ttk.Label(currency_type_frame, text="Тип валюты:").pack(side=tk.LEFT, padx=5)
        self.currency_type = ttk.Combobox(
            currency_type_frame, 
            values=["Обычные валюты", "Криптовалюты"],
            state="readonly",
            width=15
        )
        self.currency_type.pack(side=tk.LEFT, padx=5)
        self.currency_type.current(0)
        self.currency_type.bind("<<ComboboxSelected>>", self.update_currency_lists)
        
        # Ввод суммы
        amount_frame = ttk.Frame(converter_frame)
        amount_frame.pack(pady=10)
        
        ttk.Label(amount_frame, text="Сумма:").pack(side=tk.LEFT, padx=5)
        self.amount_entry = ttk.Entry(amount_frame, width=20)
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        
        # Выбор валют
        currency_frame = ttk.Frame(converter_frame)
        currency_frame.pack(pady=10)
        
        # Исходная валюта
        ttk.Label(currency_frame, text="Из:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.from_currency = ttk.Combobox(currency_frame, state="readonly", width=10)
        self.from_currency.grid(row=0, column=1, padx=5)
        
        # Целевая валюта
        ttk.Label(currency_frame, text="В:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.to_currency = ttk.Combobox(currency_frame, state="readonly", width=10)
        self.to_currency.grid(row=0, column=3, padx=5)
        
        # Кнопки
        button_frame = ttk.Frame(converter_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame, 
            text="Конвертировать", 
            command=self.convert
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="↔️ Поменять валюты", 
            command=self.swap_currencies
        ).pack(side=tk.LEFT, padx=5)
        
        # Результат
        result_frame = ttk.Frame(converter_frame)
        result_frame.pack(pady=10)
        
        self.result_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.result_var, font=("Arial", 12, "bold")).pack()
        
        # Email
        email_frame = ttk.Frame(converter_frame)
        email_frame.pack(pady=10)
        
        ttk.Label(email_frame, text="Email для отправки результата:").pack(side=tk.LEFT, padx=5)
        self.email_entry = ttk.Entry(email_frame, width=30)
        self.email_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            email_frame, 
            text="Отправить", 
            command=self.send_result_email
        ).pack(side=tk.LEFT, padx=5)
        
        # Инициализация списков валют
        self.update_currency_lists()
    
    def create_history_tab(self):
        """Вкладка истории операций"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="История")
        
        # Дерево для отображения истории
        columns = ("date", "amount", "from", "to", "result", "rate")
        self.history_tree = ttk.Treeview(
            history_frame, 
            columns=columns, 
            show="headings",
            height=15
        )
        
        # Настройка столбцов
        self.history_tree.heading("date", text="Дата и время")
        self.history_tree.heading("amount", text="Сумма")
        self.history_tree.heading("from", text="Из")
        self.history_tree.heading("to", text="В")
        self.history_tree.heading("result", text="Результат")
        self.history_tree.heading("rate", text="Курс")
        
        self.history_tree.column("date", width=150, anchor=tk.CENTER)
        self.history_tree.column("amount", width=100, anchor=tk.CENTER)
        self.history_tree.column("from", width=80, anchor=tk.CENTER)
        self.history_tree.column("to", width=80, anchor=tk.CENTER)
        self.history_tree.column("result", width=120, anchor=tk.CENTER)
        self.history_tree.column("rate", width=100, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки управления историей
        control_frame = ttk.Frame(history_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            control_frame, 
            text="Очистить историю", 
            command=self.clear_history
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Экспорт в JSON", 
            command=self.export_history_json
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Экспорт в CSV", 
            command=self.export_history_csv
        ).pack(side=tk.LEFT, padx=5)
    
    def create_chart_tab(self):
        """Вкладка графиков курсов"""
        chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(chart_frame, text="Графики")
        
        # Выбор валюты и периода
        control_frame = ttk.Frame(chart_frame)
        control_frame.pack(pady=10)
        
        ttk.Label(control_frame, text="Валюта:").pack(side=tk.LEFT, padx=5)
        self.chart_currency = ttk.Combobox(
            control_frame, 
            values=["USD", "EUR", "BTC", "ETH"],
            state="readonly",
            width=10
        )
        self.chart_currency.pack(side=tk.LEFT, padx=5)
        self.chart_currency.current(0)
        
        ttk.Button(
            control_frame, 
            text="Неделя", 
            command=lambda: self.update_chart(7)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Месяц", 
            command=lambda: self.update_chart(30)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Год", 
            command=lambda: self.update_chart(365)
        ).pack(side=tk.LEFT, padx=5)
        
        # График
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Инициализация графика
        self.update_chart(7)
    
    def create_settings_tab(self):
        """Вкладка настроек"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Настройки")
        
        # Настройки API
        api_frame = ttk.LabelFrame(settings_frame, text="API ключи", padding=10)
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # API для обычных валют
        ttk.Label(api_frame, text="API для валют:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.fiat_api_entry = ttk.Entry(api_frame, width=40)
        self.fiat_api_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(
            api_frame, 
            text="Сохранить", 
            command=self.save_fiat_api_key
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # API для криптовалют
        ttk.Label(api_frame, text="API для криптовалют:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.crypto_api_entry = ttk.Entry(api_frame, width=40)
        self.crypto_api_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(
            api_frame, 
            text="Сохранить", 
            command=self.save_crypto_api_key
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Настройки email
        email_frame = ttk.LabelFrame(settings_frame, text="Настройки почты", padding=10)
        email_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(email_frame, text="SMTP сервер:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.smtp_entry = ttk.Entry(email_frame, width=30)
        self.smtp_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Порт:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.port_entry = ttk.Entry(email_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_setting_entry = ttk.Entry(email_frame, width=30)
        self.email_setting_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(email_frame, text="Пароль:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(email_frame, width=20, show="*")
        self.password_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(
            email_frame, 
            text="Сохранить настройки", 
            command=self.save_email_settings
        ).grid(row=2, column=0, columnspan=4, pady=10)
    
    def update_currency_lists(self, event=None):
        """Обновление списков валют в зависимости от выбранного типа"""
        currency_type = self.currency_type.get()
        
        if currency_type == "Обычные валюты":
            currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY"]
        else:
            currencies = ["BTC", "ETH", "XRP", "LTC", "ADA", "DOGE"]
        
        self.from_currency["values"] = currencies
        self.to_currency["values"] = currencies
        
        if len(currencies) > 0:
            self.from_currency.current(0)
            if len(currencies) > 1:
                self.to_currency.current(1)
            else:
                self.to_currency.current(0)
    
    def convert(self):
        """Выполнение конвертации валют"""
        try:
            amount = float(self.amount_entry.get())
            from_curr = self.from_currency.get()
            to_curr = self.to_currency.get()
            
            if from_curr == to_curr:
                result = amount
                rate = 1.0
            else:
                # Здесь должна быть логика получения реального курса
                # Для примера используем фиктивные значения
                rates = {
                    "USD": 1.0,
                    "EUR": 0.85,
                    "RUB": 75.0,
                    "BTC": 0.000025,
                    "ETH": 0.0005
                }
                
                if from_curr in rates and to_curr in rates:
                    rate = rates[to_curr] / rates[from_curr]
                    result = amount * rate
                else:
                    messagebox.showerror("Ошибка", "Не удалось получить курс для выбранных валют")
                    return
            
            # Форматируем результат
            result_str = f"{amount:.2f} {from_curr} = {result:.6f} {to_curr} (Курс: {rate:.6f})"
            self.result_var.set(result_str)
            
            # Сохраняем в историю
            operation = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": f"{amount:.2f} {from_curr}",
                "from": from_curr,
                "to": to_curr,
                "result": f"{result:.6f} {to_curr}",
                "rate": f"{rate:.6f}"
            }
            self.history.append(operation)
            self.update_history_table()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
    
    def swap_currencies(self):
        """Обмен выбранных валют местами"""
        from_idx = self.from_currency.current()
        to_idx = self.to_currency.current()
        self.from_currency.current(to_idx)
        self.to_currency.current(from_idx)
    
    def send_result_email(self):
        """Отправка результата на email"""
        email = self.email_entry.get()
        result = self.result_var.get()
        
        if not email or not result:
            messagebox.showerror("Ошибка", "Введите email и получите результат конвертации")
            return
        
        try:
            if not self.email_settings:
                messagebox.showerror("Ошибка", "Настройте почту в разделе Настройки")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_settings['email']
            msg['To'] = email
            msg['Subject'] = 'Результат конвертации валют'
            
            body = f"Результат конвертации:\n{result}"
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_settings['smtp'], self.email_settings['port'])
            server.starttls()
            server.login(self.email_settings['email'], self.email_settings['password'])
            server.send_message(msg)
            server.quit()
            
            messagebox.showinfo("Успех", "Результат отправлен на указанный email")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить email: {str(e)}")
    
    def update_history_table(self):
        """Обновление таблицы истории"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        for op in reversed(self.history[-50:]):  # Показываем последние 50 операций
            self.history_tree.insert("", tk.END, values=(
                op["date"],
                op["amount"],
                op["from"],
                op["to"],
                op["result"],
                op["rate"]
            ))
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить историю операций?"):
            self.history = []
            self.update_history_table()
    
    def export_history_json(self):
        """Экспорт истории в JSON"""
        try:
            with open("conversion_history.json", "w") as f:
                json.dump(self.history, f, indent=2)
            messagebox.showinfo("Успех", "История экспортирована в conversion_history.json")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать историю: {str(e)}")
    
    def export_history_csv(self):
        """Экспорт истории в CSV"""
        try:
            import csv
            with open("conversion_history.csv", "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["date", "amount", "from", "to", "result", "rate"])
                writer.writeheader()
                writer.writerows(self.history)
            messagebox.showinfo("Успех", "История экспортирована в conversion_history.csv")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать историю: {str(e)}")
    
    def update_chart(self, days):
        """Обновление графика курса"""
        currency = self.chart_currency.get()
        if not currency:
            return
        
        try:
            # Здесь должна быть логика получения реальных данных
            # Для примера используем фиктивные данные
            dates = [datetime.now() - timedelta(days=x) for x in range(days, 0, -1)]
            values = [100 + x**0.5 + x*0.1 for x in range(days)]
            
            self.ax.clear()
            self.ax.plot(dates, values, 'b-')
            self.ax.set_title(f"Курс {currency} за последние {days} дней")
            self.ax.set_xlabel("Дата")
            self.ax.set_ylabel("Курс")
            self.ax.grid(True)
            
            # Форматирование дат
            self.fig.autofmt_xdate()
            
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить график: {str(e)}")
    
    def save_fiat_api_key(self):
        """Сохранение API ключа для валют"""
        self.fiat_api_key = self.fiat_api_entry.get()
        messagebox.showinfo("Успех", "API ключ для валют сохранен")
    
    def save_crypto_api_key(self):
        """Сохранение API ключа для криптовалют"""
        self.crypto_api_key = self.crypto_api_entry.get()
        messagebox.showinfo("Успех", "API ключ для криптовалют сохранен")
    
    def save_email_settings(self):
        """Сохранение настроек почты"""
        self.email_settings = {
            "smtp": self.smtp_entry.get(),
            "port": int(self.port_entry.get()),
            "email": self.email_setting_entry.get(),
            "password": self.password_entry.get()
        }
        messagebox.showinfo("Успех", "Настройки почты сохранены")
    
    def schedule_updates(self):
        """Планирование автоматического обновления курсов"""
        def update_task():
            # Здесь должна быть логика обновления курсов
            print("Обновление курсов...")
        
        # Обновляем каждые 10 минут
        schedule.every(10).minutes.do(update_task)
        
        # Запускаем планировщик в отдельном потоке
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
