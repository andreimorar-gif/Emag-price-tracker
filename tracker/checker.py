from tracker import db
from tracker.exceptions import NotificationException
from tracker.notifier import format_alert
from tracker.scraper import get_price


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

def print_result(product,info):
    name=info.name or product["name"] or product["url"]
    if info.price is None:
        status = "no price found"
    else:
        status = f"{info.price} {info.priceCurrency}"
    if not info.in_stock:
        status = "out of stock"
    print(f"[{product['id']}] {name[:60]}: {status}")

def check_product(conn,product,notifier,get_price_function=get_price):
    info=get_price_function(product["url"])
    previous_price=db.latest_price(conn,product["id"])
    db.record_price(conn,product["id"],info)

    if info.name is not None and info.name != product["name"]:
        db.update_product_name(conn,product["id"],info.name)

    print_result(product,info)

    if info.price is None:
        return

    for watcher in db.watchers(conn,product["id"]):
        last_notified=watcher["last_notified_price"]
        if last_notified is not None and info.price > last_notified:
            db.set_last_notified(conn,watcher["user_id"],product["id"],None)
            last_notified=None

        if not should_notify(previous_price,info.price,watcher["target_price"],last_notified):
            continue

        subject,body=format_alert(info.name or product["name"],product["url"],previous_price,info.price,info.priceCurrency)

        try:
            notifier.send(watcher["email"],subject,body)
        except NotificationException as e:
            print(f"[{product['id']}] {e}")
            continue

        db.set_last_notified(conn,watcher["user_id"],product["id"],info.price)
