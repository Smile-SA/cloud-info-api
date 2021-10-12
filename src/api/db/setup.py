from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


def setup_db(app):
    db.init_app(app)


def create_table_product(table):
    query = f"""
    CREATE TABLE IF NOT EXISTS {table} (
      "productHash" text,
      "sku" text NOT NULL,
      "vendorName" text NOT NULL,
      "region" text,
      "service" text NOT NULL,
      "productFamily" text NOT NULL,
      "attributes" jsonb NOT NULL,
      "prices" jsonb NOT NULL,
      CONSTRAINT {table}_key PRIMARY KEY("productHash")
    );
    """

    db.engine.execute(query)
