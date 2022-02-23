import time
import rlp
from client_sdk_python import HTTPProvider, Web3
from client_sdk_python.packages.platon_account.internal.transactions import bech32_address_bytes
from hexbytes import HexBytes
from platon.platon import Platon

from common.log import log
from environment import Node, TestConfig
from tests.conftest import upgrade_proposal
from tests.lib import get_the_dynamic_parameter_gas_fee, assert_code, get_pledge_list, get_block_count_number


def test_1769_call_return_32000(client_consensus):
    client = client_consensus
    address = client.economic.account.account_with_money['address']
    for i in range(1000):
        nonce = client.node.eth.getTransactionCount(address)
        log.info(f'nonce: {nonce}')
        assert type(nonce) is int

    for i in range(1000):
        balance = client.node.eth.getBalance(address)
        log.info(f'balance: {balance}')
        assert type(balance) is int


def test_1758_estimate_pip_without_gas_price(client_consensus):
    client = client_consensus
    pip = client.pip
    pip_id = str(time.time())
    data = rlp.encode([rlp.encode(int(2000)), rlp.encode(bytes.fromhex(pip.node.node_id)), rlp.encode(pip_id)])
    expect_gas = 350000 + get_the_dynamic_parameter_gas_fee(data)
    log.info(f'expect_gas is: {expect_gas}')
    # 使用处于门槛金额的地址去预估gas
    txn = {"to": client.pip.pip.pipAddress, "data": data}
    estimated_gas = client.node.eth.estimateGas(txn)
    log.info(f'estimated_gas is: {estimated_gas}')
    assert expect_gas == estimated_gas


# def test_0000_estimate_pip_use_threshold_balance(client_consensus):
#     client = client_consensus
#     pip = client.pip
#     pip_id = str(time.time())
#     data = rlp.encode([rlp.encode(int(2000)), rlp.encode(bytes.fromhex(pip.node.node_id)), rlp.encode(pip_id)])
#     expect_gas = 350000 + get_the_dynamic_parameter_gas_fee(data)
#     log.info(f'expect_gas is: {expect_gas}')
#     # 使用处于门槛金额的地址去预估gas
#     gas_price = 1000000000
#     address, _ = client.economic.account.generate_account(client.node.web3, expect_gas * gas_price)
#     log.info(f'new address balance is: {client.node.eth.getBalance(address)}')
#     txn = {"from": address, "to": client.pip.pip.pipAddress, "data": data, "gasPrice": gas_price}
#     estimated_gas = client.node.eth.estimateGas(txn)
#     log.info(f'estimated_gas is: {estimated_gas}')
#     assert expect_gas == estimated_gas


def test_1583_EI_BC_090(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    @describe: 0.13.2节点质押被A/B委托（B是自由金额委托），等待三个结算周期 A委托失败 升级到0.16.0，可领取委托分红奖励正确
    @step:
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another, mount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address,  amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)

    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i == 0:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id,
                                              amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id,
                                               amount=economic.delegate_limit * 2)
            assert_code(result, 0)

    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)

    amount1 = economic.delegate_limit
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan,
                                                       economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq',
                                                           amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for delegate_address in delegate_address_list:
        result = node.ppos.getDelegateReward(delegate_address)['Ret']
        reward = result[0]['reward']
        print(f'Bug重现后用户当前可领取分红reward={reward},delegate_address={delegate_address}')
        assert reward == 0

    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    print(f'委托收益池金额={balance_delegaterewardaddress_befor}')
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        print(f'升级前的候选人信息candidate_info={candidate_info}')
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client
    print(delegate_reward_total_befor)

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for delegate_address in delegate_address_list:
        result = node.ppos.getDelegateReward(delegate_address)['Ret']
        reward = result[0]['reward']
        print(f'升级后后用户当前可领取分红reward={reward},delegate_address={delegate_address}')
        assert reward == 0

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i], i))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[
        5] == 267379679144385026737

    economic.wait_settlement(node)

    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    print(f'升级后委托收益池金额={balance_delegaterewardaddress_after}')

    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        print(f'candidate_info={candidate_info}')
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    print(f'delegate_reward_total={delegate_reward_total}')
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress, lastround_end_block)
    print(f'升级后查询收益轮委托收益池金额={balance_delegaterewardaddress_after}')
    if delegate_reward_total == delegate_reward_total_befor:
        assert 0 < balance_delegaterewardaddress_befor - builtin_balance_amount - balance_delegaterewardaddress_after < 6
        for delegate_address in delegate_address_list:
            result = node.ppos.getDelegateReward(delegate_address)['Ret']
            reward = result[0]['reward']
            print(f'升级后后用户当前可领取分红reward={reward},delegate_address={delegate_address}')
            assert reward == 0
    else:
        assert 0 < delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after- balance_delegaterewardaddress_befor + builtin_balance_amount




def test_1583_EI_BC_091(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    @describe: 0.13.2节点质押被A/B委托（B是自由金额委托），等待三个结算周期 A委托失败，B撤销委托， 升级到0.16.0，可领取委托分红奖励正确
    @step:
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another, amount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address, amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)

    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i == 0:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)
    amount1 = economic.delegate_limit
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan,
                                                       economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0,economic.genesis.economicModel.innerAcc.cdfAccount, amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    stakingnum = client2.staking.get_stakingblocknum(client2.node)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address_list[3], amount=economic.delegate_limit)
    assert_code(result, 0)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address_list[5], amount=economic.delegate_limit * 2)
    assert_code(result, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for delegate_address in delegate_address_list[:5]:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for delegate_address in delegate_address_list[:5]:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i], i))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[
        5] == 267379679144385026737

    economic.wait_settlement(node)
    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress, lastround_end_block)
    if delegate_reward_total == delegate_reward_total_befor:
        assert 0 < balance_delegaterewardaddress_befor - builtin_balance_amount - balance_delegaterewardaddress_after < 6
        for delegate_address in delegate_address_list:
            reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
            assert reward == 0
    else:
        assert 0 < delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after - balance_delegaterewardaddress_befor + builtin_balance_amount




def test_1583_EI_BC_092(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    @describe: 0.13.2节点质押被A/B委托（B是自由金额委托），等待三个结算周期 A委托失败 升级到0.16.0，可领取委托分红奖励正确
    @step:
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another, amount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address, amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)

    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i in [0]:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)

    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)

    amount1 = economic.delegate_limit
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan, economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    receive_reward = 0
    for i in range(len(delegate_address_list)):
        result = node.ppos.getDelegateReward(delegate_address_list[i])['Ret']
        reward = result[0]['reward']
        if i % 2 == 0:
            receive_reward += reward

    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for delegate_address in delegate_address_list:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 3584, client.pip.cfg.PLATON_NEW_BIN2)
    upgrade_proposal(all_clients, client_consensus, 3840, client.pip.cfg.PLATON_NEW_BIN1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for delegate_address in delegate_address_list:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i], i))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[5] == 267379679144385026737

    economic.wait_settlement(node)
    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        print(f'candidate_info={candidate_info}')
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress, lastround_end_block)
    if delegate_reward_total == delegate_reward_total_befor:
        assert 0 < balance_delegaterewardaddress_befor - builtin_balance_amount - balance_delegaterewardaddress_after < 6
        for delegate_address in delegate_address_list:
            reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
            assert reward == 0
    else:
        assert 0 < delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after - balance_delegaterewardaddress_befor + builtin_balance_amount



def test_1583_EI_BC_093(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    @describe: 0.13.2节点质押被A/B委托（B是自由金额委托），等待三个结算周期 A委托失败，B撤销委托， 升级0.13.2-0.14.0-0.15.0-0.15.1-0.16.0，可领取委托分红奖励正确
    @step:
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[
        3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another,
                                            amount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address,
                                                       amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)

    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i in [0]:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)

    amount1 = economic.delegate_limit
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan, economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    stakingnum = client2.staking.get_stakingblocknum(client2.node)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address_list[3], amount=economic.delegate_limit)
    assert_code(result, 0)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address_list[5], amount=economic.delegate_limit * 2)
    assert_code(result, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for delegate_address in delegate_address_list[:5]:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 3584, client.pip.cfg.PLATON_NEW_BIN2)
    upgrade_proposal(all_clients, client_consensus, 3840, client.pip.cfg.PLATON_NEW_BIN1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for delegate_address in delegate_address_list[:5]:
        reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
        assert reward == 0

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i], i))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[
        5] == 267379679144385026737

    economic.wait_settlement(node)

    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress,
                                                                     lastround_end_block)
    if delegate_reward_total == delegate_reward_total_befor:
        assert 0 < balance_delegaterewardaddress_befor - builtin_balance_amount - balance_delegaterewardaddress_after < 6
        for delegate_address in delegate_address_list:
            reward = node.ppos.getDelegateReward(delegate_address)['Ret'][0]['reward']
            assert reward == 0
    else:
        assert 0 < delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after - balance_delegaterewardaddress_befor + builtin_balance_amount




def  test_1583_EI_BC_102(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    要用0.15.1的包跑
    @describe: 0.15.1节点质押被A/B委托，等待三个结算周期 A委托失败 链id为0.15.1测试网id，升级到0.16.0，没有平账步骤
    @step:L
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another, amount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address, amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)

    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i in [0]:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)
    amount1 = economic.genesis.economicModel.restricting.minimumRelease
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan, economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for i in range(len(delegate_address_list)):
        reward = node.ppos.getDelegateReward(delegate_address_list[i])['Ret'][0]['reward']
        if i%2 == 0:
            assert reward == 0
        else:
            assert reward
    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for i in range(len(delegate_address_list)):
        reward = node.ppos.getDelegateReward(delegate_address_list[i])['Ret'][0]['reward']
        if i%2 == 0:
            assert reward == 0
        else:
            assert reward

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i]))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[5] == 267379679144385026737

    economic.wait_settlement(node)

    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress, lastround_end_block)
    if delegate_reward_total == delegate_reward_total_befor:
        assert balance_delegaterewardaddress_befor == balance_delegaterewardaddress_after
    else:
        assert  delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after- balance_delegaterewardaddress_befor



def  test_1583_EI_BC_103(clients_new_node, clients_consensus, all_clients, client_consensus):
    """
    要用0.15.1的包跑
    @describe: 0.15.1节点质押被A/B委托，等待三个结算周期 A委托失败 升级到0.16.0，链id与主网一致时，有平账
    @step:L
    - 1. 未生效期A账号委托A节点
    - 2. 未生效期B账号委托A节点
    - 3. 生效期A委托A节点，失败
    - 4. 查看A\B的可领取委托收益
    - 5. 升级到0.16.0
    @expect:
    - 1. A\B委托可领取分红分别都正确
    """
    client, client1, client2, client3 = clients_new_node[0], clients_new_node[1], clients_new_node[2], clients_new_node[3]
    economic = client.economic
    node = client.node
    node2 = client2.node
    builtin_balance_amount = 1225490196078431372544
    prikey1 = '1db04a0cd453d554f9de99d711ac4569d3a4ff408e1aaf0c03878daccea9601e'
    prikey2 = 'b521bc4a0dd5b7da9e60f232d0c0e1a92963c144999d3c0ce30a95f0345c4b5c'
    prikey3 = '1511c10b05396aa51c0ec2030dd311adac60ee4599961dbdcdd94697eedcdd33'

    staking_address_another, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 11)
    result = client3.staking.create_staking(0, staking_address_another, staking_address_another, amount=economic.create_staking_limit * 10, reward_per=0)
    assert_code(result, 0)

    for staking_client in clients_new_node[:3]:
        staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 3)
        result = staking_client.staking.create_staking(0, staking_address, staking_address, amount=economic.create_staking_limit * 2, reward_per=1000)
        assert_code(result, 0)
    delegate_address_list = []
    prinkey_list = [prikey1, prikey2, prikey3]
    for prikey in prinkey_list:
        delegate_address1, _ = economic.account.generate_account(node.web3, economic.delegate_limit * 3)
        delegate_address_list.append(delegate_address1)
        delegate_address2 = client.node.personal.importRawKey(prikey, '88888888')
        result = economic.account.sendTransaction(node.web3, '', economic.account.account_with_money['address'],
                                                  delegate_address2, node.eth.gasPrice, 21000,
                                                  economic.delegate_limit * 3)
        account = {
            "address": delegate_address2,
            "nonce": 0,
            "balance": economic.delegate_limit * 3,
            "prikey": prikey,
        }
        economic.account.accounts[delegate_address2] = account
        delegate_address_list.append(delegate_address2)

    for i in range(6):
        if i == 0:
            result = client.delegate.delegate(0, delegate_address_list[i], node.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
        elif i in [2, 4, 5]:
            result = client2.delegate.delegate(0, delegate_address_list[i], node2.node_id, amount=economic.delegate_limit * 2)
            assert_code(result, 0)
    result = client.delegate.delegate(0, delegate_address_list[1], node.node_id)
    assert_code(result, 0)
    amount1 = economic.genesis.economicModel.restricting.minimumRelease
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1}]
    result = client1.restricting.createRestrictingPlan(delegate_address_list[3], plan, economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client2.delegate.delegate(1, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)
    result = client2.delegate.delegate(0, delegate_address_list[3], node2.node_id)
    assert_code(result, 0)

    assert delegate_address_list[1] == 'atp1g004udw6gy2z2vc4t5d7a77qdrlx3nk07ce9fv'
    assert delegate_address_list[3] == 'atp1zc3k2zd7j72d3h045h43hgzgy8wsvan2lnpegt'
    assert delegate_address_list[5] == 'atp13t9ml06m5q5p6yl277xagwhl734zhl2dteywzw'

    economic.wait_settlement(node)
    for clinet_consensus in clients_consensus:
        result = clinet_consensus.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=economic.create_staking_limit * 10)
        assert_code(result, 0)

    economic.wait_settlement(node)
    fail_result = client.delegate.delegate(0, delegate_address_list[0], amount=economic.delegate_limit)
    assert_code(fail_result, 301111)
    fail_result1 = client2.delegate.delegate(0, delegate_address_list[2], amount=economic.delegate_limit * 2)
    assert_code(fail_result1, 301111)
    fail_result2 = client2.delegate.delegate(0, delegate_address_list[4], amount=economic.delegate_limit * 2)
    assert_code(fail_result2, 301111)

    withdraw_delegate_reward_result = client.delegate.withdraw_delegate_reward(delegate_address_list[0])
    assert_code(withdraw_delegate_reward_result, 0)
    withdraw_delegate_reward_result1 = client2.delegate.withdraw_delegate_reward(delegate_address_list[2])
    assert_code(withdraw_delegate_reward_result1, 0)
    withdraw_delegate_reward_result2 = client2.delegate.withdraw_delegate_reward(delegate_address_list[4])
    assert_code(withdraw_delegate_reward_result2, 0)

    balance_list_befor = []
    for i in range(len(delegate_address_list)):
        balance_list_befor.insert(i, node.eth.getBalance(delegate_address_list[i]))

    for i in range(len(delegate_address_list)):
        reward = node.ppos.getDelegateReward(delegate_address_list[i])['Ret'][0]['reward']
        if i%2 == 0:
            assert reward == 0
        else:
            assert reward

    balance_delegaterewardaddress_befor = client.node.eth.getBalance(client.ppos.delegateRewardAddress)
    assert balance_delegaterewardaddress_befor > builtin_balance_amount, "收益池金额小于包内置金额"

    delegate_reward_total_befor = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward_client = candidate_info['DelegateRewardTotal']
            delegate_reward_total_befor += delegate_reward_client

    economic.wait_settlement(node, 1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for i in range(len(delegate_address_list)):
        reward = node.ppos.getDelegateReward(delegate_address_list[i])['Ret'][0]['reward']
        if i%2 == 0:
            assert reward == 0
        else:
            assert reward

    balance_list_after = []
    for i in range(len(delegate_address_list)):
        balance_list_after.insert(i, node.eth.getBalance(delegate_address_list[i]))
        print(node.eth.getBalance(delegate_address_list[i]))
    assert balance_list_befor[0] == balance_list_after[0] and balance_list_befor[2] == balance_list_after[2] and \
           balance_list_befor[4] == balance_list_after[4]
    assert balance_list_after[1] - balance_list_befor[1] == 690730837789661319070
    assert balance_list_after[3] - balance_list_befor[3] == balance_list_after[5] - balance_list_befor[
        5] == 267379679144385026737

    economic.wait_settlement(node)


    delegate_reward_total = 0
    for client_node in all_clients:
        candidate_info = client_node.ppos.getCandidateInfo(client_node.node.node_id)['Ret']
        if client.node.node_id == client_node.node.node_id or client2.node.node_id == client_node.node.node_id:
            delegate_reward = candidate_info['DelegateRewardTotal']
            delegate_reward_total += delegate_reward
    lastround_end_block = economic.get_switchpoint_by_settlement(client.node) - 160
    balance_delegaterewardaddress_after = client.node.eth.getBalance(client.ppos.delegateRewardAddress, lastround_end_block)
    if delegate_reward_total == delegate_reward_total_befor:
        assert balance_delegaterewardaddress_befor - balance_delegaterewardaddress_after == builtin_balance_amount
    else:
        assert  delegate_reward_total - delegate_reward_total_befor == balance_delegaterewardaddress_after- balance_delegaterewardaddress_befor + builtin_balance_amount





def test_1654_continuous_upgrade_zero_out_block_N(clients_new_node, client_consensus, all_clients):
    """
    0.13.2非内置节点（无替换节点，自由金额质押）零出块处罚一次，小于质押金额且恢复节点未被剔除候选人列表，验证人列表，共识验证人列表，升级0.13.2-0.14.0-0.15.0-0.16.0，被剔除候选人列表，验证人列表，共识验证人列表
    """
    sub_share = 798328877005347593582890
    for i in range(len(clients_new_node)-1):
        if clients_new_node[i].node.node_id == '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf':
            client, client1 = clients_new_node[i], clients_new_node[i+1]
            break
    else:
        client, client1 = clients_new_node[3], clients_new_node[0]
    client2 = client_consensus
    target_node_id = client.node.node_id
    address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    address1, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.staking.create_staking(0, address, address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    result = client1.staking.create_staking(0, address1, address1, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    stakingnum = client.staking.get_stakingblocknum(client.node)
    print(f'stakingnum={stakingnum}')
    assert stakingnum == 25
    delegate_address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.delegate.delegate(0, delegate_address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)

    # Next settlement period
    client.economic.wait_settlement(client.node)
    verifierlist = get_pledge_list(client.ppos.getVerifierList)
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id
    log.info("Close one node")
    client.node.stop()
    node = client1.node

    log.info("The next  periods")
    client1.economic.wait_settlement(node)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address, client.node.node_id, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    assert client.node.node_id not in verifierlist and client1.node.node_id in verifierlist
    assert client1.node.node_id in verifierlist
    client.node.start()
    # Next settlement period
    client1.economic.wait_settlement(node)
    log.info("The next  periods")
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    candidate_share_befor = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Shares']
    candidate_released_befor = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Released']
    assert verifierlist[0] == target_node_id and verifierlist[1] == client1.node.node_id

    #让委托收益池有钱,为了升级用
    result =  client.economic.account.sendTransaction(client2.node.web3, "", client2.economic.account.raw_accounts[0]['address'], client2.ppos.delegateRewardAddress, client2.node.eth.gasPrice, 21000, client2.economic.create_staking_limit * 200)

    # 升级
    upgrade_proposal(all_clients, client_consensus, 3584, client.pip.cfg.PLATON_NEW_BIN2)
    time.sleep(5)
    upgrade_proposal(all_clients, client_consensus, 3840, client.pip.cfg.PLATON_NEW_BIN1)
    time.sleep(5)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    verifierlist = get_pledge_list(client2.ppos.getVerifierList)
    print(f'升级后verifierlist={verifierlist}')

    client2.economic.wait_settlement(client2.node)
    verifierlist = get_pledge_list(client2.ppos.getVerifierList)
    assert verifierlist[0] == client1.node.node_id and verifierlist[1] == target_node_id
    candidate_share_after = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Shares']
    assert candidate_share_befor - candidate_share_after == sub_share
    candidate_released_after = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Released']
    assert candidate_released_after == candidate_released_befor

    candidate_info = client1.ppos.getCandidateInfo(target_node_id)['Ret']
    if candidate_info['ProgramVersion'] == 4096:
        assert target_node_id == verifierlist[1] and client1.node.node_id == verifierlist[0]
    else:
        assert client.node.node_id not in verifierlist



def test_1654_upgrade_zero_out_block_N(clients_new_node, client_consensus, all_clients):
    """
    0.13.2非内置节点（无替换节点，自由金额质押）零出块处罚多次，且恢复节点候选人列表，验证人列表，共识验证人列表权重未更新，升级0.16.0后，候选人列表，验证人列表，共识验证人列表权重更新
    """
    sub_share = 798328877005347593582890
    for i in range(len(clients_new_node)-1):
        if clients_new_node[i].node.node_id == '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf':
            client, client1 = clients_new_node[i], clients_new_node[i+1]
            break
    else:
        client, client1 = clients_new_node[3], clients_new_node[0]
    client2 = client_consensus
    target_node_id = client.node.node_id
    address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    address1, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.staking.create_staking(0, address, address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    result = client1.staking.create_staking(0, address1, address1, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    stakingnum = client.staking.get_stakingblocknum(client.node)
    print(f'stakingnum={stakingnum}')
    assert stakingnum == 25
    delegate_address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.delegate.delegate(0, delegate_address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)

    # Next settlement period
    client.economic.wait_settlement(client.node)
    verifierlist = get_pledge_list(client.ppos.getVerifierList)
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id
    log.info("Close one node")
    client.node.stop()
    node = client1.node

    log.info("The next  periods")
    client1.economic.wait_settlement(node)
    result = client2.delegate.withdrew_delegate(stakingnum, delegate_address, client.node.node_id, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    assert client.node.node_id not in verifierlist and client1.node.node_id in verifierlist
    assert client1.node.node_id in verifierlist
    client.node.start()
    # Next settlement period
    client1.economic.wait_settlement(node)
    log.info("The next  periods")
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    candidate_share_befor = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Shares']
    candidate_released_befor = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Released']
    assert verifierlist[0] == target_node_id and verifierlist[1] == client1.node.node_id

    #让委托收益池有钱,为了升级用
    result =  client.economic.account.sendTransaction(client2.node.web3, "", client2.economic.account.raw_accounts[0]['address'], client2.ppos.delegateRewardAddress, client2.node.eth.gasPrice, 21000, client2.economic.create_staking_limit * 200)

    # 升级
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    verifierlist = get_pledge_list(client2.ppos.getVerifierList)
    print(f'升级后verifierlist={verifierlist}')

    client2.economic.wait_settlement(client2.node)
    verifierlist = get_pledge_list(client2.ppos.getVerifierList)
    assert verifierlist[0] == client1.node.node_id and verifierlist[1] == target_node_id
    candidate_share_after = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Shares']
    assert candidate_share_befor - candidate_share_after == sub_share
    candidate_released_after = client1.ppos.getCandidateInfo(target_node_id)['Ret']['Released']
    assert candidate_released_after == candidate_released_befor

    candidate_info = client1.ppos.getCandidateInfo(target_node_id)['Ret']
    if candidate_info['ProgramVersion'] == 4096:
        assert target_node_id == verifierlist[1] and client1.node.node_id == verifierlist[0]
    else:
        assert client.node.node_id not in verifierlist




def test_1654_restricting_upgrade_zero_out_block_N(clients_new_node, client_consensus, all_clients):
    """
    0.13.2非内置节点（无替换节点，锁仓金额质押）零出块处罚多次，且恢复节点候选人列表，验证人列表，共识验证人列表权重未更新，升级0.16.0后，候选人列表，验证人列表，共识验证人列表权重更新
    """
    sub_share = 798328877005347593582890
    for i in range(len(clients_new_node)-1):
        if clients_new_node[i].node.node_id == '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf':
            client, client1 = clients_new_node[i], client_consensus
            break
    else:
        client, client1 = clients_new_node[3], client_consensus
    address, _ = client.economic.account.generate_account(client.node.web3, client.economic.delegate_limit)
    amount1 = client.economic.create_staking_limit * 10
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1},
            {'Epoch': 6, 'Amount': amount1},
            {'Epoch': 7, 'Amount': amount1},
            {'Epoch': 8, 'Amount': amount1},
            {'Epoch': 9, 'Amount': amount1},
            {'Epoch': 10, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(address, plan, client.economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.create_staking(1, address, address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    result = client1.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    stakingnum = client.staking.get_stakingblocknum(client.node)
    print(f'stakingnum={stakingnum}')
    assert stakingnum == 25
    delegate_address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.delegate.delegate(0, delegate_address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)

    # Next settlement period
    client.economic.wait_settlement(client.node)
    verifierlist = get_pledge_list(client.ppos.getVerifierList)
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id
    log.info("Close one node")
    client.node.stop()
    node = client1.node

    log.info("The next  periods")
    client1.economic.wait_settlement(node)
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    result = client1.delegate.withdrew_delegate(stakingnum, delegate_address, client.node.node_id, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    assert client.node.node_id not in verifierlist and client1.node.node_id in verifierlist
    client.node.start()
    # Next settlement period
    client1.economic.wait_settlement(node)
    log.info("The next  periods")
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    restricting_balance = client1.ppos.getRestrictingInfo(address)['Ret']['balance']
    candidateinfo_restrictingplan = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']['RestrictingPlan']
    candidateinfo_shares = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']['Shares']
    assert restricting_balance == candidateinfo_restrictingplan
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id

    #让委托收益池有钱
    result =  client.economic.account.sendTransaction(client1.node.web3, "", client1.economic.account.raw_accounts[0]['address'], client1.ppos.delegateRewardAddress, client1.node.eth.gasPrice, 21000, client1.economic.create_staking_limit * 200)

    #升级
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)

    for i in range(6):
        client.economic.wait_settlement(node)
        verifierlist = get_pledge_list(client1.ppos.getVerifierList)
        assert verifierlist[0] == client1.node.node_id and verifierlist[1] == client.node.node_id
        restricting_debt = client.ppos.getRestrictingInfo(address)['Ret']['debt']
        assert restricting_debt == amount1 * (3 + i)
        candidate_info = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']
        assert candidate_info['Shares'] == candidateinfo_shares - sub_share
        assert candidate_info['RestrictingPlan'] == candidateinfo_restrictingplan



def test_1654_restricting_continuous_upgrade_zero_out_block_N(clients_new_node, client_consensus, all_clients):
    """
    0.13.2非内置节点（无替换节点，锁仓金额质押）零出块处罚一次，小于质押金额且恢复节点未被剔除候选人列表，验证人列表，共识验证人列表，升级0.13.2-0.14.0-0.15.0-0.16.0，候选人列表，验证人列表，共识验证人列表权重更新
    """
    sub_share = 798328877005347593582890
    for i in range(len(clients_new_node)-1):
        if clients_new_node[i].node.node_id == '493c66bd7d6051e42a68bffa5f70005555886f28a0d9f10afaca4abc45723a26d6b833126fb65f11e3be51613405df664e7cda12baad538dd08b0a5774aa22cf':
            client, client1 = clients_new_node[i], client_consensus
            break
    else:
        client, client1 = clients_new_node[3], client_consensus
    address, _ = client.economic.account.generate_account(client.node.web3, client.economic.delegate_limit)
    amount1 = client.economic.create_staking_limit * 10
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1},
            {'Epoch': 6, 'Amount': amount1},
            {'Epoch': 7, 'Amount': amount1},
            {'Epoch': 8, 'Amount': amount1},
            {'Epoch': 9, 'Amount': amount1},
            {'Epoch': 10, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(address, plan, client.economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.create_staking(1, address, address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    result = client1.staking.increase_staking(0, 'atp1ur2hg0u9wt5qenmkcxlp7ysvaw6yupt4vll2fq', amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    stakingnum = client.staking.get_stakingblocknum(client.node)
    print(f'stakingnum={stakingnum}')
    assert stakingnum == 25
    delegate_address, _ = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit * 100)
    result = client.delegate.delegate(0, delegate_address, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)

    # Next settlement period
    client.economic.wait_settlement(client.node)
    verifierlist = get_pledge_list(client.ppos.getVerifierList)
    print(f'verifierlist={verifierlist}')
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id
    log.info("Close one node")
    client.node.stop()
    node = client1.node

    log.info("The next  periods")
    client1.economic.wait_settlement(node)
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    result = client1.delegate.withdrew_delegate(stakingnum, delegate_address, client.node.node_id, amount=client.economic.create_staking_limit * 80)
    assert_code(result, 0)
    assert client.node.node_id not in verifierlist and client1.node.node_id in verifierlist
    client.node.start()
    # Next settlement period
    client1.economic.wait_settlement(node)
    log.info("The next  periods")
    verifierlist = get_pledge_list(client1.ppos.getVerifierList)
    restricting_balance = client1.ppos.getRestrictingInfo(address)['Ret']['balance']
    candidateinfo_restrictingplan = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']['RestrictingPlan']
    candidateinfo_shares = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']['Shares']
    assert restricting_balance == candidateinfo_restrictingplan
    assert verifierlist[0] == client.node.node_id and verifierlist[1] == client1.node.node_id

    #让委托收益池有钱
    result =  client.economic.account.sendTransaction(client1.node.web3, "", client1.economic.account.raw_accounts[0]['address'], client1.ppos.delegateRewardAddress, client1.node.eth.gasPrice, 21000, client1.economic.create_staking_limit * 200)

    #升级
    upgrade_proposal(all_clients, client_consensus, 3584, client.pip.cfg.PLATON_NEW_BIN2)
    upgrade_proposal(all_clients, client_consensus, 3840, client.pip.cfg.PLATON_NEW_BIN1)
    upgrade_proposal(all_clients, client_consensus, 4096, client.pip.cfg.PLATON_NEW_BIN)


    for i in range(4):
        client.economic.wait_settlement(node)
        verifierlist = get_pledge_list(client1.ppos.getVerifierList)
        assert verifierlist[0] == client1.node.node_id and verifierlist[1] == client.node.node_id
        restricting_debt = client.ppos.getRestrictingInfo(address)['Ret']['debt']
        assert restricting_debt == amount1 * (5 + i)
        candidate_info = client1.ppos.getCandidateInfo(client.node.node_id)['Ret']
        assert candidate_info['Shares'] == candidateinfo_shares - sub_share
        assert candidate_info['RestrictingPlan'] == candidateinfo_restrictingplan



def test_eth17037(clients_consensus):
    # 启用--allow-insecure-unlock之后执行
    for client_node in clients_consensus:
        print(client_node.node.node_mark)
        if client_node.node.node_mark == '192.168.16.121:16789':
            client = client_node
    print(client.node.node_mark)

    account, pri = client.economic.account.generate_account(client.node.web3, client.economic.create_staking_limit)
    account1, _ = client.economic.account.generate_account(client.node.web3, 0)
    client.node.personal.importRawKey(pri, '88888888')

    account_balance = client.node.eth.getBalance(account)
    result = client.node.personal.unlockAccount(account, '88888888')
    assert result
    restlt = client.economic.account.sendTransaction(client.node.web3, "", account, account1, client.node.eth.gasPrice, 21000, 10000000000)
    account_balance_after = client.node.eth.getBalance(account)
    assert 0 < account_balance - account_balance_after - 10000000000 < client.node.web3.toWei(0.001, 'ether')
    balance1 = client.node.eth.getBalance(account1)
    assert balance1 == 10000000000



def test_debugpz(clients_new_node):
    for client in clients_new_node:
        if client.node.node_mark == '192.168.16.121:16790':
            break



    # 修改质押信息预估gas
    # reward_per = 0
    # node_name = "aaanode_name"
    # staking_address = 'atp1jt5puthuzyf48r5su9ejy9hnf85juvtvwelxsp'
    # pri_key = '0x7793f49c6af925e13e5d1c80d9f7756b29eaefe8de210370c6da6e3d277c2ac7'
    # rlp_reward_per = rlp.encode(reward_per) if reward_per else b''
    # data = HexBytes(rlp.encode(
    #     [rlp.encode(int(1001)), rlp.encode(bech32_address_bytes(staking_address)), rlp.encode(bytes.fromhex(client.node.node_id)),
    #      rlp_reward_per,
    #      rlp.encode(client.staking.cfg.external_id), rlp.encode(node_name), rlp.encode(client.staking.cfg.website),
    #      rlp.encode(client.staking.cfg.details)]))
    # estimated_edit_gas = client.node.eth.estimateGas({"from": staking_address, "to": client.node.ppos.stakingAddress, "data": data})
    # print(estimated_edit_gas)
    # address = 'atp1jt5puthuzyf48r5su9ejy9hnf85juvtvwelxsp'
    # node_name = "node_aname"
    # reward_per = 0
    # rlp_reward_per = rlp.encode(reward_per) if reward_per else b''
    # data = HexBytes(rlp.encode(
    #     [rlp.encode(int(1001)), rlp.encode(bech32_address_bytes(address)), rlp.encode(bytes.fromhex(client.node.node_id)),
    #      rlp_reward_per,
    #      rlp.encode("external_id"), rlp.encode(node_name), rlp.encode("website"),
    #      rlp.encode("details")]))
    # estimated_edit_gas = client.node.eth.estimateGas(
    #     {"from": address, "to": 'atp1zqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzfyslg3', "data": data})
    # print(estimated_edit_gas)

    # 委托预估gas
    delegate_address = 'atp1eq95atjq30yqk3j93ma0f5287mqgpdfgtsvd0s'
    # delegate_privatekey = '0x1da03be888f1721c1ab859cc56aab4e5272c39b0990746e6140b35b079e7f54c'
    #
    # data = rlp.encode([rlp.encode(int(1004)), rlp.encode(0), rlp.encode(bytes.fromhex(client.node.node_id)),
    #                    rlp.encode(client.economic.delegate_limit)])
    # transaction_data = {"to": client.node.ppos.stakingAddress, "data": data, "from": delegate_address}
    # estimated_gas = client.node.eth.estimateGas(transaction_data)
    # print(estimated_gas)

    # 领取委托预估gas
    # balance = client.node.web3.toWei(1000, 'ether')
    # delegate_address, delegate_prikey = client.economic.account.generate_account(client.node.web3, balance)
    # delegate_address = 'atp14pc23tfs0frkd6tpzye45ps2pvau7wz0uvns8f'
    # print(f'委托地址 ={delegate_address}')
    # result = client.delegate.delegate(0, delegate_address)
    # print(f'委托结果 ={result}')
    # client.economic.wait_settlement(client.node, 2)
    #
    # data = rlp.encode([rlp.encode(int(5000))])
    # print(client.node.ppos.delegateRewardAddress)
    # estimated_gas = client.node.eth.estimateGas({"to": delegate_address, "data": data, "from": client.node.ppos.delegateRewardAddress})
    # print(estimated_gas)  # 21080


def test_172_debug_economicConfig(client_new_node):
    economic_config = client_new_node.node.debug.economicConfig()
    assert economic_config['restricting']['minimumRelease'] == client_new_node.node.web3.toWei(80, 'ether')