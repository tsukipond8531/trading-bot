""" simple script for stop-loss calculation """


def calculate_stop_loss(capital, risk_percent, asset_price, leverage):
    risk_amount = capital * risk_percent
    leveraged_capital = capital * leverage
    price_move = (risk_amount / leveraged_capital) * asset_price
    stop_loss_price = asset_price - price_move

    buy_amount = leveraged_capital / asset_price
    loss = leveraged_capital - (buy_amount * stop_loss_price)

    print(f"stop_loss: {stop_loss_price}")
    print(f"risk_amount: {risk_amount}")
    print(f"loss: {loss}")
    assert round(loss, 1) == round(risk_amount, 1)
    return stop_loss_price


if __name__ == '__main__':
    calculate_stop_loss(capital=500,
                        risk_percent=0.05,
                        asset_price=70_000,
                        leverage=2)
