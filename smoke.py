import argparse
import logging
import os
import time

from chains import Binance, MockBinance
from thorchain import ThorchainState, ThorchainClient

from common import Transaction, Coin, Asset

# Init logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=os.environ.get("LOGLEVEL", "INFO"),
)

# A list of smoke test transaction
txns = [
    Transaction(
        Binance.chain,
        "MASTER",
        "MASTER",
        [Coin("BNB", 49730000), Coin("RUNE-A1F", 100000000000), Coin("LOK-3C0", 0)],
        "SEED",
    ),
    Transaction(
        Binance.chain,
        "MASTER",
        "USER-1",
        [
            Coin("BNB", 50000000),
            Coin("RUNE-A1F", 50000000000),
            Coin("LOK-3C0", 50000000000),
        ],
        "SEED",
    ),
    Transaction(
        Binance.chain,
        "MASTER",
        "STAKER-1",
        [
            Coin("BNB", 200000000),
            Coin("RUNE-A1F", 100000000000),
            Coin("LOK-3C0", 40000000000),
        ],
        "SEED",
    ),
    Transaction(
        Binance.chain,
        "MASTER",
        "STAKER-2",
        [
            Coin("BNB", 200000000),
            Coin("RUNE-A1F", 50900000000),
            Coin("LOK-3C0", 10000000000),
        ],
        "SEED",
    ),
    # Staking
    Transaction(
        Binance.chain,
        "STAKER-1",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "STAKE:BNB.BNB",
    ),
    Transaction(
        Binance.chain,
        "STAKER-1",
        "VAULT",
        [Coin("LOK-3C0", 40000000000), Coin("RUNE-A1F", 50000000000)],
        "STAKE:BNB.LOK-3C0",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "ABDG?",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "STAKE:",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "STAKE:BNB.TCAN-014",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 150000000), Coin("RUNE-A1F", 50000000000)],
        "STAKE:RUNE-A1F",
    ),
    Transaction(
        Binance.chain, "STAKER-2", "VAULT", [Coin("BNB", 30000000)], "STAKE:BNB.BNB"
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("RUNE-A1F", 10000000000)],
        "STAKE:BNB.BNB",
    ),
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 90000000), Coin("RUNE-A1F", 30000000000)],
        "STAKE:BNB.BNB",
    ),
    # Adding
    Transaction(
        Binance.chain,
        "STAKER-2",
        "VAULT",
        [Coin("BNB", 30000000), Coin("RUNE-A1F", 5000000000)],
        "ADD:BNB.BNB",
    ),
    # Misc
    Transaction(Binance.chain, "USER-1", "VAULT", [Coin("RUNE-A1F", 200000000)], " "),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("RUNE-A1F", 200000000)], "ABDG?"
    ),
    # Swaps
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("BNB", 30000000)], "SWAP:BNB.BNB"
    ),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("BNB", 30000000)], "SWAP:BNB.BNB"
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("BNB", 30000000), Coin("RUNE-A1F", 100000000)],
        "SWAP:BNB.BNB",
    ),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("RUNE-A1F", 100001000)], "SWAP:BNB.BNB"
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("RUNE-A1F", 10000000000)],
        "SWAP:BNB.BNB::26572599",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("RUNE-A1F", 10000000000)],
        "SWAP:BNB.BNB",
    ),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("BNB", 10000000)], "SWAP:BNB.RUNE-A1F",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("RUNE-A1F", 10000000000)],
        "SWAP:BNB.BNB:STAKER-1:23853375",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("RUNE-A1F", 10000000000)],
        "SWAP:BNB.BNB:STAKER-1:22460886",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("BNB", 10000000)],
        "SWAP:BNB.RUNE-A1F:bnbSTAKER-1",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("LOK-3C0", 5000000000)],
        "SWAP:BNB.RUNE-A1F",
    ),
    Transaction(
        Binance.chain,
        "USER-1",
        "VAULT",
        [Coin("RUNE-A1F", 5000000000)],
        "SWAP:BNB.LOK-3C0",
    ),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("LOK-3C0", 5000000000)], "SWAP:BNB.BNB",
    ),
    Transaction(
        Binance.chain, "USER-1", "VAULT", [Coin("BNB", 5000000)], "SWAP:BNB.LOK-3C0"
    ),
    # Unstaking (withdrawing)
    Transaction(
        Binance.chain, "STAKER-1", "VAULT", [Coin("BNB", 1)], "WITHDRAW:BNB.BNB:5000",
    ),
    Transaction(
        Binance.chain, "STAKER-1", "VAULT", [Coin("BNB", 1)], "WITHDRAW:BNB.LOK-3C0"
    ),
    Transaction(
        Binance.chain, "STAKER-1", "VAULT", [Coin("BNB", 1)], "WITHDRAW:BNB.BNB:10000",
    ),
    Transaction(
        Binance.chain, "STAKER-2", "VAULT", [Coin("BNB", 1)], "WITHDRAW:BNB.BNB"
    ),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--binance", default="http://localhost:26660", help="Mock binance server"
    )
    parser.add_argument(
        "--thorchain", default="http://localhost:1317", help="Thorchain API url"
    )
    parser.add_argument(
        "--generate-balances", default=False, type=bool, help="Generate balances (bool)"
    )
    parser.add_argument(
        "--fast-fail", default=False, type=bool, help="Generate balances (bool)"
    )

    args = parser.parse_args()

    smoker = Smoker(
        args.binance, args.thorchain, txns, args.generate_balances, args.fast_fail
    )
    smoker.run()


class Smoker:
    def __init__(self, bnb, thor, txns=txns, gen_balances=False, fast_fail=False):
        self.binance = Binance()
        self.thorchain = ThorchainState()

        self.txns = txns

        self.thorchain_client = ThorchainClient(thor)
        vault_address = self.thorchain_client.get_vault_address()

        self.mock_binance = MockBinance(bnb)
        self.mock_binance.set_vault_address(vault_address)

        self.generate_balances = gen_balances
        self.fast_fail = fast_fail

    def wait_for_pool_asset(self, target, attempts=5):
        """
        Waits until a pool asset amount is equal to given amount
        """
        for x in range(attempts):
            pools = self.thorchain_client.get_pools()
            for pool in pools:
                if Asset(pool["asset"]).is_equal(target.asset):
                    if int(pool["balance_asset"]) == target.amount:
                        print(">>>>>>>> wait passed1..")
                        mockAccounts = self.mock_binance.accounts()
                        for macct in mockAccounts:
                            for name, address in self.mock_binance.aliases.items():
                                if name == "VAULT":
                                    for bal in macct["balances"]:
                                        if (
                                            bal["denom"] == "BNB"
                                            and target.amount == bal["amount"]
                                        ):
                                            print(">>>>>>>> wait passed2..")
                                            return
            time.sleep(5)  # wait a block

        # if we get here, we've effectively timed out waiting for everything to
        # match. Do nothing and let a comparison occur
        logging.error(f"Timed out waiting for pool asset")

    def run(self):
        gas_assets = ["BNB.BNB"]
        for i, txn in enumerate(self.txns):
            logging.info(f"{i} {txn}")
            if txn.memo == "SEED":
                self.binance.seed(txn.toAddress, txn.coins)
                self.mock_binance.seed(txn.toAddress, txn.coins)
                continue

            self.binance.transfer(txn)  # send transfer on binance chain
            outbounds = self.thorchain.handle(txn)  # process transaction in thorchain
            outbounds = self.thorchain.handle_fee(outbounds)
            for outbound in outbounds:
                gas = self.binance.transfer(
                    outbound
                )  # send outbound txns back to Binance
                self.thorchain.handle_gas(gas)  # subtract gas from pool(s)

            # update memo with actual address (over alias name)
            for name, addr in self.mock_binance.aliases.items():
                txn.memo = txn.memo.replace(name, addr)

            self.mock_binance.transfer(txn)  # trigger mock Binance transaction

            # wait for transactions to be executed on thorchain
            if len(outbounds) == 0:
                self.thorchain_client.wait_for_blocks(1)
            else:
                for gas_asset in gas_assets:
                    pool = self.thorchain.get_pool(Asset(gas_asset))
                    self.wait_for_pool_asset(Coin(gas_asset, pool.asset_balance))

            # compare simulation pools vs real pools
            real_pools = self.thorchain_client.get_pools()
            for rpool in real_pools:
                spool = self.thorchain.get_pool(Asset(rpool["asset"]))
                if int(spool.rune_balance) != int(rpool["balance_rune"]):
                    raise Exception(
                        f"bad pool rune balance: {rpool['asset']} "
                        f"{spool.rune_balance} != {rpool['balance_rune']}"
                    )
                if int(spool.asset_balance) != int(rpool["balance_asset"]):
                    raise Exception(
                        f"bad pool asset balance: {rpool['asset']} "
                        f"{spool.asset_balance} != {rpool['balance_asset']}"
                    )

            # compare simulation binance vs mock binance
            mockAccounts = self.mock_binance.accounts()
            for macct in mockAccounts:
                for name, address in self.mock_binance.aliases.items():
                    if name == "MASTER":
                        continue  # don't care to compare MASTER account
                    if address == macct["address"]:
                        sacct = self.binance.get_account(name)
                        for bal in macct["balances"]:
                            coin = Coin(bal["denom"], sacct.get(bal["denom"]))
                            if not coin.is_equal(
                                Coin(bal["denom"], int(bal["amount"]))
                            ):
                                raise Exception(
                                    f"bad binance balance: {bal['denom']} "
                                    f"{bal['amount']} != {coin}"
                                )


if __name__ == "__main__":
    main()
