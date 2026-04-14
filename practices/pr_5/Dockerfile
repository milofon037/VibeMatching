FROM ruby:3.2-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY Gemfile Gemfile.lock* ./

RUN bundle install --jobs 4 --retry 3

COPY . .

RUN mkdir -p log tmp

ENV RAILS_ENV=production
ENV RACK_ENV=production
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres

CMD ["sh", "-c", "bundle exec rake db:prepare && bundle exec ruby run_examples.rb"]
