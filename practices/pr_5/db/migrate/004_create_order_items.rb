class CreateOrderItems < ActiveRecord::Migration[7.0]
  def change
    create_table :order_items, if_not_exists: true do |t|
      t.references :order, null: false, foreign_key: true
      t.references :product, null: false, foreign_key: true
      t.integer :quantity, null: false
      t.decimal :subtotal, precision: 10, scale: 2, null: false
      t.timestamps
    end

    unless index_exists?(:order_items, [:order_id, :product_id])
      add_index :order_items, [:order_id, :product_id]
    end
  end
end
