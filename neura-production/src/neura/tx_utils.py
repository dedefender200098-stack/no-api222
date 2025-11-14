from time import time
from typing import Iterable

from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.contracts import SwapData


def _normalize_addr(addr: str) -> str:
    if not (isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42):
        raise ValueError(f"Invalid address: {addr}")
    return addr[2:].lower()


def _encode_path(token_in: str, token_out: str) -> str:
    a = _normalize_addr(token_in)
    b = _normalize_addr(token_out)
    zeros20 = "00" * 20
    return "0x" + a + zeros20 + b


def _encode_path_univ3(addresses: Iterable[str], fees: Iterable[int]) -> str:
    addrs = list(addresses)
    fs = list(fees)
    if len(addrs) < 2:
        raise ValueError("Path must contain at least two addresses")
    if len(fs) != len(addrs) - 1:
        raise ValueError("fees length must be len(addresses) - 1")

    out = bytearray()
    for i, addr in enumerate(addrs):
        out += bytes.fromhex(_normalize_addr(addr))
        if i < len(fs):
            fee = fs[i]
            if not (0 <= fee < 1 << 24):
                raise ValueError(f"Invalid fee: {fee}")
            out += fee.to_bytes(3, "big")
    return "0x" + out.hex()


def get_path(from_token_address: str, to_token_address: str, from_token_name: str, to_token_name: str) -> str:
    if from_token_address.lower() == to_token_address.lower():
        raise ValueError("from_token_address and to_token_address must be different")
    return _encode_path(from_token_address, to_token_address)


async def get_min_amount_out(
        self,
        from_token_address: str,
        to_token_address: str,
        from_token_name: str,
        to_token_name: str,
        amount: int
):
    quoter = self.load_contract(
        address=SwapData.quoter_address,
        abi=SwapData.quoter_abi,
        web3=self.web3
    )
    path = get_path(
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        from_token_name=from_token_name,
        to_token_name=to_token_name
    )
    min_amount_out, _, _, _, _, _ = await quoter.functions.quoteExactInput(
        path,
        amount
    ).call()
    min_amount_out = min_amount_out[0]
    return int(min_amount_out - (min_amount_out / 100 * 20))


async def create_swap_tx(
        self,
        from_token_name: str,
        to_token_name: str,
        from_token_address: str,
        to_token_address: str,
        contract: AsyncContract,
        amount: int,
) -> TxParams:
    min_amount_out = await get_min_amount_out(
        self,
        from_token_address,
        to_token_address,
        from_token_name,
        to_token_name,
        amount
    )
    deadline = int(time() * 1000 + 1800)
    transaction_data = contract.encode_abi(
        abi_element_identifier="exactInputSingle",
        args=[(
            self.web3.to_checksum_address(from_token_address),
            self.web3.to_checksum_address(to_token_address),
            self.web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            self.wallet_address if from_token_name == 'ANKR'
            else self.web3.to_checksum_address('0x0000000000000000000000000000000000000000'),
            deadline,
            amount,
            min_amount_out,
            0
        )]
    )

    multicall_data = [transaction_data]

    if to_token_name == 'ANKR':
        unwrap_data = contract.encode_abi(
            abi_element_identifier="unwrapWNativeToken",
            args=[
                min_amount_out,
                self.wallet_address
            ]
        )
        multicall_data.append(unwrap_data)

    gas_estimate = await contract.functions.multicall(multicall_data).estimate_gas({
        'from': self.wallet_address,
        'value': amount if from_token_name == 'ANKR' else 0
    })
    gas_limit = int(gas_estimate * 1.15)

    tx = await contract.functions.multicall(
        [transaction_data]
    ).build_transaction({
        'value': amount if from_token_name == 'ANKR' else 0,
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'from': self.wallet_address,
        'gasPrice': int(await self.web3.eth.gas_price * 1.2),
        'gas': gas_limit
    })

    return tx
