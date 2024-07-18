def trading_logic(price, capital, holding_quantity, average_purchase_price):
    action = None
    quantity = 0

    # ルール1: 取得した金額より10%上がったら売る
    if holding_quantity > 0 and price >= average_purchase_price * 1.10:
        action = 'sell'
        quantity = holding_quantity

    # ルール2: 取得した金額より5%下がったら売る
    elif holding_quantity > 0 and price <= average_purchase_price * 0.95:
        action = 'sell'
        quantity = holding_quantity

    # ルール3: 5万円以内で買える場合は買う
    elif capital >= price and holding_quantity == 0:
        quantity = int(capital / price)
        if quantity > 0:
            action = 'buy'

    return action, quantity
