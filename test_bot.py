from matrix_bot import AntiUwUBot


def test_get_coin_balance(user="@test_user:test_server.gg"):
    test_inst = AntiUwUBot()
    assert test_inst.get_coin_balance(user) == 42
