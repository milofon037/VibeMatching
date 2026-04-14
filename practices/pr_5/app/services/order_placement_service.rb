# Сценарий 1: Размещение заказа с позициями
class OrderPlacementService
  # Создание заказа с позициями в одной атомарной транзакции
  # 
  # @param customer_id [Integer] ID покупателя
  # @param items [Array<Hash>] Массив позиций с ключами:
  #   - product_id [Integer] ID продукта
  #   - quantity [Integer] Количество товара
  # @return [Order] Созданный заказ
  # @raise [ActiveRecord::RecordInvalid] Если данные невалидны
  def self.place_order(customer_id, items)
    ActiveRecord::Base.transaction do
      # 1. Создаём новую запись заказа
      order = Order.create!(
        customer_id: customer_id,
        order_date: Time.current,
        total_amount: 0
      )

      # 2. Добавляем позиции заказа в таблицу OrderItems
      total = 0
      items.each do |item|
        product = Product.find(item[:product_id])
        subtotal = product.price * item[:quantity]
        
        OrderItem.create!(
          order_id: order.id,
          product_id: product.id,
          quantity: item[:quantity],
          subtotal: subtotal
        )
        
        total += subtotal
      end

      # 3. Обновляем общую сумму заказа на основе суммы промежуточных итогов
      order.update!(total_amount: total)
      order.reload
    end
  end
end
