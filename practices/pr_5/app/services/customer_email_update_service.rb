# Сценарий 2: Обновление адреса электронной почты клиента
class CustomerEmailUpdateService
  # Обновление адреса электронной почты в одной атомарной транзакции
  # Обеспечивает консистентность данных
  #
  # @param customer_id [Integer] ID клиента
  # @param new_email [String] Новый адрес электронной почты
  # @return [Customer] Обновленный клиент
  # @raise [ActiveRecord::RecordNotFound] Если клиент не найден
  # @raise [ActiveRecord::RecordInvalid] Если объект уже использует новый email
  def self.update_email(customer_id, new_email)
    ActiveRecord::Base.transaction do
      customer = Customer.find(customer_id)
      
      # Проверка валидности и уникальности email внутри транзакции
      customer.update!(email: new_email)
      
      customer.reload
    end
  end
end
