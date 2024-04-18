from cd_data.database.adapters.postgresql import PostgresqlAdapter

trader_database = PostgresqlAdapter.from_env_vars()
