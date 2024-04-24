""" simple script for stop-loss calculation """


def calculate_stop_loss_based_on_risk(position, capital, risk_percent, asset_price, leverage):
    risk_amount = capital * risk_percent
    leveraged_capital = capital * leverage
    price_move = (risk_amount / leveraged_capital) * asset_price

    if position == 'long':
        stop_loss_price = asset_price - price_move
    else:
        stop_loss_price = asset_price + price_move

    asset_amount = leveraged_capital / asset_price
    loss = leveraged_capital - (asset_amount * stop_loss_price)
    assert round(loss, 1) == round(risk_amount, 1)

    print(f"============\n"
          f"Find stop-loss price if investing {capital} with leverage {leverage} "
          f"and risking {risk_percent} of capital\n"
          f"position {str.upper(position)} set up:\n"
          f"capital: {capital}\n"
          f"leverage: {leverage}\n"
          f"percent risk of cap: {risk_percent * 100}%\n"
          f"risk amount: {risk_amount}\n"
          f"leverage entry: amount {asset_amount}\n"
          f"stop-loss price: {stop_loss_price}")

    return stop_loss_price


def calculate_risk_based_on_stop_loss(position, capital, risk_percent, asset_price, move, leverage=1):
    leveraged_risk = leverage * risk_percent

    risk_amount = leveraged_risk * capital
    asset_amount = risk_amount / move
    inv = asset_amount * asset_price

    if position == 'long':
        stop_loss_price = asset_price - move
    else:
        stop_loss_price = asset_price + move

    check = inv - (stop_loss_price * asset_amount)
    assert round(check, 1) == round(risk_amount, 1)

    print(f"============\n"
          f"Find position size based on price move ({move} against the position), "
          f"risk percent and leverage. Risk percent of capital "
          f"is multiplied be leverage!!\n"
          f"position {str.upper(position)} set up:\n"
          f"capital: {capital}\n"
          f"leverage: {leverage}\n"
          f"percent risk of cap: {leveraged_risk * 100}%\n"
          f"risk amount: {risk_amount}\n"
          f"leverage entry: amount {asset_amount}, investment {inv}\n"
          f"stop-loss price: {stop_loss_price}")

    return asset_amount


if __name__ == '__main__':
    calculate_stop_loss_based_on_risk(position='long',
                                      capital=800,
                                      risk_percent=0.01,
                                      asset_price=66_000,
                                      leverage=5)

    calculate_risk_based_on_stop_loss(position='long',
                                      capital=8400,
                                      risk_percent=0.01,
                                      asset_price=66_600,
                                      move=3300,
                                      leverage=2)
