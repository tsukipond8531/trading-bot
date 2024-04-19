from database_tools.adapters.postgresql import PostgresqlAdapter

trader_database = PostgresqlAdapter.from_env_vars()
