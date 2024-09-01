from typing import Final
from uuid import UUID, uuid4

from dotenv import load_dotenv
from os import getenv
from flashbots.types import FlashbotsBundleTx, HexStr
from pick import pick
from web3 import HTTPProvider, Web3
from web3.exceptions import TransactionNotFound
from web3morebundlers import bundler
from uni.swap import _load_contract, _deadline
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
import time

def main() -> None:
    option, _ = pick(constants.PICK_MENU_OPTIONS_WALLET, constants.PICK_MENU_TITLE_WALLET)
    match option:
        case -1:
            print("Exiting.")
            exit()
        case _:
            select_wallet=option

    print(f"Selecting wallet {select_wallet}")

    option, _ = pick(constants.PICK_MENU_OPTIONS_BRIBE, constants.PICK_MENU_TITLE_BRIBE)
    match option:
        case -1:
            print("Exiting.")
            exit()
        case _:
            select_fee = option

    print(f"Selecting fee {select_fee}")
    buy_amount = input("Enter ether amount to buy token: ")

    option, _ = pick(constants.PICK_MENU_OPTIONS_START, constants.PICK_MENU_TITLE_START_BOT)
    match option:
        case 'Yes':
            print("Start...")
        case 'No':
            print("Stop.")
            exit()

    BUNDLER_ENPOINTS: Final[list[str]] = [
        constants.HTTP_FLASHBOTS_URI_MAINNET
        if constants.CHAIN_ID == 1
        else constants.HTTP_FLASHBOTS_URI_SEPOLIA,
        # "https://rpc.titanbuilder.xyz",
        # "https://builder0x69.io",
        # "https://rpc.beaverbuild.org",
        # "https://rsync-builder.xyz",
        # "https://eth-builder.com",
        # "https://builder.gmbit.co/rpc",
        # "https://buildai.net",
        # "https://rpc.payload.de",
    ]

    # Create Web3 provider and inject flashbots module
    w3: Web3 = Web3(
        HTTPProvider(
            # constants.HTTP_PROVIDER_MAINNET
            # if constants.CHAIN_ID == 1
            # else constants.HTTP_PROVIDER_SEPOLIA
            "https://ethereum-sepolia-rpc.publicnode.com"
        )
    )

    bundler(
        w3=w3,
        signature_account=constants.GASSER_ACCOUNT_SIGNER,
        endpoint_uris=BUNDLER_ENPOINTS,
        flashbots_uri=(
            constants.HTTP_FLASHBOTS_URI_MAINNET
            if constants.CHAIN_ID == 1
            else constants.HTTP_FLASHBOTS_URI_SEPOLIA
        ),
    )

    # Construct tx bundle from ./bundle/bundle.py
    # print("Constructing bundle")
    UNISWAP_ROUTER_CONTRACT = _load_contract("uniswap-v2/router02", constants.UNISWAP_ROUTER_ADDRESS)
    BRIBE_CONTRACT = _load_contract("bribe", constants.BRIBE_CONTRACT)

    bribe_fee = Web3.toWei(constants.BRIBE_FEES[select_fee], 'ether')
    tx_bribe_params = {
        "from": constants.GASSER_ACCOUNT_SIGNER.address,
        "value": bribe_fee,
        "nonce": w3.eth.get_transaction_count(constants.GASSER_ACCOUNT_SIGNER.address),
        "type": 2,
    }
    transaction_bribe = BRIBE_CONTRACT.functions.execute().build_transaction(tx_bribe_params)
    transaction_bribe['gas'] = int(w3.eth.estimateGas(transaction_bribe) * 2)
    path = [constants.WETH, constants.TOKEN_ADDRESS]
    ethAmount = Web3.toWei(buy_amount, "ether")
    buyWallet = constants.BUYER_ACCOUNT_SIGNERS[select_wallet]
    tx_params = {
        "from": buyWallet.address,
        "value": ethAmount,
        "nonce": w3.eth.get_transaction_count(buyWallet.address),
        "type": 2,
    }
    cycle = 0
    while True:
        print(f"Cycle: {cycle}")
        cycle += 1
        deadline = _deadline()
        try:
            transaction = UNISWAP_ROUTER_CONTRACT.functions.swapExactETHForTokens(0, path, buyWallet.address, deadline).build_transaction(tx_params)
        except Exception as error:
            print(f"Liquidity wasn't created!")
            continue

        transaction['gas'] = int(w3.eth.estimateGas(transaction) * 2)
        BUNDLE: Final[list[FlashbotsBundleTx]] = [
            {"transaction": transaction_bribe, "signer": constants.GASSER_ACCOUNT_SIGNER},
            {"transaction": transaction, "signer": buyWallet},
        ]
        print(BUNDLE)
        sub_cycle = 0
        # Attempt to mine bundle
        while True:
            print(f"Sub cycle: {sub_cycle}")
            sub_cycle += 1
            current_time = int(time.time())
            current_block: int = w3.eth.block_number
            target_block: int = current_block + 1
            print(f"Simulating bundle on block {current_block}")
            try:
                w3.flashbots.simulate(BUNDLE, current_block)
                time.sleep(10)
                print("Simulation successful")
            except Exception as error:
                print(f"Simulation failed, {error=}")
                continue

            replacement_uuid: UUID = str(uuid4())
            print(f"Sending bundle targeting block {target_block}")
            send_result = w3.flashbots.send_bundle(
                BUNDLE,
                target_block_number=target_block,
                opts={"replacementUuid": replacement_uuid,},
            )
            send_result.wait()
            try:
                receipts = send_result.receipts()
                print(f"Bundle was successfully mined in block {receipts[0].blockNumber}")
                return
            except TransactionNotFound:
                # print(f"Bundle was not found in block {target_block}, canceling")
                cancel_res = w3.flashbots.cancel_bundles(replacement_uuid)
                # print(f"{cancel_res=}")
            if current_time > deadline:
                break


if __name__ == "__main__":
    load_dotenv()
    import utils.settings as constants

    main()
