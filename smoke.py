import argparse
import logging
import os
import time
import sys
import json

from chains import Binance, MockBinance
from thorchain import ThorchainState, ThorchainClient, Event

from common import Transaction, Coin, Asset

# Init logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=os.environ.get("LOGLEVEL", "INFO"),
)


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
    parser.add_argument(
        "--no-verify", default=False, type=bool, help="Skip verifying results"
    )

    args = parser.parse_args()

    with open("data/smoke_test_transactions.json", "r") as f:
        txns = json.load(f)

    smoker = Smoker(
        args.binance,
        args.thorchain,
        txns,
        args.generate_balances,
        args.fast_fail,
        args.no_verify,
    )
    try:
        smoker.run()
        sys.exit(smoker.exit)
    except Exception as e:
        logging.fatal(e)
        sys.exit(1)


class Smoker:
    def __init__(
        self, bnb, thor, txns, gen_balances=False, fast_fail=False, no_verify=False
    ):
        self.binance = Binance()
        self.thorchain = ThorchainState()

        self.txns = txns

        self.thorchain_client = ThorchainClient(thor)
        vault_address = self.thorchain_client.get_vault_address()

        self.mock_binance = MockBinance(bnb)
        self.mock_binance.set_vault_address(vault_address)

        self.generate_balances = gen_balances
        self.fast_fail = fast_fail
        self.no_verify = no_verify
        self.exit = 0

        time.sleep(5)  # give thorchain extra time to start the blockchain

    def error(self, err):
        self.exit = 1
        if self.fast_fail:
            raise Exception(err)
        else:
            logging.error(err)

    def run(self):
        for i, txn in enumerate(self.txns):
            txn = Transaction.from_dict(txn)
            logging.info(f"{i} {txn}")
            if txn.memo == "SEED":
                self.binance.seed(txn.to_address, txn.coins)
                self.mock_binance.seed(txn.to_address, txn.coins)
                continue

            self.binance.transfer(txn)  # send transfer on binance chain
            outbounds = self.thorchain.handle(txn)  # process transaction in thorchain
            outbounds = self.thorchain.handle_fee(outbounds)
            for outbound in outbounds:
                gas = self.binance.transfer(
                    outbound
                )  # send outbound txns back to Binance
                outbound.gas = [gas]

            self.thorchain.handle_rewards()
            self.thorchain.handle_gas(outbounds)

            # update memo with actual address (over alias name)
            for name, addr in self.mock_binance.aliases.items():
                txn.memo = txn.memo.replace(name, addr)

            self.mock_binance.transfer(txn)  # trigger mock Binance transaction
            self.mock_binance.wait_for_blocks(len(outbounds))
            self.thorchain_client.wait_for_blocks(
                2
            )  # wait an additional block to pick up gas

            # check if we are verifying the results
            if self.no_verify:
                continue

            # compare simulation pools vs real pools
            real_pools = self.thorchain_client.get_pools()
            for rpool in real_pools:
                spool = self.thorchain.get_pool(Asset(rpool["asset"]))
                if int(spool.rune_balance) != int(rpool["balance_rune"]):
                    self.error(
                        f"bad pool rune balance: {rpool['asset']} "
                        f"{spool.rune_balance} != {rpool['balance_rune']}"
                    )
                if int(spool.asset_balance) != int(rpool["balance_asset"]):
                    self.error(
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
                            coin1 = Coin(bal["denom"], sacct.get(bal["denom"]))
                            coin2 = Coin(bal["denom"], int(bal["amount"]))
                            if coin1 != coin2:
                                self.error(
                                    f"bad binance balance: {name} {coin2} != {coin1}"
                                )

            # check vault data
            vdata = self.thorchain_client.get_vault_data()
            if int(vdata["total_reserve"]) != self.thorchain.reserve:
                sim = self.thorchain.reserve
                real = vdata["total_reserve"]
                self.error(f"mismatching reserves: {sim} != {real}")
            if int(vdata["bond_reward_rune"]) != self.thorchain.bond_reward:
                sim = self.thorchain.bond_reward
                real = vdata["bond_reward_rune"]
                self.error(f"mismatching bond reward: {sim} != {real}")

            # compare simulation events with real events
            raw_events = self.thorchain_client.get_events()
            # convert to Event objects
            events = [Event.from_dict(evt) for evt in raw_events]

            # TODO ignore some un processed events type
            not_implemented = ["pool"]
            events = [e for e in events if e.type not in not_implemented]

            # get simulator events
            sim_events = self.thorchain.get_events()
            logging.info("Events: " + str(len(events)) + "/" + str(len(sim_events)))

            # check ordered events
            for event, sim_event in zip(events, sim_events):
                if event != sim_event:
                    logging.error(
                        f"Event Thorchain {event} \n   !="
                        f"  \nEvent Simulator {sim_event}"
                    )

                    logging.info(events)
                    logging.info(sim_events)
                    self.error("Events mismatch")


if __name__ == "__main__":
    main()
