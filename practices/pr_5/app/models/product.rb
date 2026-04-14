class Product < ApplicationRecord
  has_many :order_items, dependent: :destroy
  
  validates :product_name, presence: true
  validates :price, presence: true, numericality: { greater_than: 0 }
end
