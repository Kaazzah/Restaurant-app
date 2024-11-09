import sqlite3

def create_database():
    connection = sqlite3.connect("restaurant.db")
    cursor = connection.cursor()

    # Таблица для пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Таблица для блюд
    cursor.execute('''
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            reservation_date TEXT NOT NULL,
            number_of_guests INTEGER NOT NULL,
            table_number INTEGER NOT NULL
        )
    ''')

    # Таблица для персонала
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL
        )
    ''')

    # Таблица для остатков продуктов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL
        )
    ''')

    # Вставка тестовых данных для пользователей
    test_users = [
        ("admin", "admin", "admin"),
        ("user", "user", "user")
    ]
    cursor.executemany('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', test_users)

    # Вставка тестовых данных для блюд
    test_data = [
        ("Салат Цезарь", "Салат с курицей и пармезаном", "курица, пармезан, романо, соус Цезарь", 350.00, "Закуска"),
        ("Борщ", "Украинский суп с свеклой", "свекла, капуста, картофель, мясо", 250.00, "Супы"),
        ("Стейк", "Говяжий стейк с картофелем", "говядина, картофель, специи", 1200.00, "Основное блюдо"),
        ("Тирамису", "Итальянский десерт с кофе", "маскарпоне, кофе, бисквиты, какао", 400.00, "Десерты"),
        ("Пицца Маргарита", "Пицца с томатами и сыром", "томатный соус, моцарелла, базилик", 600.00, "Основное блюдо"),
        ("Спагетти", "Спагетти с томатным соусом", "спагетти, томаты, специи", 500.00, "Основное блюдо"),
        ("Фруктовый салат", "Салат из свежих фруктов", "яблоки, груши, бананы, виноград", 300.00, "Закуска"),
        ("Кофе", "Крепкий черный кофе", "кофейные зерна, вода", 150.00, "Напитки"),
        ("Чай", "Чай черный или зеленый", "чайные листья, вода", 100.00, "Напитки"),
        ("Морс", "Напиток из ягод", "ягоды, сахар, вода", 200.00, "Напитки"),
        ("Суп Минестроне", "Итальянский овощной суп", "овощи, паста, бульон", 300.00, "Супы"),
        ("Куриное филе", "Запеченное куриное филе", "куриное филе, специи", 600.00, "Основное блюдо"),
        ("Блинчики", "Блинчики с ягодами", "мука, яйца, ягоды", 350.00, "Десерты"),
        ("Огуречный салат", "Салат из свежих огурцов", "огурцы, укроп, сметана", 200.00, "Закуска"),
        ("Котлета по-киевски", "Куриная котлета с зеленью", "куриное мясо, зелень, панировка", 700.00, "Основное блюдо"),
        ("Крем-брюле", "Десерт с карамельной корочкой", "сливки, яйца, сахар", 400.00, "Десерты"),
        ("Лимонад", "Освежающий лимонад", "лимон, сахар, вода", 250.00, "Напитки"),
        ("Суп-пюре", "Суп из брокколи", "брокколи, сливки, специи", 300.00, "Супы"),
        ("Медовик", "Торт с медом", "мука, мед, яйца", 350.00, "Десерты"),
        ("Чизкейк", "Творожный десерт", "творог, сахар, яйца, печенье", 400.00, "Десерты")
    ]
    cursor.executemany('INSERT INTO dishes (name, description, ingredients, price, category) VALUES (?, ?, ?, ?, ?)', test_data)

    # Вставка тестовых данных для бронирований
    test_reservations = [
        ("Иван Иванов", "2024-11-10 19:00", 4, 1),
        ("Петр Петров", "2024-11-11 20:00", 2, 3),
        ("Светлана Сидорова", "2024-11-12 18:00", 3, 2),
        ("Анна Смирнова", "2024-11-13 17:30", 5, 4),
        ("Олег Сидоров", "2024-11-14 19:00", 1, 5),
        ("Елена Кузнецова", "2024-11-15 20:00", 6, 1)
    ]
    cursor.executemany('INSERT INTO reservations (customer_name, reservation_date, number_of_guests, table_number) VALUES (?, ?, ?, ?)', test_reservations)

    # Вставка тестовых данных для персонала
    test_staff = [
        ("Александр Смирнов", "Официант", 30000.00, "2023-01-15"),
        ("Мария Кузнецова", "Повар", 50000.00, "2022-05-10"),
        ("Екатерина Васильева", "Администратор", 40000.00, "2021-03-25"),
        ("Дмитрий Федоров", "Бариста", 35000.00, "2023-07-01"),
        ("Ирина Сергеева", "Уборщица", 20000.00, "2023-09-10"),
        ("Сергей Николаев", "Сомелье", 45000.00, "2020-11-20")
    ]
    cursor.executemany('INSERT INTO staff (name, position, salary, hire_date) VALUES (?, ?, ?, ?)', test_staff)

    # Вставка тестовых данных для остатков продуктов
    test_ingredients = [
        ("Курица", 50, "кг"),
        ("Говядина", 30, "кг"),
        ("Помидоры", 100, "кг"),
        ("Сыр", 20, "кг"),
        ("Яйца", 200, "шт"),
        ("Мука", 150, "кг"),
        ("Сахар", 100, "кг"),
        ("Ягоды", 50, "кг"),
        ("Зелень", 30, "пакетов"),
        ("Специи", 20, "банок")
    ]
    cursor.executemany('INSERT INTO ingredients (name, quantity, unit) VALUES (?, ?, ?)', test_ingredients)

    connection.commit()
    connection.close()

create_database()
