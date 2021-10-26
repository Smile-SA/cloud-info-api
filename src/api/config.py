class Config(object):
    TESTING = False


class ProductionConfig(Config):
    # SQLALCHEMY_DATABASE_URI = os.environ('POSTGRES_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
