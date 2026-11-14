from app.negotiation.engine import Rules, asks_last_price, decide, floor_price, parse_offer

RULES = Rules(max_discount_percent=20, auto_accept_below=0)
LIST = 10000.0


def test_floor():
    assert floor_price(LIST, RULES) == 8000


def test_first_ask_holds_price():
    d = decide(LIST, RULES, 0, None, None)
    assert d.action == "hold" and d.price == LIST


def test_soft_requests_never_reach_floor():
    last, prices = None, []
    for i in range(10):
        d = decide(LIST, RULES, i, last, None, 0)
        prices.append(d.price)
        last = d.price
        assert d.action != "final"
    assert prices == sorted(prices, reverse=True)
    assert min(prices) > 8000


def test_single_last_price_ask_is_treated_as_normal_price():
    d = decide(LIST, RULES, 0, None, None, 1)
    assert d.action == "hold" and d.price == LIST


def test_insisting_on_last_price_gives_floor():
    d = decide(LIST, RULES, 1, 9400, None, 2)
    assert d.action == "final" and d.price == 8000


def test_asks_last_price_detection():
    assert asks_last_price("donne moi ton dernier prix")
    assert asks_last_price("c'est quoi le prix final ?")
    assert not asks_last_price("c'est cher, tu peux baisser ?")


def test_too_low_offer_not_accepted():
    d = decide(LIST, RULES, 0, None, 5000)
    assert d.action == "too_low" and d.price >= 8000


def test_offer_above_ask_accepted():
    d = decide(LIST, RULES, 1, 9400, 9500)
    assert d.action == "accept" and d.price == 9500


def test_disabled_when_no_discount():
    assert decide(LIST, Rules(0), 0, None, 5000).action == "disabled"


def test_parse_offer():
    assert parse_offer("je donne 8500", LIST) == 8500
    assert parse_offer("8k stp", LIST) == 8000
    assert parse_offer("10% de réduction", LIST) == 9000
    assert parse_offer("donne moi le dernier prix", LIST) is None
    assert parse_offer("j'en veux 2", LIST) is None
