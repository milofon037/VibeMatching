class CreateCustomers < ActiveRecord::Migration[7.0]
  def change
    create_table :customers, if_not_exists: true do |t|
      t.string :first_name, null: false
      t.string :last_name, null: false
      t.string :email, null: false, index: { unique: true, if_not_exists: true } 
      t.timestamps
    end
  end
end
