class Chain:
    def __init__(self, chain_id: int, rpc: str, scan: str, native_token: str) -> None:
        self.chain_id = chain_id
        self.rpc = rpc
        self.scan = scan
        self.native_token = native_token


BASE = Chain(
    chain_id=8453,
    rpc='https://base.meowrpc.com',
    scan='https://basescan.org/tx',
    native_token='ETH'
)

NEURA = Chain(
    chain_id=267,
    rpc='https://testnet.rpc.neuraprotocol.io',
    scan='https://testnet-blockscout.infra.neuraprotocol.io/tx',
    native_token='ANKR'
)

OP = Chain(
    chain_id=10,
    rpc='https://optimism.drpc.org',
    scan='https://optimistic.etherscan.io/tx',
    native_token='ETH',
)

ARB = Chain(
    chain_id=42161,
    rpc='https://arbitrum.meowrpc.com',
    scan='https://arbiscan.io/tx',
    native_token='ETH',
)

BSC = Chain(
    chain_id=56,
    rpc='https://bsc-pokt.nodies.app',
    scan='https://bscscan.com/tx',
    native_token='BNB'
)

LINEA = Chain(
    chain_id=59144,
    rpc='https://linea-rpc.publicnode.com',
    scan='https://lineascan.build/tx',
    native_token='ETH'
)

SEPOLIA = Chain(
    chain_id=11155111,
    rpc='https://ethereum-sepolia-rpc.publicnode.com',
    scan='https://sepolia.etherscan.io/tx',
    native_token='ETH'
)

chain_mapping = {
    'BASE': BASE,
    'ARBITRUM ONE': ARB,
    'ARB': ARB,
    'OP': OP,
    'OPTIMISM': OP,
    'BSC': BSC,
    'LINEA': LINEA,
    'SEPOLIA': SEPOLIA,
}
