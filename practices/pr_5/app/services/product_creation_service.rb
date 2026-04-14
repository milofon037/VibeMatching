# Сценарий 3: Добавление нового продукта
class ProductCreationService
  # Добавление нового продукта в одной атомарной транзакции
  # Обеспечивает консистентность данных и отсутствие промежуточных состояний
  #
  # @param product_name [String] Название продукта
  # @param price [Decimal] Цена продукта
  # @return [Product] Созданный продукт
  # @raise [ActiveRecord::RecordInvalid] Если данные невалидны
  def self.create_product(product_name, price)
    ActiveRecord::Base.transaction do
      product = Product.create!(
        product_name: product_name,
        price: price
      )
      
      product.reload
    end
  end
end
