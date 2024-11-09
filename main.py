import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Toplevel
import sqlite3

from unicodedata import category


class Database:
    def __init__(self):
        self.connection = sqlite3.connect("restaurant.db")
        self.cursor = self.connection.cursor()
        self.create_tables()
        self.setup_initial_users()

    def create_tables(self):
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')

        # Таблица для блюд
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS dishes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    ingredients TEXT,
                    price REAL NOT NULL,
                    category TEXT
                )
            ''')

        # Таблица для бронирований
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT NOT NULL,
                    reservation_date TEXT NOT NULL,
                    number_of_guests INTEGER NOT NULL,
                    table_number INTEGER NOT NULL
                )
            ''')

        # Таблица для персонала
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS staff (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    position TEXT NOT NULL,
                    salary REAL NOT NULL,
                    hire_date TEXT NOT NULL
                )
            ''')

        # Таблица для остатков продуктов
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit TEXT NOT NULL
                )
            ''')
        self.connection.commit()

    def setup_initial_users(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        count = self.cursor.fetchone()[0]
        if count == 0:
            # Добавляем админа и обычного пользователя
            self.add_user("admin", "admin", "admin")
            self.add_user("user", "user", "user")

    def add_user(self, username, password, role):
        self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        self.connection.commit()

    def fetch_user(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return self.cursor.fetchone()

    def fetch_all(self, table_name):
        self.cursor.execute(f"SELECT * FROM {table_name}")
        return self.cursor.fetchall()

    def add_record(self, table_name, record):
        self.cursor.execute(f"INSERT INTO {table_name} VALUES (NULL, {','.join('?' * len(record))})", record)
        self.connection.commit()

    def update_record(self, table_name, record):
        record_id = record.pop('id')
        set_clause = ', '.join([f"{key}=?" for key in record.keys()])
        self.cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id=?", (*record.values(), record_id))
        self.connection.commit()

    def delete_record(self, table_name, record_id):
        self.cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (record_id,))
        self.connection.commit()

    def fetch_all_dishes(self, order_by="id", ascending=True, category_filter=None):
        order = "ASC" if ascending else "DESC"
        if category_filter:
            placeholders = ', '.join('?' for _ in category_filter)
            query = f"SELECT * FROM dishes WHERE category IN ({placeholders}) ORDER BY {order_by} {order}"
            self.cursor.execute(query, category_filter)
        else:
            query = f"SELECT * FROM dishes ORDER BY {order_by} {order}"
            self.cursor.execute(query)

        return self.cursor.fetchall()

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Вход")
        self.master.geometry("300x200")

        self.db = Database()

        tk.Label(master, text="Имя пользователя:").pack(pady=5)
        self.username_entry = tk.Entry(master)
        self.username_entry.pack(pady=5)

        tk.Label(master, text="Пароль:").pack(pady=5)
        self.password_entry = tk.Entry(master, show='*')
        self.password_entry.pack(pady=5)

        self.show_password_var = tk.BooleanVar()
        self.show_password_button = tk.Checkbutton(self.master, text="Показать пароль", variable=self.show_password_var,
                                                   command=self.toggle_password)
        self.show_password_button.pack()

        tk.Button(master, text="Войти", command=self.login).pack(pady=5)

    def toggle_password(self):
        self.password_entry.config(show='' if self.show_password_var.get() else '*')

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = self.db.fetch_user(username, password)

        if user:
            self.master.destroy()
            self.open_main_window(user[3])
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    def open_main_window(self, role):
        self.main_window = RestaurantApp(role)

class RestaurantApp:
    def __init__(self, user_role):
        self.user_role = user_role
        self.db = Database()

        self.window = tk.Tk()
        self.window.title("Управление Рестораном")
        self.window.geometry("600x400")

        self.tab_control = ttk.Notebook(self.window)

        # Вкладки для управления
        self.tab_dishes = ttk.Frame(self.tab_control)
        self.tab_reservations = ttk.Frame(self.tab_control)
        self.tab_ingredients = ttk.Frame(self.tab_control)
        self.tab_staff = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_dishes, text='Блюда')
        self.tab_control.add(self.tab_reservations, text='Резервации')
        self.tab_control.add(self.tab_ingredients, text='Остатки Ингредиентов')
        self.tab_control.add(self.tab_staff, text='Персонал')

        self.tab_control.pack(expand=1, fill='both')

        self.sort_order = {"id": True, "name": True, "price": True, "category": True}
        self.category_filter = None
        # Список допустимых категорий
        self.valid_categories = ["Закуска", "Супы", "Основное блюдо", "Десерты", "Напитки"]
        self.selected_categories = {category: True for category in self.valid_categories}

        self.setup_dishes_tab()
        self.setup_reservations_tab()
        self.setup_ingredients_tab()
        self.setup_staff_tab()

        self.window.mainloop()


    def setup_dishes_tab(self):
        # Таблица для блюд
        self.dishes_tree = ttk.Treeview(self.tab_dishes,
                                        columns=("ID", "Name", "Description", "Ingredients", "Price", "Category"),
                                        show='headings')
        self.dishes_tree.heading("ID", text="ID", command=lambda: self.sort_by("id"))
        self.dishes_tree.heading("Name", text="Название", command=lambda: self.sort_by("name"))
        self.dishes_tree.heading("Description", text="Описание")
        self.dishes_tree.heading("Ingredients", text="Ингредиенты")
        self.dishes_tree.heading("Price", text="Цена", command=lambda: self.sort_by("price"))
        self.dishes_tree.heading("Category", text="Категория", command=lambda: self.sort_by("category"))
        self.dishes_tree.pack(expand=True, fill='both')

        # Панель управления
        self.refresh_button = tk.Button(self.window, text="Обновить список", command=self.refresh_dishes)
        self.refresh_button.pack(side=tk.LEFT)

        # Кнопка для выхода
        self.exit_button = tk.Button(self.window, text="Выход", command=self.window.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Кнопка для выбора категорий
        self.category_button = tk.Button(self.window, text="Выбрать категории", command=self.open_category_selection)
        self.category_button.pack(side=tk.LEFT)

        self.refresh_dishes()

        # Кнопки для блюд
        button_frame = tk.Frame(self.tab_dishes)
        button_frame.pack(pady=5)

        if self.user_role == "admin":
            tk.Button(button_frame, text="Добавить", command=self.open_add_dish_window).pack(side="left")
            tk.Button(button_frame, text="Редактировать", command=self.open_edit_dish_window).pack(side="left")
            tk.Button(button_frame, text="Удалить", command=self.delete_dish).pack(side="left")  # Исправленная строка

        self.load_dishes()

    def load_dishes(self):
        for record in self.dishes_tree.get_children():
            self.dishes_tree.delete(record)
        for row in self.db.fetch_all("dishes"):
            self.dishes_tree.insert("", "end", values=row)

    def delete_dish(self):
        selected_item = self.dishes_tree.selection()
        if not selected_item:
            print("Не выбрано ни одного блюда для удаления.")
            return

        # Получаем ID выбранного блюда
        dish_id = self.dishes_tree.item(selected_item)["values"][0]

        # Подтверждение удаления
        confirm = tk.messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить выбранное блюдо?")
        if confirm:
            # Удаление записи из базы данных
            self.db.delete_record("dishes", dish_id)
            # Обновление списка блюд
            self.load_dishes()
            print(f"Блюдо с ID {dish_id} удалено.")

    def open_add_dish_window(self):
        self.open_dish_window("Добавить Блюдо")

    def open_category_selection(self):
        category_selection_window = CategorySelectionWindow(self)

    def open_edit_dish_window(self):
        selected_item = self.dishes_tree.selection()
        if selected_item:
            dish_id = self.dishes_tree.item(selected_item)["values"][0]
            self.open_dish_window("Редактировать Блюдо", dish_id)

    def open_dish_window(self, title, dish_id=None):
        window = Toplevel(self.window)
        window.title(title)
        window.geometry("300x200")

        # Название
        tk.Label(window, text="Название:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        name_entry = tk.Entry(window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Описание
        tk.Label(window, text="Описание:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        description_entry = tk.Entry(window, width=30)
        description_entry.grid(row=1, column=1, padx=5, pady=5)

        # Ингредиенты
        tk.Label(window, text="Ингредиенты:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ingredients_entry = tk.Entry(window, width=30)
        ingredients_entry.grid(row=2, column=1, padx=5, pady=5)

        # Цена
        tk.Label(window, text="Цена:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        price_entry = tk.Entry(window, width=30)
        price_entry.grid(row=3, column=1, padx=5, pady=5)

        # Категория
        tk.Label(window, text="Категория:").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        category_entry = tk.Entry(window, width=30)
        category_entry.grid(row=4, column=1, padx=5, pady=5)

        if dish_id:
            dish_data = self.db.cursor.execute("SELECT * FROM dishes WHERE id=?", (dish_id,)).fetchone()
            name_entry.insert(0, dish_data[1])
            description_entry.insert(0, dish_data[2])
            ingredients_entry.insert(0, dish_data[3])
            price_entry.insert(0, dish_data[4])
            category_entry.insert(0, dish_data[5])

        save_button = tk.Button(window, text="Сохранить", command=lambda: self.save_dish(dish_id, name_entry.get(), description_entry.get(), ingredients_entry.get(), price_entry.get(), category_entry.get()))
        save_button.grid(row=5, column=0, columnspan=2, pady=10)

    def save_dish(self, dish_id, name, description, ingredients, price, category):
        if dish_id:
            self.db.update_record("dishes",
                                  {'id': dish_id, 'name': name, 'description': description, 'ingredients': ingredients,
                                   'price': price, 'category': category})
        else:
            self.db.add_record("dishes", (name, description, ingredients, price, category))
        self.load_dishes()

    # Здесь также должны быть другие методы класса RestaurantApp для работы с другими вкладками, как в оригинальном коде

    def save_dish(self, dish_id, name, description, ingredients, price, category):
        if dish_id:
            self.db.update_record("dishes", {'id': dish_id, 'name': name, 'description': description, 'ingredients': ingredients, 'price': price, 'category': category})
        else:
            self.db.add_record("dishes", (name, description, ingredients, price, category))
        self.load_dishes()

    def refresh_dishes(self):
        if self.selected_categories:
            category_filter = [category for category, selected in self.selected_categories.items() if selected]
            if category_filter:
                dishes = self.db.fetch_all_dishes(category_filter=category_filter)
                self.display_dishes(dishes)
            else:
                self.display_dishes([])
        else:
            dishes = self.db.fetch_all_dishes()
            self.display_dishes(dishes)

    def sort_by(self, column):
        self.sort_order[column] = not self.sort_order[column]
        dishes = self.db.fetch_all_dishes(order_by=column, ascending=self.sort_order[column],
                                          category_filter=[category for category, selected in
                                                           self.selected_categories.items() if selected])
        self.display_dishes(dishes)

    def display_dishes(self, dishes):
        for i in self.dishes_tree.get_children():
            self.dishes_tree.delete(i)

        for dish in dishes:
            self.dishes_tree.insert("", "end", values=dish)

    def delete_dish(self):
        selected_item = self.dishes_tree.selection()
        if not selected_item:
            print("Не выбрано ни одного блюда для удаления.")
            return

        # Получаем ID выбранного блюда
        dish_id = self.dishes_tree.item(selected_item)["values"][0]

        # Подтверждение удаления
        confirm = tk.messagebox.askyesno("Удаление", "Вы уверены, что хотите удалить выбранное блюдо?")
        if confirm:
            # Удаление записи из базы данных
            self.db.delete_record("dishes", dish_id)
            # Обновление списка блюд
            self.load_dishes()
            print(f"Блюдо с ID {dish_id} удалено.")

    def setup_reservations_tab(self):
        # Таблица для бронирований
        self.reservations_tree = ttk.Treeview(self.tab_reservations, columns=("ID", "Customer Name", "Reservation Date", "Guests", "Table Number"), show='headings')
        self.reservations_tree.heading("ID", text="ID")
        self.reservations_tree.heading("Customer Name", text="Имя клиента")
        self.reservations_tree.heading("Reservation Date", text="Дата бронирования")
        self.reservations_tree.heading("Guests", text="Количество гостей")
        self.reservations_tree.heading("Table Number", text="Номер стола")
        self.reservations_tree.pack(expand=True, fill='both')

        # Кнопки для бронирований
        button_frame = tk.Frame(self.tab_reservations)
        button_frame.pack(pady=5)

        if self.user_role == "admin":
            tk.Button(button_frame, text="Добавить", command=self.open_add_reservation_window).pack(side="left")
            tk.Button(button_frame, text="Редактировать", command=self.open_edit_reservation_window).pack(side="left")
            tk.Button(button_frame, text="Удалить", command=self.delete_reservation).pack(side="left")

        self.load_reservations()

    def load_reservations(self):
        for record in self.reservations_tree.get_children():
            self.reservations_tree.delete(record)
        for row in self.db.fetch_all("reservations"):
            self.reservations_tree.insert("", "end", values=row)

    def open_add_reservation_window(self):
        self.open_reservation_window("Добавить Бронирование")

    def open_edit_reservation_window(self):
        selected_item = self.reservations_tree.selection()
        if selected_item:
            reservation_id = self.reservations_tree.item(selected_item)["values"][0]
            self.open_reservation_window("Редактировать Бронирование", reservation_id)

    def open_reservation_window(self, title, reservation_id=None):
        window = Toplevel(self.window)
        window.title(title)
        window.geometry("300x250")

        tk.Label(window, text="Имя клиента:").pack(pady=5)
        customer_name_entry = tk.Entry(window)
        customer_name_entry.pack(pady=5)

        tk.Label(window, text="Дата бронирования:").pack(pady=5)
        reservation_date_entry = tk.Entry(window)
        reservation_date_entry.pack(pady=5)

        tk.Label(window, text="Количество гостей:").pack(pady=5)
        guests_entry = tk.Entry(window)
        guests_entry.pack(pady=5)

        tk.Label(window, text="Номер стола:").pack(pady=5)
        table_number_entry = tk.Entry(window)
        table_number_entry.pack(pady=5)

        if reservation_id:
            reservation_data = self.db.cursor.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
            customer_name_entry.insert(0, reservation_data[1])
            reservation_date_entry.insert(0, reservation_data[2])
            guests_entry.insert(0, reservation_data[3])
            table_number_entry.insert(0, reservation_data[4])

        save_button = tk.Button(window, text="Сохранить", command=lambda: self.save_reservation(reservation_id, customer_name_entry.get(), reservation_date_entry.get(), guests_entry.get(), table_number_entry.get()))
        save_button.pack(pady=5)

    def save_reservation(self, reservation_id, customer_name, reservation_date, guests, table_number):
        if reservation_id:
            self.db.update_record("reservations", {'id': reservation_id, 'customer_name': customer_name, 'reservation_date': reservation_date, 'number_of_guests': guests, 'table_number': table_number})
        else:
            self.db.add_record("reservations", (customer_name, reservation_date, guests, table_number))
        self.load_reservations()

    def delete_reservation(self):
        selected_item = self.reservations_tree.selection()
        if selected_item:
            reservation_id = self.reservations_tree.item(selected_item)["values"][0]
            self.db.delete_record("reservations", reservation_id)
            self.load_reservations()

    def setup_ingredients_tab(self):
        # Таблица для остатков ингредиентов
        self.ingredients_tree = ttk.Treeview(self.tab_ingredients, columns=("ID", "Name", "Quantity", "Unit"), show='headings')
        self.ingredients_tree.heading("ID", text="ID")
        self.ingredients_tree.heading("Name", text="Название")
        self.ingredients_tree.heading("Quantity", text="Количество")
        self.ingredients_tree.heading("Unit", text="Единица измерения")
        self.ingredients_tree.pack(expand=True, fill='both')

        # Кнопки для остатков
        button_frame = tk.Frame(self.tab_ingredients)
        button_frame.pack(pady=5)

        if self.user_role == "admin":
            tk.Button(button_frame, text="Добавить", command=self.open_add_ingredient_window).pack(side="left")
            tk.Button(button_frame, text="Редактировать", command=self.open_edit_ingredient_window).pack(side="left")
            tk.Button(button_frame, text="Удалить", command=self.delete_ingredient).pack(side="left")

        self.load_ingredients()

    def load_ingredients(self):
        for record in self.ingredients_tree.get_children():
            self.ingredients_tree.delete(record)
        for row in self.db.fetch_all("ingredients"):
            self.ingredients_tree.insert("", "end", values=row)

    def open_add_ingredient_window(self):
        self.open_ingredient_window("Добавить Ингредиент")

    def open_edit_ingredient_window(self):
        selected_item = self.ingredients_tree.selection()
        if selected_item:
            ingredient_id = self.ingredients_tree.item(selected_item)["values"][0]
            self.open_ingredient_window("Редактировать Ингредиент", ingredient_id)

    def open_ingredient_window(self, title, ingredient_id=None):
        window = Toplevel(self.window)
        window.title(title)
        window.geometry("300x200")

        tk.Label(window, text="Название:").pack(pady=5)
        name_entry = tk.Entry(window)
        name_entry.pack(pady=5)

        tk.Label(window, text="Количество:").pack(pady=5)
        quantity_entry = tk.Entry(window)
        quantity_entry.pack(pady=5)

        tk.Label(window, text="Единица измерения:").pack(pady=5)
        unit_entry = tk.Entry(window)
        unit_entry.pack(pady=5)

        if ingredient_id:
            ingredient_data = self.db.cursor.execute("SELECT * FROM ingredients WHERE id=?", (ingredient_id,)).fetchone()
            name_entry.insert(0, ingredient_data[1])
            quantity_entry.insert(0, ingredient_data[2])
            unit_entry.insert(0, ingredient_data[3])

        save_button = tk.Button(window, text="Сохранить", command=lambda: self.save_ingredient(ingredient_id, name_entry.get(), quantity_entry.get(), unit_entry.get()))
        save_button.pack(pady=5)

    def save_ingredient(self, ingredient_id, name, quantity, unit):
        if ingredient_id:
            self.db.update_record("ingredients", {'id': ingredient_id, 'name': name, 'quantity': quantity, 'unit': unit})
        else:
            self.db.add_record("ingredients", (name, quantity, unit))
        self.load_ingredients()

    def delete_ingredient(self):
        selected_item = self.ingredients_tree.selection()
        if selected_item:
            ingredient_id = self.ingredients_tree.item(selected_item)["values"][0]
            self.db.delete_record("ingredients", ingredient_id)
            self.load_ingredients()

    def setup_staff_tab(self):
        # Таблица для персонала
        self.staff_tree = ttk.Treeview(self.tab_staff, columns=("ID", "Name", "Position", "Salary", "Hire Date"), show='headings')
        self.staff_tree.heading("ID", text="ID")
        self.staff_tree.heading("Name", text="Имя")
        self.staff_tree.heading("Position", text="Должность")
        self.staff_tree.heading("Salary", text="Зарплата")
        self.staff_tree.heading("Hire Date", text="Дата приема на работу")
        self.staff_tree.pack(expand=True, fill='both')

        # Кнопки для персонала
        button_frame = tk.Frame(self.tab_staff)
        button_frame.pack(pady=5)

        if self.user_role == "admin":
            tk.Button(button_frame, text="Добавить", command=self.open_add_staff_window).pack(side="left")
            tk.Button(button_frame, text="Редактировать", command=self.open_edit_staff_window).pack(side="left")
            tk.Button(button_frame, text="Удалить", command=self.delete_staff).pack(side="left")

        self.load_staff()

    def load_staff(self):
        for record in self.staff_tree.get_children():
            self.staff_tree.delete(record)
        for row in self.db.fetch_all("staff"):
            self.staff_tree.insert("", "end", values=row)

    def open_add_staff_window(self):
        self.open_staff_window("Добавить Персонал")

    def open_edit_staff_window(self):
        selected_item = self.staff_tree.selection()
        if selected_item:
            staff_id = self.staff_tree.item(selected_item)["values"][0]
            self.open_staff_window("Редактировать Персонал", staff_id)

    def open_staff_window(self, title, staff_id=None):
        window = Toplevel(self.window)
        window.title(title)
        window.geometry("300x250")

        tk.Label(window, text="Имя:").pack(pady=5)
        name_entry = tk.Entry(window)
        name_entry.pack(pady=5)

        tk.Label(window, text="Должность:").pack(pady=5)
        position_entry = tk.Entry(window)
        position_entry.pack(pady=5)

        tk.Label(window, text="Зарплата:").pack(pady=5)
        salary_entry = tk.Entry(window)
        salary_entry.pack(pady=5)

        tk.Label(window, text="Дата приема на работу:").pack(pady=5)
        hire_date_entry = tk.Entry(window)
        hire_date_entry.pack(pady=5)

        if staff_id:
            staff_data = self.db.cursor.execute("SELECT * FROM staff WHERE id=?", (staff_id,)).fetchone()
            name_entry.insert(0, staff_data[1])
            position_entry.insert(0, staff_data[2])
            salary_entry.insert(0, staff_data[3])
            hire_date_entry.insert(0, staff_data[4])

        save_button = tk.Button(window, text="Сохранить", command=lambda: self.save_staff(staff_id, name_entry.get(), position_entry.get(), salary_entry.get(), hire_date_entry.get()))
        save_button.pack(pady=5)

    def save_staff(self, staff_id, name, position, salary, hire_date):
        if staff_id:
            self.db.update_record("staff", {'id': staff_id, 'name': name, 'position': position, 'salary': salary, 'hire_date': hire_date})
        else:
            self.db.add_record("staff", (name, position, salary, hire_date))
        self.load_staff()

    def delete_staff(self):
        selected_item = self.staff_tree.selection()
        if selected_item:
            staff_id = self.staff_tree.item(selected_item)["values"][0]
            self.db.delete_record("staff", staff_id)
            self.load_staff()

class CategorySelectionWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent.window)  # Инициализация окна выбора категорий
        self.parent = parent
        self.title("Выбор категории")
        self.geometry("300x200")

        # Флажки для выбора категорий
        self.check_buttons = {}
        for category in parent.valid_categories:
            var = tk.BooleanVar(value=parent.selected_categories[category])
            chk = tk.Checkbutton(self, text=category, variable=var)
            chk.pack(anchor="w")
            self.check_buttons[category] = var

        # Создаем Frame для кнопок
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        # Кнопка для подтверждения выбора
        confirm_button = tk.Button(self, text="Применить", command=self.apply_selection)
        confirm_button.pack(side="right", padx=5)

        select_all_button = tk.Button(self, text="Выбрать все", command=self.select_all)
        select_all_button.pack(side="left", padx=5)

    def apply_selection(self):
        # Обновление выбора категорий в основном окне
        for category, var in self.check_buttons.items():
            self.parent.selected_categories[category] = var.get()
        self.parent.refresh_dishes()  # Обновление списка блюд
        self.destroy()  # Закрытие окна выбора категорий

    def select_all(self):
        # Установка всех флажков в True (выбор всех категорий)
        for var in self.check_buttons.values():
            var.set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)  # Замените "admin" на "user" для ограниченного доступа
    root.mainloop()
