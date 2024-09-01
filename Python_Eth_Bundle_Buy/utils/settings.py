from os import getenv
from typing import Final

from web3 import Web3
from eth_account.account import Account
from eth_account.signers.local import LocalAccount

# fmt: off
CHAIN_ID: Final[int] = 11155111
SEND_ETH_GAS_LIMIT: Final[int] = 21_000
HTTP_PROVIDER_MAINNET: Final[str] = f"https://eth-mainnet.g.alchemy.com/v2/{getenv('ALCHEMY_API_KEY')}"
HTTP_PROVIDER_SEPOLIA: Final[str] = f"https://eth-sepolia-public.unifra.io"
HTTP_FLASHBOTS_URI_MAINNET: Final[str] = "https://relay.flashbots.net"
HTTP_FLASHBOTS_URI_SEPOLIA: Final[str] = "https://relay-sepolia.flashbots.net"

# Contract Address
if CHAIN_ID==1:         # Ethereum mainnet
    WETH=f'0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    TOKEN_ADDRESS=f''
    UNISWAP_ROUTER_ADDRESS = f'0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    BRIBE_CONTRACT = f'0x73C9321ab67177C3005Dcd273009737482c45Ce8'
else:                  # Sepolia
    WETH = f'0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9'
    # TOKEN_ADDRESS = f'0x8eE0f3AF39eb852ccC2d41E12B9e5D55D529d095'
    TOKEN_ADDRESS = '0x22A270573700DD0Cc10Dd3788e815D22a874F8cE'
    UNISWAP_ROUTER_ADDRESS=f'0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008'
    BRIBE_CONTRACT=f'0xf7c44bd8ED1906967ad06A618B5cbFf07dA1Be68'

# Account signers
# GASSER_ACCOUNT_SIGNER: Final[LocalAccount] = Account.from_key(getenv("GASSER_PRIVATE_KEY"))
# BUYER_ACCOUNT_SIGNERS: Final[list[LocalAccount]] = [Account.from_key(priv) for priv in getenv("BUYER_PRIVATE_KEY").split(',')]
GASSER_ACCOUNT_SIGNER: Final[LocalAccount] = Account.from_key()

buyer_keypairs = [ # private key, public key

]
BUYER_ACCOUNT_SIGNERS: Final[list[LocalAccount]] = [Account.from_key(keypair['secret']) for keypair in buyer_keypairs]

# Gas fees, denominated in ether
BRIBE_FEES: Final[list[float]] = [0.01, 0.002, 0.003, 0.004, 0.005]

# Pick menu options and title
compromised_wallets = '\n- '.join(f"Compromised Wallet {i}: {account.address}" for i, account in enumerate(BUYER_ACCOUNT_SIGNERS))
PICK_MENU_OPTIONS_WALLET: Final[list[int]] = [i for i, account in enumerate(BUYER_ACCOUNT_SIGNERS)]
PICK_MENU_OPTIONS_WALLET.append(-1)
PICK_MENU_TITLE_WALLET: Final[str] = f"Are the following addresses correct (use the arrow keys to move and enter to select)?\n- {compromised_wallets}\n- Gas Provider Wallet: {GASSER_ACCOUNT_SIGNER.address}"

bribe_fees = '\n- '.join(f"Bribe Fee {i}: {bribe_fee}" for i, bribe_fee in enumerate(BRIBE_FEES))
PICK_MENU_OPTIONS_BRIBE: Final[list[int]] = [i for i, account in enumerate(BRIBE_FEES)]
PICK_MENU_OPTIONS_BRIBE.append(-1)
PICK_MENU_TITLE_BRIBE: Final[str] = f"Are the following bribe fees (use the arrow keys to move and enter to select)?\n- {bribe_fees}\n"

PICK_MENU_OPTIONS_START: Final[list[str]] = ['Yes', 'No']
PICK_MENU_TITLE_START_BOT: Final[str] = f"Do you start bot (use the arrow keys to move and enter to select)?\n? - Yes\n -No\n"
