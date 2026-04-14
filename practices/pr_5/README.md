# Практическое задание: Online Store Transactions
Рассмотрим упрощенную схему базы данных для интернет-магазина со следующими таблицами: 
```Customers (CustomerID, FirstName, LastName, Email)
Products (ProductID, ProductName, Price)
Orders (OrderID, CustomerID, OrderDate, TotalAmount)
OrderItems (OrderItemID, OrderID, ProductID, Quantity, Subtotal)
```
## Задача - написать транзакции SQL для реализации следующих сценариев:

### Сценарий 1: 
Напишите транзакцию, имитирующую размещение заказа. В заказе должны быть указаны:
1. Новая запись о заказе в таблице Orders.
2. Позиции заказа добавлены в таблицу OrderItems с соответствующими количествами и промежуточными итогами.
3. Обновите общую сумму в таблице «Заказы» на основе суммы промежуточных итогов по позициям заказа. 
### Сценарий 2:
Напишите транзакцию, которая обновляет адрес электронной почты клиента в таблице «Клиенты». Убедитесь, что обновление является атомарным и не вызывает несоответствий. 
### Сценарий 3:
Напишите транзакцию, которая добавляет новый продукт в таблицу Products. Убедитесь, что добавление продукта является атомарным и не оставляет базу данных в inconsistent состоянии.

## Формат:
- Сервис на Ruby, ORM -  ActiveRecord из Ruby on Rails
- Dockerfile и Docker-compose файл под сервис, где будет подниматься сервис и postgresql

# Описание решения
## Структура проекта

```
pr_5/
├── Gemfile                              # Зависимости Ruby (Rails, PostgreSQL и т.д.)
├── Dockerfile                           # Конфигурация контейнера приложения
├── docker-compose.yml                   # Оркестрация контейнеров (приложение + БД)
├── Rakefile                             # Rake файл для задач (миграции, и т.д.)
├── run_examples.rb                      # Скрипт с примерами использования всех сценариев
├── config/
│   ├── application.rb                   # Конфигурация приложения Rails
│   ├── database.yml                     # Настройки подключения к БД
│   └── environment.rb                   # Инициализация окружения
├── app/
│   ├── models/
│   │   ├── application_record.rb        # Базовый класс для моделей
│   │   ├── customer.rb                  # Модель Customer
│   │   ├── product.rb                   # Модель Product
│   │   ├── order.rb                     # Модель Order
│   │   └── order_item.rb                # Модель OrderItem
│   └── services/
│       ├── order_placement_service.rb   # Сценарий 1 (размещение заказа)
│       ├── customer_email_update_service.rb  # Сценарий 2 (обновление email)
│       └── product_creation_service.rb  # Сценарий 3 (создание продукта)
└── db/
    └── migrate/
        ├── 001_create_customers.rb      # Миграция таблицы Customers
        ├── 002_create_products.rb       # Миграция таблицы Products
        ├── 003_create_orders.rb         # Миграция таблицы Orders
        └── 004_create_order_items.rb    # Миграция таблицы OrderItems
```

## Реализация сценариев

### Сценарий 1: Размещение заказа (Order Placement)

**Файл:** `app/services/order_placement_service.rb`

**Описание:** Размещение заказа включает три операции, выполняемые в единой атомарной транзакции:

1. Создание новой записи заказа в таблице `Orders`
2. Добавление позиций заказа в таблицу `OrderItems` с вычислением промежуточных итогов
3. Обновление общей суммы заказа на основе суммы всех промежуточных итогов

**Ключевая особенность:** Использование `ActiveRecord::Base.transaction` обеспечивает ACID-гарантии:
- **Atomicity:** Либо все операции выполнены, либо ни одна
- **Consistency:** Сумма в Orders всегда соответствует сумме OrderItems
- **Isolation:** Изменения видны другим транзакциям только после коммита
- **Durability:** После коммита данные сохранены в БД

```ruby
ActiveRecord::Base.transaction do
  # 1. Создание заказа
  order = Order.create!(customer_id: customer_id, order_date: Time.current, total_amount: 0)
  
  # 2. Добавление позиций
  items.each do |item|
    OrderItem.create!(...)
  end
  
  # 3. Обновление суммы
  order.update!(total_amount: total)
end
```

### Сценарий 2: Обновление адреса электронной почты

**Файл:** `app/services/customer_email_update_service.rb`

**Описание:** Обновление email клиента в единой атомарной транзакции.

**Ключевые особенности:**
- Валидация Email (уникальность) проверяется внутри транзакции
- Если Email уже используется другим клиентом, транзакция откатывается
- Использование `lock: true` предотвращает race conditions

```ruby
ActiveRecord::Base.transaction do
  customer = Customer.find(customer_id)
  customer.update!(email: new_email)  # Валидация и проверка уникальности
end
```

### Сценарий 3: Добавление нового продукта

**Файл:** `app/services/product_creation_service.rb`

**Описание:** Добавление нового продукта в таблицу `Products` в единой атомарной транзакции.

**Ключевые особенности:**
- Валидация цены (должна быть > 0) проверяется внутри транзакции
- Если валидация не пройдена, база остаётся в консистентном состоянии
- Никакие промежуточные состояния не видны другим клиентам

```ruby
ActiveRecord::Base.transaction do
  Product.create!(product_name: product_name, price: price)
end
```
