require "rails"

require "active_record/railtie"

# Load all gems from the Gemfile
Bundler.require(*Rails.groups)

module OnlineStore
  class Application < Rails::Application
    config.load_defaults 7.0
    config.autoload_paths << "#{config.root}/app"
  end
end

Rails.application.initialize!
