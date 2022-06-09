import logging

from utils.common import Coin, HttpClient, get_rune_asset, Asset
from chains.aliases import aliases_xhv, get_alias_address
from chains.chain import GenericChain
from tenacity import retry, stop_after_delay, wait_fixed

RUNE = get_rune_asset()


class MockHaven(HttpClient):
    """
    An client implementation for a regtest haven server
    """

    seeds = {
        "MASTER": "water rotate bimonthly arises deity cycling oven unlikely "
        + "smuggled pheasants coexist purged menu tacit upstairs guest "
        + "deity dotted italics pouch yacht hairy rebel ringing coexist",
        "CONTRIB": "fossil never whipped cylinder umpire owner gave kitchens "
        + "going sake sabotage ashtray pipeline tyrant outbreak ought inactive "
        + "gawk huge sedan border toaster evenings firm whipped",
        "USER-1": "arises zero aglow amnesty unveil nightly anybody major "
        + "dogs nestle down rounded budget viewpoint boxes ghetto "
        + "ruling vector liquid vulture pastry dazed number ostrich budget",
        "PROVIDER-1": "nuisance easy citadel irate lobster dexterity ghost inactive "
        + "buckets bimonthly spiders utopia down logic dehydrate tugs "
        + "examine tender egotistic muppet poverty dozen feline gigantic egotistic",
    }
    wallets = {}

    decimal_diff = 10000  # difference in decimal between haven and thor
    block_stats = {
        "tx_rate": 31401,
        "tx_size": 1000,
    }

    def __init__(self, base_url_daemon):
        super().__init__(base_url_daemon)
        self.wallet = HttpClient(self.get_wallet_url())
        self.wait_for_node()
        self.create_wallets()

    @retry(stop=stop_after_delay(30), wait=wait_fixed(1))
    def create_wallets(self):
        for key in self.seeds:
            result = self.call_RPC(
                "wallet",
                "restore_deterministic_wallet",
                {"filename": key, "password": "password", "seed": self.seeds[key]},
            )
            self.wallets[result["address"]] = key

    def get_wallet_url(self):
        url = self.base_url.replace("17750", "5051")
        return url

    def call_RPC(self, server, method, args):
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": args,
        }

        if server == "wallet":
            result = self.wallet.post("/json_rpc", payload)
        elif server == "daemon":
            result = self.post("/json_rpc", payload)
        else:
            logging.error("unknown server passed")
            raise Exception

        if result.get("error"):
            err = result["error"]
            logging.error(f"error calling rpc {err}")
            raise Exception("RPC call error")
        return result["result"]

    def set_vault_address(self, addr):
        """
        Set the vault haven address
        """
        aliases_xhv["VAULT"] = addr

    @retry(stop=stop_after_delay(180), wait=wait_fixed(1))
    def wait_for_node(self):
        """
        Haven regtest node is started with directly mining 100 blocks
        to be able to start handling transactions.
        It can take a while depending on the machine specs so we retry.
        """
        current_height = self.get_block_height()
        if current_height < 75:
            logging.warning("Haven regtest starting, waiting")
            raise Exception

    def get_block_height(self):
        """
        Get the current block height of bitcoin regtest
        """
        result = self.call_RPC("daemon", "get_block_count", {})
        return result["count"]

    def get_balance(self, address):
        """
        Get XHV balance for an address
        """
        # open wallet
        self.call_RPC(
            "wallet",
            "open_wallet",
            {"filename": self.wallets[address], "password": "password"},
        )

        # refresh wallet
        for i in range(5):
            result = self.call_RPC("wallet", "refresh", {})
            if result["blocks_fetched"] > 0:
                break

        # get balance
        result = self.call_RPC(
            "wallet", "get_balance", {"account_index": 0, "asset_type": "XHV"}
        )

        return result["balance"] // self.decimal_diff

    def transfer(self, txn):
        """
        Make a transaction/transfer on regtest haven
        """
        if not isinstance(txn.coins, list):
            txn.coins = [txn.coins]

        self.call_RPC(
            "wallet",
            "open_wallet",
            {"filename": txn.from_address, "password": "password"},
        )

        if txn.to_address in aliases_xhv.keys():
            txn.to_address = get_alias_address(txn.chain, txn.to_address)

        if txn.from_address in aliases_xhv.keys():
            txn.from_address = get_alias_address(txn.chain, txn.from_address)

        chain = txn.chain
        asset = txn.get_asset_from_memo()
        if asset:
            chain = asset.get_chain()

        # update memo with actual address (over alias name)
        is_synth = txn.is_synth()
        for alias in aliases_xhv.keys():
            # we use RUNE BNB address to identify a cross chain liqudity provision
            if txn.memo.startswith("ADD") or is_synth:
                chain = RUNE.get_chain()
            addr = get_alias_address(chain, alias)
            txn.memo = txn.memo.replace(alias, addr)

        if txn.memo.startswith("ADD"):
            # append the sender address to memo
            txn.memo += txn.from_address

        # refresh wallet
        for i in range(5):
            result = self.call_RPC("wallet", "refresh", {})
            if result["blocks_fetched"] > 0:
                break

        # create transaction
        result = self.call_RPC(
            "wallet",
            "transfer",
            {
                "destinations": [
                    {
                        "amount": txn.coins[0].amount * self.decimal_diff,
                        "address": txn.to_address,
                    }
                ],
                "memo": txn.memo,
            },
        )

        txn.id = result["tx_hash"]
        txn.gas = [Coin("XHV.XHV", result["fee"] // self.decimal_diff)]


class Haven(GenericChain):
    """
    A local simple implementation of haven chain
    """

    name = "Haven"
    chain = "XHV"
    coin = Asset("XHV.XHV")
    rune_fee = 2000000

    @classmethod
    def _calculate_gas(cls, pool, txn):
        """
        Calculate gas according to RUNE thorchain fee
        """
        if pool is None:
            return Coin(cls.coin, MockHaven.block_stats["tx_rate"])

        xhv_amount = pool.get_rune_in_asset(int(cls.rune_fee / 2))
        return Coin(cls.coin, xhv_amount)
