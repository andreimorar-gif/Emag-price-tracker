from tracker.exceptions import NotificationException

def format_alert(product_name,url,old_price,new_price,currency):
    if product_name is None:
        product_name = "Your product"
    if currency is None:
        currency = "RON"
    if old_price is not None and new_price > old_price:
        kind = "Price increase"
    else:
        kind = "Price drop"
    subject=f"{kind}: {product_name} is now {new_price:.2f} {currency}"

    new_price_line=f"New price: {new_price:.2f} {currency}"
    lines=[product_name, ""]

    if old_price is not None and old_price > 0:
        percent = (new_price - old_price) / old_price * 100
        lines.append(f"{new_price_line} ({percent:+.0f}%)")
        lines.append(f"Previous price: {old_price:.2f} {currency}")
    else:
        lines.append(new_price_line)

    lines.append("")
    lines.append(url)
    body="\n".join(lines)+"\n"
    return subject,body

class ConsoleNotifier:
    def send(self,to,subject,body):
        print()
        print(f"ALERT to {to}")
        print(subject)
        print(body)

def get_notifier():
    return ConsoleNotifier()