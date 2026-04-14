ENV['RAILS_ENV'] ||= 'development'

require_relative 'application'

# Load config/database.yml
require 'yaml'
require 'erb'

database_config = YAML.safe_load(
  ERB.new(File.read(File.expand_path('../database.yml', __FILE__))).result,
  aliases: true
)
ActiveRecord::Base.establish_connection(database_config[ENV['RAILS_ENV']])
