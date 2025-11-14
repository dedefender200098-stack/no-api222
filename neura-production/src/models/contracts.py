from dataclasses import dataclass


@dataclass
class ERC20:
    abi: str = open('./assets/abi/erc20.json', 'r').read()


@dataclass
class BridgeData:
    address: str = '0xc6255a594299F1776de376d0509aB5ab875A6E3E'
    abi: str = open('./assets/abi/bridge.json', 'r').read()


@dataclass
class SwapData:
    router_address: str = '0x5AeFBA317BAba46EAF98Fd6f381d07673bcA6467'
    router_abi: str = open('./assets/abi/router.json', 'r').read()

    quoter_address: str = '0xE94de02e52Eaf9F0f6Bf7f16E4927FcBc2c09bC7'
    quoter_abi: str = open('./assets/abi/quoter.json', 'r').read()
