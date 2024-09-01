import json
import os
from typing import Union, Optional, Final
from eth_typing.evm import Address, ChecksumAddress
import time
from web3 import HTTPProvider, Web3
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput, ContractLogicError, NameNotFound
from web3.types import (
    TxParams,
    Wei,
)
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from os import getenv


AddressLike = Union[Address, ChecksumAddress]

w3: Web3 = Web3(
    HTTPProvider(
        "https://ethereum-sepolia-rpc.publicnode.com"
    )
)

def _load_abi(name: str) -> str:
    path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/"
    with open(os.path.abspath(path + f"{name}.abi")) as f:
        abi: str = json.load(f)
    return abi

def _load_contract(abi_name: str, token_address: AddressLike) -> Contract:
    address = w3.to_checksum_address(token_address)
    return w3.eth.contract(address=address, abi=_load_abi(abi_name))

def get_eth_balance(address: AddressLike) -> Wei:
    """Get the balance of ETH for your address."""
    return w3.eth.get_balance(address)

def get_token_balance(token_address: AddressLike, address: AddressLike) -> int:
    """Get the balance of a token for your address."""
    erc20 = _load_contract("erc20", token_address)
    balance: int = erc20.functions.balanceOf(address).call()
    return balance

def _deadline() -> int:
    """Get a predefined deadline. 10min by default (same as the Uniswap SDK)."""
    return int(time.time()) + 10 * 60


def _addr_to_str(a: AddressLike) -> str:
    if isinstance(a, bytes):
        # Address or ChecksumAddress
        addr: str = Web3.to_checksum_address("0x" + bytes(a).hex())
        return addr
    elif isinstance(a, str) and a.startswith("0x"):
        addr = Web3.to_checksum_address(a)
        return addr

    raise NameNotFound(a)

def _get_tx_params(
    address:AddressLike, value: Wei = Wei(0), gas: Optional[Wei] = None
) -> TxParams:
    """Get generic transaction parameters."""
    params: TxParams = {
        "from": address,
        "value": value,
        "nonce": w3.eth.get_transaction_count(address)
    }

    if gas:
        params["gas"] = gas

    return params

def buy(wallet_private_key: str, token_address: AddressLike, ethAmount: float):
    UNISWAP_ROUTER_CONTRACT = _load_contract("uniswap-v2/router02", getenv("UNISWAP_ROUTER_ADDRESS"))
    amountIn = int(ethAmount * (10**18))
    account: Final[LocalAccount] = Account.from_key(wallet_private_key)
    wallet_address = account.address
    eth_bal = get_eth_balance(wallet_address)
    print(eth_bal)
    if eth_bal < amountIn:
        return None
    path = [getenv("WETH"), token_address]
    deadline = _deadline()
    
    print(deadline)

    tx_params = _get_tx_params(wallet_address, amountIn)
    print(tx_params)
    transaction = UNISWAP_ROUTER_CONTRACT.functions.swapExactETHForTokens(1, path, wallet_address, deadline).build_transaction(tx_params)
    print(transaction)
    
    transaction["gas"] = Wei(int(w3.eth.estimate_gas(transaction) * 1.2))

    signed_txn = w3.eth.account.sign_transaction(
        transaction, private_key=wallet_private_key
    )
    
    print(signed_txn)
    
    try:
        return w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    finally:
        print(f"nonce: {tx_params['nonce']}")

def sell(wallet_private_key: str, token_address: AddressLike, tokenAmount: float):
    account: Final[LocalAccount] = Account.from_key(wallet_private_key)
    wallet_address = account.address
    
    UNISWAP_ROUTER_CONTRACT = _load_contract("uniswap-v2/router02", getenv("UNISWAP_ROUTER_ADDRESS"))
    TOKEN_CONTRACT = _load_contract("erc20", token_address)
    amountIn = int(tokenAmount * (10**18))
    token_bal = get_token_balance(token_address, wallet_address)
    print(token_bal)
    if token_bal < amountIn:
        return None
    
    path = [token_address, getenv("WETH")]
    
    tx_params_approve = _get_tx_params(wallet_address)
    transaction_approve = TOKEN_CONTRACT.functions.approve(getenv("UNISWAP_ROUTER_ADDRESS"), amountIn).build_transaction(tx_params_approve)
    tx_params_approve["gas"] = Wei(int(w3.eth.estimate_gas(transaction_approve) * 1.2))
    signed_txn_approve = w3.eth.account.sign_transaction(
        transaction_approve, private_key=wallet_private_key
    )
    
    print("signed_txn_approve\n", signed_txn_approve)
    txn = w3.eth.send_raw_transaction(signed_txn_approve.rawTransaction)
    txn_receipt = w3.eth.wait_for_transaction_receipt(txn)
    print("approve", txn_receipt)
    deadline = _deadline()
    
    tx_params = _get_tx_params(wallet_address)
    transaction = UNISWAP_ROUTER_CONTRACT.functions.swapExactTokensForETH(amountIn, 0, path, wallet_address, deadline).build_transaction(tx_params)
    print(transaction)
        
    transaction["gas"] = Wei(int(w3.eth.estimate_gas(transaction) * 1.2))

    signed_txn = w3.eth.account.sign_transaction(
        transaction, private_key=wallet_private_key
    )
    
    print(signed_txn)
    
    try:
        return w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    finally:
        print(f"nonce: {tx_params['nonce']}")
    return 0
