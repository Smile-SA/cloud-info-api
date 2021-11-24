from typing import Any

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


def setup_db(app: Any):
    """
    Set up the database.

    :app (Any) FLask App
    """
    db.init_app(app)


def create_table_product(table: str):
    """
    Create a table for storing product information in the database.

    :table (str) Table name
    """
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
