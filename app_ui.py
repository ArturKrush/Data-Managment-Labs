import tkinter as tk
from tkinter import ttk
import threading
import json
from db_manager import DatabaseManager


# ГОЛОВНИЙ КЛАС ДОДАТКУ
class GradebookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gradebook Transaction")
        self.root.geometry("850x650")
        self.setup_ui()

    # НАЛАШТУВАННЯ ІНТЕРФЕЙСУ
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        self.tab_transactions = ttk.Frame(notebook)
        notebook.add(self.tab_transactions, text='Транзакції (PostgreSQL)')
        self.build_transaction_tab()

        self.tab_history = ttk.Frame(notebook)
        notebook.add(self.tab_history, text='Історія оцінок (PostgreSQL)')
        self.build_history_tab()

        self.tab_mongo = ttk.Frame(notebook)
        notebook.add(self.tab_mongo, text='Курси (MongoDB)')
        self.build_mongo_tab()

    # ПОБУДОВА ВКЛАДКИ ТРАНЗАКЦІЙ
    def build_transaction_tab(self):
        frame_inputs = ttk.LabelFrame(self.tab_transactions, text="Створення оцінки (Паралельний запуск)")
        frame_inputs.pack(fill='x', padx=10, pady=10)

        # ОТРИМАННЯ ДОВІДНИКІВ З БАЗИ
        courses = DatabaseManager.get_courses()
        self.course_map = {name: cid for cid, name in courses}
        course_names = list(self.course_map.keys())

        grades = DatabaseManager.get_grades()
        self.grade_map = {str(val): gid for gid, val in grades}
        grade_values = list(self.grade_map.keys())

        # ВВЕДЕННЯ ID ЗАЛІКОВКИ
        ttk.Label(frame_inputs, text="ID Заліковки:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_gradebook = ttk.Entry(frame_inputs, width=15)
        self.ent_gradebook.insert(0, "1")
        self.ent_gradebook.grid(row=0, column=1, padx=5, pady=5)

        # ПОТІК 1: КУРС ТА ОЦІНКА
        ttk.Label(frame_inputs, text="Курс 1:").grid(row=1, column=0, padx=5, pady=5)
        self.cb_course1 = ttk.Combobox(frame_inputs, values=course_names, width=17, state="readonly")
        if course_names:
            self.cb_course1.set(course_names[0])
        self.cb_course1.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_inputs, text="Оцінка 1 (Бали):").grid(row=1, column=2, padx=5, pady=5)
        self.cb_grade1 = ttk.Combobox(frame_inputs, values=grade_values, width=12, state="readonly")
        if grade_values:
            self.cb_grade1.set("80")
        self.cb_grade1.grid(row=1, column=3, padx=5, pady=5)

        # ПОТІК 2: КУРС ТА ОЦІНКА
        ttk.Label(frame_inputs, text="Курс 2:").grid(row=2, column=0, padx=5, pady=5)
        self.cb_course2 = ttk.Combobox(frame_inputs, values=course_names, width=17, state="readonly")
        # Якщо в базі є хоча б два курси, для другого потоку обираємо другий курс за замовчуванням
        if len(course_names) > 1:
            self.cb_course2.set(course_names[1])
        elif course_names:
            self.cb_course2.set(course_names[0])
        self.cb_course2.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame_inputs, text="Оцінка 2 (Бали):").grid(row=2, column=2, padx=5, pady=5)
        self.cb_grade2 = ttk.Combobox(frame_inputs, values=grade_values, width=12, state="readonly")
        if grade_values:
            self.cb_grade2.set("90")
        self.cb_grade2.grid(row=2, column=3, padx=5, pady=5)

        # ПЕРЕМИКАЧ БЛОКУВАННЯ
        self.use_lock_var = tk.BooleanVar(value=False)
        chk_lock = ttk.Checkbutton(frame_inputs, text="Застосувати SELECT ... FOR UPDATE",
                                   variable=self.use_lock_var)
        chk_lock.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # КНОПКА ЗАПУСКУ
        btn_run = ttk.Button(frame_inputs, text="Запустити 2 потоки", command=self.run_parallel_transactions)
        btn_run.grid(row=3, column=2, columnspan=2, padx=5, pady=10)

        # ВІДЖЕТ ЖУРНАЛУ
        frame_log = ttk.LabelFrame(self.tab_transactions, text="Журнал операцій")
        frame_log.pack(fill='both', expand=True, padx=10, pady=5)

        self.text_log = tk.Text(frame_log, bg="#1e1e1e", fg="#4af626", font=("Consolas", 10), state='disabled')
        self.text_log.pack(fill='both', expand=True, padx=5, pady=5)

    # ПОБУДОВА ВКЛАДКИ ІСТОРІЇ ОЦІНОК
    def build_history_tab(self):
        btn_frame = ttk.Frame(self.tab_history)
        btn_frame.pack(fill='x', padx=10, pady=5)

        btn_refresh = ttk.Button(btn_frame, text="Оновити таблицю", command=self.load_history_data)
        btn_refresh.pack(side='right')

        # ТАБЛИЦЯ ВИВОДУ ДАНИХ
        columns = ("id", "student", "course", "grade", "date")
        self.tree = ttk.Treeview(self.tab_history, columns=columns, show="headings")

        self.tree.heading("id", text="ID запису")
        self.tree.heading("student", text="Студент")
        self.tree.heading("course", text="Курс")
        self.tree.heading("grade", text="Оцінка")
        self.tree.heading("date", text="Дата та час")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("student", width=150)
        self.tree.column("course", width=200)
        self.tree.column("grade", width=80, anchor="center")
        self.tree.column("date", width=150, anchor="center")

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

    # ПОБУДОВА ВКЛАДКИ MONGODB
    def build_mongo_tab(self):
        btn_frame = ttk.Frame(self.tab_mongo)
        btn_frame.pack(fill='x', padx=10, pady=5)

        btn_refresh = ttk.Button(btn_frame, text="Оновити документи з БД", command=self.load_mongo_data)
        btn_refresh.pack(side='right')

        self.text_mongo = tk.Text(self.tab_mongo, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.text_mongo.pack(fill='both', expand=True, padx=10, pady=5)

        self.load_mongo_data()

    # ОНОВЛЕННЯ ЛОГУВАННЯ
    def log_message(self, message):
        def update_ui():
            # Дозвіл потоку вивести дані у текстове поле
            self.text_log.config(state='normal')
            # Вставка повідомлення у кінець тексту
            self.text_log.insert('end', message + "\n")
            # Прокручування журналу у кінець
            self.text_log.see('end')
            # Повернення блокування на текстове поле
            self.text_log.config(state='disabled')
        '''
        Фоновий потік не вставляє текст у поле одразу, а 
        надсилає головному запит на виконання функції update_ui()
        через 0 мілісекунд - запит стає у безпечну чергу подій UI.
        '''
        self.root.after(0, update_ui)

    # МЕТОД ЗАПУСКУ ПАРАЛЕЛЬНИХ ПОТОКІВ
    def run_parallel_transactions(self):
        # ЗЧИТУВАННЯ ТА ПЕРЕТВОРЕННЯ ДАНИХ З UI
        # Отримання ID заліковки з поля введення
        gb_id = int(self.ent_gradebook.get())

        # Отримання текстового значення 1 курсу
        course_name1 = self.cb_course1.get()
        # Зіставлення з ID курсу
        course_id1 = self.course_map[course_name1]

        # Отримання текстового значення 1 оцінки
        g1_val = self.cb_grade1.get()
        # Зіставлення з ID оцінки
        g1_id = self.grade_map[g1_val]

        # Отримання текстового значення 2 курсу
        course_name2 = self.cb_course2.get()
        # Зіставлення з ID курсу
        course_id2 = self.course_map[course_name2]
        # Отримання текстового значення 2 оцінки
        g2_val = self.cb_grade2.get()
        # Зіставлення з ID оцінки
        g2_id = self.grade_map[g2_val]

        # Чи увімкнено захист від конкурентного доступу?
        use_lock = self.use_lock_var.get()

        self.log_message(f"\nЗАПУСК. БЛОКУВАННЯ: {use_lock}")

        # ІНІЦІАЛІЗАЦІЯ ПОТОКІВ
        '''
        Створення двох паралельних потоків із передачею аргументів транзакції,
        значення прапорця увімкнення захисту від паралельного доступу та функції логування.
        '''
        # ІНІЦІАЛІЗАЦІЯ ПОТОКІВ (одразу з правильним синтаксисом args/kwargs)
        t1 = threading.Thread(
            target=DatabaseManager.execute_grade_transaction,
            args=(gb_id, course_id1, g1_id),
            kwargs={
                "thread_name": "Потік 1",
                "use_lock": use_lock,
                "log_callback": self.log_message
            }
        )

        t2 = threading.Thread(
            target=DatabaseManager.execute_grade_transaction,
            args=(gb_id, course_id2, g2_id),
            kwargs={
                "thread_name": "Потік 2",
                "use_lock": use_lock,
                "log_callback": self.log_message
            }
        )
        # Запуск потоків
        t1.start()
        t2.start()

    # ЗАВАНТАЖЕННЯ ДАНИХ В ТАБЛИЦЮ ІСТОРІЇ
    def load_history_data(self):
        # ОЧИЩЕННЯ ТАБЛИЦІ ПЕРЕД ОНОВЛЕННЯМ
        for row in self.tree.get_children():
            self.tree.delete(row)

        history = DatabaseManager.get_all_grades_history()
        for record in history:
            formatted_date = record[4].strftime("%Y-%m-%d %H:%M:%S") if record[4] else ""
            self.tree.insert("", "end", values=(record[0], record[1], record[2], record[3], formatted_date))

    # ЗАВАНТАЖЕННЯ ДАНИХ MONGODB
    def load_mongo_data(self):
        self.text_mongo.config(state='normal')
        self.text_mongo.delete(1.0, tk.END)

        try:
            docs = DatabaseManager.get_mongo_course_profiles()

            if not docs:
                self.text_mongo.insert(tk.END, "Колекція порожня.")
            else:
                for count, doc in enumerate(docs, start=1):
                    formatted_doc = json.dumps(doc, indent=4, default=str, ensure_ascii=False)
                    self.text_mongo.insert(tk.END, f"ДОКУМЕНТ #{count}\n")
                    self.text_mongo.insert(tk.END, formatted_doc + "\n\n")

        except Exception as e:
            self.text_mongo.insert(tk.END, f"Помилка отримання даних з MongoDB:\n{e}")
        finally:
            self.text_mongo.config(state='disabled')


# ТОЧКА ВХОДУ
if __name__ == "__main__":
    root = tk.Tk()
    app = GradebookApp(root)
    root.mainloop()