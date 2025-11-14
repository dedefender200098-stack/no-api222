import json
import random
import uuid
from asyncio import sleep
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from config import RETRIES, PAUSE_BETWEEN_RETRIES
from src.models.contracts import BridgeData, SwapData
from src.neura.tx_utils import create_swap_tx
from src.neura.types import UserData
from src.utils.cherry_solver.client import CherrySolver
from src.utils.common.wrappers.decorators import retry
from src.utils.data.chains import SEPOLIA
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.request_client.curl_cffi_client import CurlCffiClient
from src.utils.user.account import Account


class NeuraClient(Account, CurlCffiClient):
    # noinspection PyMissingConstructor
    def __init__(
            self,
            private_key: str,
            proxy: Proxy,
    ):
        self.private_key = private_key
        self._cherry_solver: Optional[CherrySolver] = None

        self.proxy = proxy
        if proxy:
            self.proxy.attach_client(self)
        self.reinitialize_proxy_clients()
        self.jwt_token = None

        self.auth_headers = {
            'accept': 'application/json',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://neuraverse.neuraprotocol.io',
            'priority': 'u=1, i',
            'privy-app-id': 'cmbpempz2011ll10l7iucga14',
            'privy-ca-id': str(uuid.uuid4()),
            'privy-client': 'react-auth:2.25.0',
            'referer': 'https://neuraverse.neuraprotocol.io/',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://neuraverse.neuraprotocol.io',
            'priority': 'u=1, i',
            'referer': 'https://neuraverse.neuraprotocol.io/',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        }

        self.user_data: Optional[UserData] = None

    def reinitialize_proxy_clients(self):
        Account.__init__(self, private_key=self.private_key, proxy=self.proxy)
        CurlCffiClient.__init__(self, proxy=self.proxy)
        self._cherry_solver = CherrySolver(session=self.session, proxy=self.proxy, verbose=False)

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _get_nonce(self) -> Optional[str]:
        turnstile_token = await self._cherry_solver.solve_captcha(
            captcha_name='turnstile',
            data_for_solver={
                'websiteKey': '0x4AAAAAAAM8ceq5KhP1uJBt',
                'websiteURL': 'https://neuraverse.neuraprotocol.io/'
            }
        )
        if not turnstile_token:
            logger.error(f'[{self.wallet_address}] | Failed to solve turnstile captcha for authorization.')
            return None

        json_data = {
            'address': self.wallet_address,
            'token': turnstile_token
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://privy.neuraverse.neuraprotocol.io/api/v1/siwe/init',
            json=json_data,
            headers=self.auth_headers
        )
        if status == 200:
            return response_json['nonce']
        logger.error(f'[{self.wallet_address}] | Failed to get nonce for authorization | Status: {status}')

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _send_auth_request(self, message: str, signature: str) -> Optional[bool | str]:
        json_data = {
            'message': message,
            'signature': signature,
            'chainId': 'eip155:267',
            'walletClientType': 'rabby_wallet',
            'connectorType': 'injected',
            'mode': 'login-or-sign-up',
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://privy.neuraverse.neuraprotocol.io/api/v1/siwe/authenticate',
            headers=self.auth_headers,
            json=json_data
        )
        if status == 200:
            token = response_json['identity_token']
            logger.success(f'[{self.wallet_address}] | Successfully authorized into Neuraverse!')
            self.jwt_token = token
            self.headers.update({'authorization': f'Bearer {token}'})
            return True

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _process_action(self, action_type: str) -> Optional[bool]:
        json_data = {
            'type': action_type,
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://neuraverse-testnet.infra.neuraprotocol.io/api/events',
            headers=self.headers,
            json=json_data
        )
        if status == 200:
            return True

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _send_request_token_request(self) -> Optional[bool]:
        headers = self.headers.copy()
        headers['accept'] = 'text/x-component'
        headers['next-action'] = '78459a487b08c86189d6e3cab0b36d8f76eb2b632a'

        params = {
            'section': 'faucet',
        }
        data = f'["{self.wallet_address}",267,"{self.jwt_token}",true]'

        response = await self.session.request(
            method="POST",
            url='https://neuraverse.neuraprotocol.io/',
            headers=headers,
            data=data,
            params=params
        )
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith("1:"):
                    response_json = json.loads(line[2:])
                    if not response_json['status'] in ['error', 'failure']:
                        logger.success(f'[{self.wallet_address}] | Successfully requested tokens from faucet')
                        return True
                    logger.error(
                        f'[{self.wallet_address}] | Failed to request tokens | Response: {response_json['message']}'
                    )

    async def request_tokens(self) -> Optional[bool]:
        await self._process_action(action_type='faucet:visit')
        await self._process_action(action_type='game:visitFountain')

        tokens_requested = await self._send_request_token_request()
        if tokens_requested:
            await self._process_action(action_type='faucet:claimTokens')
            return True

    async def authorize(self) -> Optional[bool]:
        nonce = await self._get_nonce()
        if not nonce:
            return None

        iso_time = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        msg = f'neuraverse.neuraprotocol.io wants you to sign in with your Ethereum account:\n{self.wallet_address}\n\nBy signing, you are proving you own this wallet and logging in. This does not initiate a transaction or cost any fees.\n\nURI: https://neuraverse.neuraprotocol.io\nVersion: 1\nChain ID: 267\nNonce: {nonce}\nIssued At: {iso_time}\nResources:\n- https://privy.io'
        signature = self.get_signature(message=msg)

        return await self._send_auth_request(message=msg, signature=signature)

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def get_user(self) -> Optional[UserData]:
        response_json, status = await self.make_request(
            method="GET",
            url='https://neuraverse-testnet.infra.neuraprotocol.io/api/account',
            headers=self.headers
        )
        if status == 200:
            self.user_data = UserData.from_dict(response_json)
            return self.user_data

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _collect_pulse(self, pulse_id: str):
        json_data = {
            'type': 'pulse:collectPulse',
            'payload': {
                'id': pulse_id,
            },
        }
        response_json, status = await self.make_request(
            method="POST",
            url='https://neuraverse-testnet.infra.neuraprotocol.io/api/events',
            headers=self.headers,
            json=json_data
        )
        if status == 200:
            logger.success(f'[{self.wallet_address}] | Pulse {pulse_id} has been successfully collected!')
            return True

    async def collect_pulses(self) -> bool:
        await self._process_action(action_type='game:visitFountain')

        uncollected_pulses = [
            pulse for pulse in self.user_data.pulses.data
            if not pulse.is_collected
        ]
        if not uncollected_pulses:
            logger.success(f'[{self.wallet_address}] | All pulses has been already collected.')
            return True

        collected_times = 0
        for pulse_obj in uncollected_pulses:
            collected = await self._collect_pulse(pulse_obj.id)
            if collected:
                collected_times += 1

            await sleep(random.randint(5, 10))

        return collected_times > 0

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _get_tasks(self) -> Optional[list[dict]]:
        response_json, status = await self.make_request(
            method="GET",
            url='https://neuraverse-testnet.infra.neuraprotocol.io/api/tasks',
            headers=self.headers
        )
        if status == 200:
            return response_json['tasks']

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def _claim_task(self, task_id: str) -> Optional[bool]:
        response_json, status = await self.make_request(
            method="POST",
            url=f'https://neuraverse-testnet.infra.neuraprotocol.io/api/tasks/{task_id}/claim',
            headers=self.headers
        )
        if status == 200:
            points = response_json['points']
            name = response_json['name']
            logger.success(f'[{self.wallet_address}] | Successfully claimed {name} task and earned {points} points!')
            return True

    async def claim_tasks(self) -> Optional[bool]:
        await self._process_action(action_type='game:visitFountain')

        all_tasks = await self._get_tasks()
        if not all_tasks:
            return None

        claimable_tasks = [task for task in all_tasks if task['status'] == 'claimable']
        if not claimable_tasks:
            logger.warning(f'[{self.wallet_address}] | Claimable tasks not found.')
            return None

        logger.debug(f'[{self.wallet_address}] | Found {len(claimable_tasks)} claimable tasks. Claiming...')

        claimed_times = 0
        for task in claimable_tasks:
            claimed = await self._claim_task(task['id'])
            if claimed:
                claimed_times += 1

            await sleep(random.randint(5, 10))

        return claimed_times > 0

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def bridge_tokens(self) -> Optional[bool]:
        bridge_visited = await self._process_action(action_type='bridge:visit')
        if not bridge_visited:
            return None

        sepolia_account = Account(private_key=self.private_key, rpc=SEPOLIA.rpc, proxy=self.proxy)

        native_balance = await sepolia_account.get_wallet_balance(is_native=True)
        if native_balance == 0:
            logger.error(f'[{self.wallet_address}] | Sepolia native balance is 0.')
            return None

        sepolia_ankr_balance = await sepolia_account.get_wallet_balance(
            is_native=False, address='0xB88Ca91Fef0874828e5ea830402e9089aaE0bB7F'
        )

        await sepolia_account.approve_token(
            amount=sepolia_ankr_balance,
            private_key=self.private_key,
            from_token_address='0xB88Ca91Fef0874828e5ea830402e9089aaE0bB7F',
            spender=BridgeData.address,
            address_wallet=self.wallet_address,
            web3=sepolia_account.web3
        )

        bridge_contract = self.load_contract(
            address=BridgeData.address,
            abi=BridgeData.abi,
            web3=sepolia_account.web3
        )

        tx = await bridge_contract.functions.deposit(
            sepolia_ankr_balance,
            self.wallet_address
        ).build_transaction({
            'value': 0,
            'nonce': await sepolia_account.web3.eth.get_transaction_count(self.wallet_address),
            'from': self.wallet_address,
            'gasPrice': await sepolia_account.web3.eth.gas_price
        })
        tx_hash = await sepolia_account.sign_transaction(tx)
        confirmed = await sepolia_account.wait_until_tx_finished(tx_hash)
        if confirmed and tx_hash:
            logger.success(
                f'[{self.wallet_address}] | Successfully bridged {sepolia_ankr_balance / 10 ** 18} ANKR '
                f'| TX: https://sepolia.etherscan.io/tx/{tx_hash}'
            )
            await self._process_action(action_type='bridge:depositEth')
            return True

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def swap(self, from_token: str, to_token: str, swap_percentage: float) -> Optional[bool]:
        await self._process_action(action_type='game:visitFountain')

        contract = self.load_contract(
            address=SwapData.router_address,
            abi=SwapData.router_abi,
            web3=self.web3
        )
        is_native = from_token == 'ANKR'
        balance = await self.get_wallet_balance(
            is_native=is_native, address=tokens['NEURA'][from_token]
        )
        amount = int(balance * swap_percentage)

        if not is_native:
            await self.approve_token(
                amount=amount,
                private_key=self.private_key,
                from_token_address=tokens['NEURA'][from_token],
                spender=SwapData.router_address,
                address_wallet=self.wallet_address,
                web3=self.web3
            )

        tx = await create_swap_tx(
            self,
            from_token_name=from_token,
            to_token_name=to_token,
            from_token_address=tokens['NEURA'][from_token] if not from_token == 'ANKR' else tokens['NEURA']['WANKR'],
            to_token_address=tokens['NEURA'][to_token] if not to_token == 'ANKR' else tokens['NEURA']['WANKR'],
            contract=contract,
            amount=amount
        )
        tx_hash = await self.sign_transaction(tx)
        confirmed = await self.wait_until_tx_finished(tx_hash)
        if confirmed and tx_hash:
            logger.success(
                f'[{self.wallet_address}] | Successfully swapped {from_token} => {to_token} '
                f'| TX: https://testnet-blockscout.infra.neuraprotocol.io/tx/{tx_hash}'
            )
            await self._process_action(action_type='bridge:depositEth')
            return True

    @retry(retries=RETRIES, delay=PAUSE_BETWEEN_RETRIES, backoff=1.5)
    async def send_message(self, agent: str, message: str) -> Optional[str]:
        await self._process_action(action_type="game:visitFountain")

        json_data = {
            'messages': [
                {
                    'role': 'user',
                    'content': message,
                },
            ],
        }
        response_json, status = await self.make_request(
            method="POST",
            url=f'https://neuraverse-testnet.infra.neuraprotocol.io/api/game/chat/validator/{agent}',
            headers=self.headers,
            json=json_data
        )
        if status == 200:
            return response_json['messages'][0]['content']
        elif status == 429:
            return "RATE_LIMIT"
