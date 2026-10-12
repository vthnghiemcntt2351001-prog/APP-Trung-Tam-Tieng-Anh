
# core/blockchain/blockchain_service.py

import json
import re

from web3 import Web3

from .contract_config import (
    BLOCKCHAIN_RPC_URL,
    CONTRACT_ADDRESS,
    CONTRACT_ABI,
)


# =====================================================
# 1. KET NOI BLOCKCHAIN VA SMART CONTRACT
# =====================================================

def get_blockchain_contract():
    """Ket noi den Blockchain va Smart Contract."""

    if not BLOCKCHAIN_RPC_URL:
        raise ValueError(
            "Chua cau hinh BLOCKCHAIN_RPC_URL."
        )

    if not CONTRACT_ADDRESS:
        raise ValueError(
            "Chua cau hinh CONTRACT_ADDRESS."
        )

    web3 = Web3(
        Web3.HTTPProvider(BLOCKCHAIN_RPC_URL)
    )

    if not web3.is_connected():
        raise ConnectionError(
            "Khong the ket noi Blockchain RPC."
        )

    if not Web3.is_address(CONTRACT_ADDRESS):
        raise ValueError(
            "Dia chi Smart Contract khong hop le."
        )

    contract_address = Web3.to_checksum_address(
        CONTRACT_ADDRESS
    )

    contract_code = web3.eth.get_code(
        contract_address
    )

    if not contract_code:
        raise ValueError(
            "Khong tim thay Smart Contract tai dia chi da cau hinh."
        )

    contract = web3.eth.contract(
        address=contract_address,
        abi=CONTRACT_ABI,
    )

    return web3, contract


# =====================================================
# 2. KIEM TRA DU LIEU DAU VAO
# =====================================================

def validate_certificate_id(certificate_id):
    """Kiem tra ma chung chi."""

    if not isinstance(certificate_id, str):
        raise ValueError(
            "Ma chung chi phai la chuoi ky tu."
        )

    certificate_id = certificate_id.strip()

    if not certificate_id:
        raise ValueError(
            "Ma chung chi khong duoc de trong."
        )

    if len(certificate_id) > 200:
        raise ValueError(
            "Ma chung chi khong duoc vuot qua 200 ky tu."
        )

    return certificate_id


def validate_data_hash(data_hash):
    """Kiem tra ma bam bytes32 co tien to 0x."""

    if not isinstance(data_hash, str):
        raise ValueError(
            "data_hash phai la chuoi ky tu."
        )

    data_hash = data_hash.strip()

    # Ho tro ca hash co va khong co tien to 0x
    if not data_hash.startswith("0x"):
        data_hash = "0x" + data_hash

    if not re.fullmatch(
        r"0x[0-9a-fA-F]{64}",
        data_hash,
    ):
        raise ValueError(
            "data_hash phai gom 0x va 64 ky tu hexa."
        )

    return data_hash.lower()


# =====================================================
# 3. LAY DIA CHI CHU SO HUU SMART CONTRACT
# =====================================================

def get_contract_owner():
    """Lay dia chi vi chu so huu Smart Contract."""

    web3, contract = get_blockchain_contract()

    return contract.functions.owner().call()


# =====================================================
# 4. GHI MA BAM CHUNG CHI LEN BLOCKCHAIN
# =====================================================

def issue_certificate(certificate_id, data_hash):
    """
    Ghi ma bam chung chi len Blockchain.

    Su dung tai khoan Ganache da duoc mo khoa.
    Khong dua private key vao ma nguon.
    """

    certificate_id = validate_certificate_id(
        certificate_id
    )

    data_hash = validate_data_hash(data_hash)

    web3, contract = get_blockchain_contract()

    accounts = web3.eth.accounts

    if not accounts:
        raise RuntimeError(
            "Ganache khong co tai khoan kha dung."
        )

    owner = contract.functions.owner().call()

    owner_checksum = Web3.to_checksum_address(
        owner
    )

    owner_account = next(
        (
            account
            for account in accounts
            if Web3.to_checksum_address(account)
            == owner_checksum
        ),
        None,
    )

    if owner_account is None:
        raise PermissionError(
            "Vi Owner khong nam trong danh sach tai khoan "
            "Ganache hien tai. Hay kiem tra Workspace."
        )

    hash_bytes = bytes.fromhex(
        data_hash[2:]
    )

    transaction_hash = (
        contract.functions.issueCertificate(
            certificate_id,
            hash_bytes,
        ).transact({
            "from": owner_account,
        })
    )

    receipt = web3.eth.wait_for_transaction_receipt(
        transaction_hash,
        timeout=120,
    )

    if receipt["status"] != 1:
        raise RuntimeError(
            "Giao dich ghi chung chi len Blockchain that bai."
        )

    return {
        "certificate_id": certificate_id,
        "data_hash": data_hash,
        "transaction_hash": Web3.to_hex(
            transaction_hash
        ),
        "block_number": receipt["blockNumber"],
        "status": "success",
    }


# =====================================================
# 5. XAC MINH CHUNG CHI TREN BLOCKCHAIN
# =====================================================

def verify_certificate(certificate_id, data_hash):
    """
    So sanh ma bam voi du lieu tren Blockchain.
    Tra ve True neu ma bam trung khop.
    """

    certificate_id = validate_certificate_id(
        certificate_id
    )

    data_hash = validate_data_hash(data_hash)

    web3, contract = get_blockchain_contract()

    hash_bytes = bytes.fromhex(
        data_hash[2:]
    )

    result = contract.functions.verifyCertificate(
        certificate_id,
        hash_bytes,
    ).call()

    return bool(result)


# =====================================================
# 6. LAY THONG TIN CHUNG CHI TU BLOCKCHAIN
# =====================================================

def get_certificate(certificate_id):
    """
    Lay thong tin chung chi tu Blockchain.
    """

    certificate_id = validate_certificate_id(
        certificate_id
    )

    web3, contract = get_blockchain_contract()

    data_hash, issued_at, exists = (
        contract.functions.getCertificate(
            certificate_id
        ).call()
    )

    # Chuan hoa bytes32 thanh chuoi hex co tien to 0x
    data_hash_hex = Web3.to_hex(data_hash)

    return {
        "certificate_id": certificate_id,
        "data_hash": validate_data_hash(
            data_hash_hex
        ),
        "issued_at": issued_at,
        "exists": bool(exists),
    }


# =====================================================
# 7. KIEM TRA CHUNG CHI CO TON TAI HAY KHONG
# =====================================================

def certificate_exists(certificate_id):
    """Kiem tra chung chi da duoc ghi len Blockchain."""

    certificate = get_certificate(
        certificate_id
    )

    return certificate["exists"]


# =====================================================
# 8. TAO MA BAM TU THONG TIN CHUNG CHI
# =====================================================

def create_certificate_hash(certificate):
    """
    Tao ma bam tu thong tin chung chi trong database.
    Cung mot bo du lieu se tao cung mot ma bam.
    """

    certificate_data = {
        "certificate_code": certificate.certificate_code,
        "student_name": certificate.student.full_name,
        "class_name": certificate.english_class.name,
        "course_name": certificate.english_class.course.name,
        "issue_date": certificate.issue_date.isoformat(),
        "score": str(certificate.score),
        "classification": certificate.classification,
    }

    json_data = json.dumps(
        certificate_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    data_hash = Web3.keccak(
        text=json_data
    ).hex()

    return validate_data_hash(data_hash)


# =====================================================
# 9. CAP CHUNG CHI TU DATABASE LEN BLOCKCHAIN
# =====================================================

def issue_database_certificate(certificate):
    """
    Ghi chung chi tu database len Blockchain.
    Luu ma bam, transaction hash va block number.
    """

    certificate.refresh_from_db()

    if certificate.blockchain_status == "issued":
        raise ValueError(
            "Chung chi nay da duoc ghi len Blockchain."
        )

    data_hash = create_certificate_hash(
        certificate
    )

    # Neu giao dich loi, khong xoa thong tin giao dich cu
    # va danh dau that bai de nguoi quan tri kiem tra.
    try:
        result = issue_certificate(
            certificate.certificate_code,
            data_hash,
        )

    except Exception:
        certificate.blockchain_status = "failed"

        certificate.save(
            update_fields=[
                "blockchain_status",
            ]
        )

        raise

    # Chi cap nhat database sau khi giao dich thanh cong
    certificate.data_hash = result["data_hash"]
    certificate.transaction_hash = result[
        "transaction_hash"
    ]
    certificate.block_number = result["block_number"]
    certificate.blockchain_status = "issued"

    certificate.save(
        update_fields=[
            "data_hash",
            "transaction_hash",
            "block_number",
            "blockchain_status",
        ]
    )

    return result


# =====================================================
# 10. XAC MINH CHUNG CHI TU DATABASE
# =====================================================

def verify_database_certificate(certificate):
    """
    Tao lai ma bam tu database va so sanh voi Blockchain.
    """

    certificate.refresh_from_db()

    if not certificate.data_hash:
        return {
            "valid": False,
            "message": "Chung chi chua co ma bam Blockchain.",
        }

    if certificate.blockchain_status != "issued":
        return {
            "valid": False,
            "message": "Chung chi chua duoc ghi len Blockchain.",
        }

    # Tao lai hash tu du lieu hien tai
    current_hash = create_certificate_hash(
        certificate
    )

    # Kiem tra du lieu database co bi thay doi khong
    if current_hash != validate_data_hash(
        certificate.data_hash
    ):
        return {
            "valid": False,
            "message": "Du lieu chung chi trong database da thay doi.",
        }

    # Lay du lieu tu Blockchain
    blockchain_data = get_certificate(
        certificate.certificate_code
    )

    if not blockchain_data["exists"]:
        return {
            "valid": False,
            "message": "Khong tim thay chung chi tren Blockchain.",
        }

    # So sanh ma bam hien tai voi ma bam da ghi tren Blockchain
    valid = (
        blockchain_data["data_hash"]
        == current_hash
        and verify_certificate(
            certificate.certificate_code,
            current_hash,
        )
    )

    return {
        "valid": valid,
        "message": (
            "Chung chi hop le."
            if valid
            else "Ma bam khong khop voi Blockchain."
        ),
        "certificate_code": certificate.certificate_code,
        "data_hash": current_hash,
        "transaction_hash": certificate.transaction_hash,
        "block_number": certificate.block_number,
    }



