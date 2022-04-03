from utils.common import get_rune_asset

RUNE = get_rune_asset()


class Breakpoint:
    """
    This takes a snapshot picture of the chain(s) and generates json
    """

    def __init__(self, thorchain, bnb):
        self.bnb = bnb
        self.thorchain = thorchain

    def snapshot(self, txID, out):
        """
        Generate a snapshot picture of the bnb and thorchain balances to
        compare
        """
        snap = {
            "TX": txID,
            "OUT": out,
            "CONTRIB": {},
            "USER-1": {},
            "PROVIDER-1": {},
            "PROVIDER-2": {},
            "VAULT": {},
        }

        for name, acct in self.bnb.accounts.items():
            # ignore if is a new name
            if name not in snap:
                continue

            for coin in acct.balances:
                snap[name][str(coin.asset)] = coin.amount

        for pool in self.thorchain.pools:
            asset = pool.asset_balance
            if asset < 0:
                asset = 0
            rune = pool.rune_balance
            if rune < 0:
                rune = 0
            snap["POOL." + str(pool.asset)] = {
                str(pool.asset): int(asset),
                RUNE: int(rune),
            }

        return snap
