class CreateOrders < ActiveRecord::Migration[7.0]
  def change
    create_table :orders, if_not_exists: true do |t|
      t.references :customer, null: false, foreign_key: true, index: { if_not_exists: true } 
      t.datetime :order_date, null: false
      t.decimal :total_amount, precision: 10, scale: 2, null: false, default: 0
      t.timestamps
    end
  end
end
