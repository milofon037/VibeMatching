#!/usr/bin/env ruby

require_relative 'config/environment'

puts "="*60
puts "Online Store Transactions - Примеры использования"
puts "="*60

begin
  # Сценарий 1: Размещение заказа
  puts "\n--- Сценарий 1: Размещение заказа ---"
  
  customer1 = Customer.create_or_find_by(
    email: "john@example.com"
  ) do |c|
    c.first_name = "John"
    c.last_name = "Doe"
  end
  puts "✓ Создан покупатель: #{customer1.first_name} #{customer1.last_name} (#{customer1.email})"

  product1 = Product.create_or_find_by(
    product_name: "Laptop"
  ) do |p|
    p.price = 999.99
  end
  puts "✓ Создан продукт: #{product1.product_name} (#{product1.price})"

  product2 = Product.create_or_find_by(
    product_name: "Mouse"
  ) do |p|
    p.price = 29.99
  end
  puts "✓ Создан продукт: #{product2.product_name} (#{product2.price})"

  # Размещаем заказ с использованием транзакции
  order = OrderPlacementService.place_order(
    customer1.id,
    [
      { product_id: product1.id, quantity: 1 },
      { product_id: product2.id, quantity: 2 }
    ]
  )
  puts "✓ Заказ размещен:"
  puts "  - ID заказа: #{order.id}"
  puts "  - Дата: #{order.order_date}"
  puts "  - Общая сумма: #{order.total_amount}"
  puts "  - Позиции:"
  order.order_items.each do |item|
    puts "    * #{item.product.product_name} x#{item.quantity} = #{item.subtotal}"
  end

  # Сценарий 2: Обновление адреса электронной почты
  puts "\n--- Сценарий 2: Обновление адреса электронной почты ---"
  
  old_email = customer1.email
  new_email = "john.doe@example.com"
  
  updated_customer = CustomerEmailUpdateService.update_email(customer1.id, new_email)
  puts "✓ Email обновлен (атомарно):"
  puts "  - Старый email: #{old_email}"
  puts "  - Новый email: #{updated_customer.email}"

  # Сценарий 3: Добавление нового продукта
  puts "\n--- Сценарий 3: Добавление нового продукта ---"
  
  new_product = ProductCreationService.create_product("Keyboard", 79.99)
  puts "✓ Новый продукт добавлен (атомарно):"
  puts "  - ID: #{new_product.id}"
  puts "  - Название: #{new_product.product_name}"
  puts "  - Цена: #{new_product.price}"

  puts "\n" + "="*60
  puts "Все сценарии выполнены успешно!"
  puts "="*60

rescue => e
  puts "\n❌ Ошибка: #{e.message}"
  puts e.backtrace.join("\n")
end
