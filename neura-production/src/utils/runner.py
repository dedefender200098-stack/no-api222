import random
from asyncio import sleep
from typing import Optional

from loguru import logger

from config import PAUSE_BETWEEN_MODULES, CycleSwapSettings, ChatSettings
from src.models.route import Route
from src.neura.client import NeuraClient


async def process_faucet(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None

    return await neura_client.request_tokens()


async def process_collect_pulses(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None
    user = await neura_client.get_user()
    if not user:
        return None

    return await neura_client.collect_pulses()


async def process_claim_tasks(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None

    return await neura_client.claim_tasks()


async def process_bridge(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None

    return await neura_client.bridge_tokens()


async def process_chat_with_agents(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None

    num_messages = random.randint(ChatSettings.num_messages[0], ChatSettings.num_messages[1])
    start_messages = ChatSettings.greet_messages
    agents = ['talon', 'borl', 'eldros', 'bullhorn', 'oomi', 'quiver', 'ember',
              'vimri', 'fenna', 'brama', 'jakar', 'izzy', 'neko']

    previous_message = random.choice(start_messages)

    for i in range(num_messages):
        current_agent = random.choice(agents)
        response = await neura_client.send_message(
            agent=current_agent,
            message=previous_message
        )
        if not response:
            logger.warning(f"[WARN] No response from agent {current_agent.capitalize()}")
            await sleep(10)
            continue
        elif response == 'RATE_LIMIT':
            logger.warning(f'[{neura_client.wallet_address}] | Rate limit reached. Sleeping...')
            await sleep(60)
            continue

        logger.debug(f"[{current_agent.capitalize()}] → {response}")
        previous_message = response

        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1])
        logger.debug(f'[{neura_client.wallet_address}] | Sleeping {random_sleep} seconds before next message...')
        await sleep(random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]))

    return True


async def process_cycle_swaps(route: Route) -> Optional[bool]:
    neura_client = NeuraClient(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy,
    )
    authed = await neura_client.authorize()
    if not authed:
        return None

    cycles = random.randint(CycleSwapSettings.cycles[0], CycleSwapSettings.cycles[1])

    for _ in range(cycles):
        token = random.choice(CycleSwapSettings.token)
        swap_percentage = random.uniform(CycleSwapSettings.swap_percentage[0], CycleSwapSettings.swap_percentage[1])

        tx_hash = await neura_client.swap(
            from_token='ANKR',
            to_token=token,
            swap_percentage=swap_percentage
        )

        if tx_hash:
            random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
                PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

            logger.info(f'Sleeping {random_sleep} seconds before {token} => ANKR swap...')
            await sleep(random_sleep)

            tx_hash = await neura_client.swap(
                from_token=token,
                to_token='ANKR',
                swap_percentage=1
            )

        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
            PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

        logger.info(f'Sleeping {random_sleep} seconds before next iteration...')
        await sleep(random_sleep)

    return True
