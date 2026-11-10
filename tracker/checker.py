

def should_notify(previous_price,new_price,target_price,last_notified_price):
    """
    :param previous_price: price at the check before this one
    :param new_price: price found now
    :param target_price: user's target ( None => alert at every price)
    :param last_notified_price: last alerted price to user
    :return: True if user gets alert
    """
    if new_price is None:
        return False

    if target_price is not None:
        if last_notified_price is not None and new_price >= last_notified_price:
            return False
        return new_price <= target_price

    if previous_price is None:
        return False
    return new_price != previous_price