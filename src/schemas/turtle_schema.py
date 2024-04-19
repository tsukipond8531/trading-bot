from marshmallow import Schema, fields, post_load

from src.model.turtle_model import Order


class OrderSchema(Schema):
    id = fields.Str()
    client_order_id = fields.Str(data_key="clientOrderId")
    timestamp = fields.Int()
    datetime = fields.Str()
    last_trade_timestamp = fields.Int(data_key="lastTradeTimestamp")
    last_update_timestamp = fields.Int(data_key="lastUpdateTimestamp")
    symbol = fields.Str()
    type = fields.Str()
    time_in_force = fields.Str(data_key="timeInForce")
    post_only = fields.Bool(data_key="postOnly")
    reduce_only = fields.Bool(data_key="reduceOnly")
    side = fields.Str()
    price = fields.Float()
    trigger_price = fields.Float(allow_none=True, data_key="triggerPrice")
    amount = fields.Float()
    cost = fields.Float()
    average = fields.Float()
    filled = fields.Float()
    remaining = fields.Float()
    status = fields.Str()
    fee = fields.Dict(allow_none=True)
    trades = fields.List(fields.Dict())
    fees = fields.List(fields.Dict())
    stop_price = fields.Float(allow_none=True, data_key="stopPrice")
    take_profit_price = fields.Float(allow_none=True, data_key="takeProfitPrice")
    stop_loss_price = fields.Float(allow_none=True, data_key="stopLossPrice")
    info = fields.Dict()

    agg_trade_id = fields.Str(missing=None)

    atr = fields.Float(missing=None)
    position_status = fields.Str(missing='opened')
    action = fields.Str(missing=None)
    closed_positions = fields.List(fields.Str(), missing=None)

    free_balance = fields.Float(missing=None)
    total_balance = fields.Float(missing=None)
    pl = fields.Float(missing=None)
    pl_percent = fields.Float(missing=None)

    @post_load
    def make_order(self, data, **kwargs):
        return Order(**data)
