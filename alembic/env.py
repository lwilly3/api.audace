from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# importation de la base de donee 10h36 modification a 10h42
# from app.db.database import metadata

from app.config.config import settings
from app.models.model_user import Base as Base__models 

# Charger les modèles de votre projet
target_metadata =  Base__models.metadata
# from app.models.table_models import Base as TableBase
# from app.models.mediaLib_models import Base as MediaLibBase
# target_metadata = [
#     Base_table_models.metadata, 
#     Base_model_invite.metadata,
#     Base_model_audit_log.metadata ,
#     Base_model_presenter.metadata ,
#     Base_model_programme.metadata ,
#     Base_model_programme_invite.metadata ,
#     Base_model_programme_status.metadata ,
#     Base_model_show_plan.metadata ,
#     Base_model_skill.metadata
    
    
#     ]

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
# 10h39
config.set_main_option("sqlalchemy.url",f"postgresql+psycopg2://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
    # 10h36
# target_metadata = Base.metadata
# Ajouter les métadonnées pour Alembic
# target_metadata = [TableBase.metadata, MediaLibBase.metadata]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
