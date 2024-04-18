from cd_data.database.adapters.postgresql import PostgresqlAdapter

database = PostgresqlAdapter.from_env_vars()
