from tracker.checker import should_notify


def test_price_drop_alerts():
    assert should_notify(100,90,None,None) is True

def test_price_increase_alerts():
    assert should_notify(90,100,None,None) is True

def test_same_price_does_not_alert():
    assert should_notify(100,100,None,None) is False

def test_first_check_without_target_does_not_alert():
    assert should_notify(None,100,None,None) is False

def test_no_price_does_not_alert():
    assert should_notify(100,None,None,None) is False

def test_drop_when_above_target_does_not_alert():
    assert should_notify(100,90,80,None) is False

def test_reaching_target_alerts():
    assert should_notify(100,90,90,None) is True

def test_price_increase_with_target_does_not_alert():
    assert should_notify(90,100,80,None) is False

def test_same_target_alert_is_not_sent_twice():
    assert should_notify(100,80,90,80) is False

def test_lower_price_below_target_alerts_again():
    assert should_notify(80,70,90,80) is True