from src.utils.runner import *

module_handlers = {
    'FAUCET': process_faucet,
    'COLLECT_PULSES': process_collect_pulses,
    'BRIDGE': process_bridge,
    'CYCLE_SWAPS': process_cycle_swaps,
    'CLAIM_TASKS': process_claim_tasks,
    'CHAT_WITH_AGENTS': process_chat_with_agents
}
