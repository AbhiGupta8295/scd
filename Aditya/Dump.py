version: "3.8"

services:
  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: vector_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com  # Default email for login
      PGADMIN_DEFAULT_PASSWORD: admin        # Default password
    ports:
      - "8080:80"  # Exposes pgAdmin on port 8080
    depends_on:
      - postgres

  backend:
    build:
      context: .
    depends_on:
      - postgres
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/vector_db

volumes:
  postgres_data:
