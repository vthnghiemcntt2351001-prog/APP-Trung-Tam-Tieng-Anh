
# core/blockchain/contract_config.py

import os
from web3 import Web3


# =====================================================
# 1. CAU HINH KET NOI BLOCKCHAIN (GANACHE)
# =====================================================

# Dia chi RPC cua Ganache
GANACHE_RPC_URL = os.getenv(
    "GANACHE_RPC_URL",
    "http://127.0.0.1:7545"
)

# Dia chi RPC chinh cua Blockchain
BLOCKCHAIN_RPC_URL = os.getenv(
    "BLOCKCHAIN_RPC_URL",
    GANACHE_RPC_URL
).strip()

# Dia chi Smart Contract CertificateVerification
CONTRACT_ADDRESS = os.getenv(
    "CONTRACT_ADDRESS",
    "0x55ac46335a9d7e394005023D534a621dcEDcFc6b"
).strip()

# Private Key dung de ky giao dich tu Django.
# De trong neu chua can gui giao dich tu Django.
# KHONG dan Seed Phrase vao day.
ADMIN_PRIVATE_KEY = os.getenv(
    "ADMIN_PRIVATE_KEY",
    ""
).strip()


# =====================================================
# 2. ABI CUA SMART CONTRACT
# =====================================================

CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "string",
                "name": "certificateId",
                "type": "string"
            },
            {
                "indexed": False,
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "issuedAt",
                "type": "uint256"
            }
        ],
        "name": "CertificateIssued",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "certificateId",
                "type": "string"
            },
            {
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32"
            }
        ],
        "name": "issueCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "certificateId",
                "type": "string"
            }
        ],
        "name": "getCertificate",
        "outputs": [
            {
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32"
            },
            {
                "internalType": "uint256",
                "name": "issuedAt",
                "type": "uint256"
            },
            {
                "internalType": "bool",
                "name": "exists",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "certificateId",
                "type": "string"
            },
            {
                "internalType": "bytes32",
                "name": "dataHash",
                "type": "bytes32"
            }
        ],
        "name": "verifyCertificate",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


# =====================================================
# 3. KIEM TRA CAU HINH BLOCKCHAIN
# =====================================================

def validate_blockchain_config():
    """
    Kiem tra dinh dang cau hinh Blockchain.
    """

    if not BLOCKCHAIN_RPC_URL:
        raise ValueError(
            "BLOCKCHAIN_RPC_URL chua duoc cau hinh."
        )

    if not (
        BLOCKCHAIN_RPC_URL.startswith("http://")
        or BLOCKCHAIN_RPC_URL.startswith("https://")
    ):
        raise ValueError(
            "BLOCKCHAIN_RPC_URL phai bat dau bang http:// "
            "hoac https://."
        )

    if not CONTRACT_ADDRESS:
        raise ValueError(
            "CONTRACT_ADDRESS chua duoc cau hinh."
        )

    if (
        not CONTRACT_ADDRESS.startswith("0x")
        or len(CONTRACT_ADDRESS) != 42
    ):
        raise ValueError(
            "CONTRACT_ADDRESS khong dung dinh dang Ethereum."
        )

    return True


# =====================================================
# 4. KHOI TAO KET NOI WEB3
# =====================================================

# Kiem tra cau hinh truoc khi ket noi
validate_blockchain_config()

# Tao doi tuong Web3 ket noi voi Ganache
web3 = Web3(
    Web3.HTTPProvider(
        BLOCKCHAIN_RPC_URL,
        request_kwargs={"timeout": 10}
    )
)

# Kiem tra ket noi Blockchain
if not web3.is_connected():
    raise ConnectionError(
        f"Khong the ket noi Blockchain tai "
        f"{BLOCKCHAIN_RPC_URL}. "
        f"Hay kiem tra Ganache va RPC."
    )


# =====================================================
# 5. KIEM TRA DIA CHI SMART CONTRACT
# =====================================================

# Chuyen dia chi sang checksum address
CHECKSUM_CONTRACT_ADDRESS = Web3.to_checksum_address(
    CONTRACT_ADDRESS
)

# Kiem tra Smart Contract co ton tai tren mang hien tai
contract_code = web3.eth.get_code(
    CHECKSUM_CONTRACT_ADDRESS
)

if not contract_code or contract_code == b"\x00":
    raise ValueError(
        "Khong tim thay bytecode Smart Contract tai "
        f"{CHECKSUM_CONTRACT_ADDRESS}. "
        "Hay kiem tra dia chi hop dong va mang Ganache."
    )


# =====================================================
# 6. KHOI TAO DOI TUONG SMART CONTRACT
# =====================================================

contract = web3.eth.contract(
    address=CHECKSUM_CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)


# =====================================================
# 7. CAC HAM KIEM TRA BLOCKCHAIN
# =====================================================

def check_blockchain_connection():
    """
    Kiem tra ket noi Blockchain.
    Tra ve True neu ket noi thanh cong.
    """
    return web3.is_connected()


def get_blockchain_info():
    """
    Lay thong tin co ban cua Blockchain.
    """
    return {
        "connected": web3.is_connected(),
        "rpc_url": BLOCKCHAIN_RPC_URL,
        "chain_id": web3.eth.chain_id,
        "latest_block": web3.eth.block_number,
        "contract_address": contract.address,
    }
