from sqlalchemy import Column, Float, String, Boolean, BigInteger, JSON, Numeric, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from model import database
Base = declarative_base()


class TurtleBase(Base):
    """Abstract DB model for all product tables"""
    __table_args__ = {'schema': 'turtle_strategy'}
    __abstract__ = True


class Order(TurtleBase):
    __tablename__ = 'orders'

    id = Column(String, primary_key=True)
    trade_id = Column(String)
    client_order_id = Column(String, index=True)
    timestamp = Column(BigInteger)
    datetime = Column(String)
    last_trade_timestamp = Column(BigInteger)
    last_update_timestamp = Column(BigInteger)
    symbol = Column(String)
    type = Column(String)
    time_in_force = Column(String)
    post_only = Column(Boolean)
    reduce_only = Column(Boolean)
    side = Column(String)
    price = Column(Float)
    trigger_price = Column(Float)
    amount = Column(Float)
    cost = Column(Float)
    average = Column(Float)
    filled = Column(Float)
    remaining = Column(Float)
    status = Column(String)
    fee = Column(JSON)
    trades = Column(JSON)
    fees = Column(JSON)
    stop_price = Column(Float)
    take_profit_price = Column(Float)
    stop_loss_price = Column(Float)
    info = Column(JSON)

    atr = Column(Numeric)
    position_status = Column(String)
    action = Column(String)
    closed_positions = Column(ARRAY(String))
    free_balance = Column(Float)
    total_balance = Column(Float)
    pl = Column(Float)
    pl_percent = Column(Float)


if __name__ == '__main__':
    Base.metadata.create_all(database.engine)
