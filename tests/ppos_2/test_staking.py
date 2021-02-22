# -*- coding: utf-8 -*-
from dacite import from_dict

from tests.lib import Genesis
from tests.lib.utils import *
import pytest
from tests.lib.config import EconomicConfig
import allure

from tests.ppos.test_general_punishment import penalty_proportion_and_income
from tests.ppos.test_punishment_related import verification_duplicate_sign


@allure.title("Verify the validity of human parameters")
@pytest.mark.P1
def test_IV_001_002_010(global_test_env, client_consensus):
    """
    001:Verify the validity of human parameters
    002:The built-in account is found with the verifier list query
    010:The initial number of nodes is consistent with the number of verifier consensus nodes set
    """
    global_test_env.deploy_all()
    node_info = client_consensus.ppos.getValidatorList()
    log.info(node_info)
    nodeid_list = []
    for node in node_info.get("Ret"):
        nodeid_list.append(node.get("NodeId"))
        StakingAddress = node.get("StakingAddress")
        log.info(StakingAddress)
        assert client_consensus.node.web3.toChecksumAddress(StakingAddress) == \
               client_consensus.economic.account.raw_accounts[2]['address']
    log.info(nodeid_list)
    consensus_node_list = global_test_env.consensus_node_list
    nodeid_list_ = [node.node_id for node in consensus_node_list]
    log.info(nodeid_list_)
    assert len(nodeid_list_) == len(consensus_node_list)
    for nodeid in nodeid_list_:
        assert nodeid in nodeid_list


@allure.title("Verify the validity of human parameters")
@pytest.mark.P1
def test_IV_003(client_consensus):
    StakingAddress = client_consensus.economic.account.raw_accounts[2]['address']
    result = client_consensus.staking.create_staking(0, StakingAddress, StakingAddress)
    log.info("Staking result:{}".format(result))
    assert_code(result, 301101)


@allure.title("The initial verifier accepts the delegate")
@pytest.mark.P1
def test_IV_004(client_consensus):
    address, _ = client_consensus.economic.account.generate_account(client_consensus.node.web3,
                                                                    10 ** 18 * 10000000)
    result = client_consensus.delegate.delegate(0, address)
    log.info(result)
    assert_code(result, 301107)


@allure.title("The initial verifier holds an additional pledge")
@pytest.mark.P1
def test_IV_005(client_consensus):
    StakingAddress = client_consensus.economic.account.raw_accounts[2]['address']
    result = client_consensus.staking.increase_staking(0, StakingAddress)
    assert_code(result, 0)


@allure.title("Initial verifier exits")
@pytest.mark.P1
def test_IV_006_007_008(client_consensus):
    """
    006:Initial verifier exits
    007:The original verifier exits and re-pledges the pledge
    008:After the initial verifier quits, re-pledge and accept the entrustment
    """
    StakingAddress = client_consensus.economic.account.raw_accounts[2]['address']
    result = client_consensus.staking.withdrew_staking(StakingAddress)
    log.info(result)
    result = client_consensus.ppos.getCandidateInfo(client_consensus.node.node_id)
    log.info(result)
    log.info("Let's go to the next three cycles")
    client_consensus.economic.wait_settlement(client_consensus.node, 2)
    msg = client_consensus.ppos.getCandidateInfo(client_consensus.node.node_id)
    log.info(msg)
    assert msg["Code"] == 301204, "预期验证人已退出"
    result = client_consensus.staking.create_staking(0, StakingAddress, StakingAddress)
    assert_code(result, 0)
    address, _ = client_consensus.economic.account.generate_account(client_consensus.node.web3,
                                                                    10 ** 18 * 10000000)
    result = client_consensus.delegate.delegate(0, address)
    log.info(result)
    assert_code(result, 0)


@allure.title("Modify the initial verifier information")
@pytest.mark.P3
def test_IV_009(client_consensus):
    address1, _ = client_consensus.economic.account.generate_account(client_consensus.node.web3,
                                                                     10 ** 18 * 10000000)
    StakingAddress = client_consensus.economic.cfg.DEVELOPER_FOUNDATAION_ADDRESS
    result = client_consensus.staking.edit_candidate(StakingAddress, address1)
    log.info(result)
    assert_code(result, 0)


@allure.title("Normal pledge、Repeat pledge")
@pytest.mark.P1
@pytest.mark.compatibility
def test_IV_014_015_019_024(client_new_node):
    """
    014：Normal pledge
    015：Repeat pledg
    019：The amount pledged by free account reaches the threshold of pledge
    024：Use the correct version signature
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    log.info("Generate address:{}".format(address))
    result = client_new_node.staking.create_staking(0, address, address)
    log.info(result)
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(0, address, address)
    log.info(result)
    assert_code(result, 301101)


@allure.title("Node ID pledge not added to the chain")
@pytest.mark.P3
def test_IV_016(client_new_node):
    """
    :param client_new_node_obj:
    :return:
    """
    illegal_nodeID = "7ee3276fd6b9c7864eb896310b5393324b6db785a2528c00cc28ca8c" \
                     "3f86fc229a86f138b1f1c8e3a942204c03faeb40e3b22ab11b8983c35dc025de42865990"
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, address, address, node_id=illegal_nodeID)
    log.info(result)
    assert_code(result, 301003)


@allure.title("The beneficiary address is the excitation pool address")
@pytest.mark.P3
def test_IV_017(client_new_node):
    """
    :param client_new_node_obj:
    :return:
    """
    INCENTPEPOOL_ADDRESS = EconomicConfig.INCENTIVEPOOL_ADDRESS
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, INCENTPEPOOL_ADDRESS, address)
    assert_code(result, 0)


@allure.title("Beneficiary address is the foundation address")
@pytest.mark.P3
def test_IV_018(client_new_node):
    """
    :param client_new_node_obj:
    :param get_generate_account:
    :return:
    """
    FOUNDATION_ADDRESS = client_new_node.economic.cfg.FOUNDATION_ADDRESS
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, FOUNDATION_ADDRESS, address)
    assert_code(result, 0)


@allure.title("The amount pledged by free account is less than the threshold of pledge, and gas is insufficient")
@pytest.mark.P2
def test_IV_020_21(client_new_node):
    """
    020:The amount pledged by free account is less than the threshold of pledge
    021:gas is insufficient
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    amount = client_new_node.economic.create_staking_limit
    result = client_new_node.staking.create_staking(0, address, address, amount=amount - 1)
    log.info(result)
    assert_code(result, 301100)
    cfg = {"gas": 1}
    status = 0
    try:
        result = client_new_node.staking.create_staking(0, address, address, transaction_cfg=cfg)
        log.info(result)
    except BaseException:
        status = 1
    assert status == 1


@allure.title("Incorrect version signature used")
@pytest.mark.P3
def test_IV_025(client_new_node, client_consensus):
    """
    :param client_new_node_obj:
    :param client_consensus_obj:
    :return:
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    program_version_sign = client_consensus.node.program_version_sign
    result = client_new_node.staking.create_staking(0, address, address, program_version_sign=program_version_sign)
    log.info(result)
    assert_code(result, 301003)


@allure.title("BlsPublicKey is too long")
@pytest.mark.P2
def test_IV_026_01(client_new_node):
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    blspubkey = client_new_node.node.blspubkey + "00000000"
    log.info(blspubkey)
    status = 0
    try:
        result = client_new_node.staking.create_staking(0, address, address, bls_pubkey=blspubkey)
        log.info(result)
    except BaseException:
        status = 1
    assert status == 1


@allure.title("BlsPublicKey is too short")
@pytest.mark.P2
def test_IV_026_02(client_new_node):
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    blspubkey = client_new_node.node.blspubkey[0:10]
    log.info(blspubkey)
    status = 0
    try:
        result = client_new_node.staking.create_staking(0, address, address, bls_pubkey=blspubkey)
        log.info(result)
    except BaseException:
        status = 1
    assert status == 1


@allure.title("Incorrect version signature used")
@pytest.mark.P2
def test_IV_026_03(client_new_node):
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    program_version = 0000
    result = client_new_node.staking.create_staking(0, address, address, program_version=program_version)
    assert_code(result, 301003)


@allure.title("Field length overflow")
@pytest.mark.P2
def test_IV_027(client_new_node):
    external_id = "11111111111111111111111111111111111111111111111111111111111111111111111111111111111"
    node_name = "1111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
    website = "1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111 "
    details = "1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111 "
    program_version = client_new_node.node.program_version
    program_version_sign = client_new_node.node.program_version_sign
    bls_pubkey = client_new_node.node.blspubkey
    bls_proof = client_new_node.node.schnorr_NIZK_prove
    amount = client_new_node.economic.create_staking_limit
    address, pri_key = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                         10 ** 18 * 10000000)

    result = client_new_node.ppos.createStaking(0, address, client_new_node.node.node_id,
                                                external_id, node_name, website, details, amount,
                                                program_version, program_version_sign, bls_pubkey, bls_proof,
                                                pri_key, reward_per=0)
    assert_code(result, 301002)


@allure.title("Pledge has been made before and the candidate has been invalidated (penalized)")
@pytest.mark.P2
def test_IV_028(clients_new_node, client_consensus):
    client = clients_new_node[0]
    node = client.node
    other_node = client_consensus.node
    economic = client.economic
    address, pri_key = economic.account.generate_account(node.web3, client.economic.create_staking_limit * 2)

    # value = economic.create_staking_limit * 2
    result = client.staking.create_staking(0, address, address)
    assert_code(result, 0)
    economic.wait_consensus(other_node, 4)
    validator_list = get_pledge_list(other_node.ppos.getValidatorList)
    assert node.node_id in validator_list
    log.info("Close one node")
    node.stop()
    for i in range(4):
        economic.wait_consensus(other_node, i)
        candidate_info = other_node.ppos.getCandidateInfo(node.node_id)
        log.info(candidate_info)
        if candidate_info["Ret"]["Released"] < client.economic.create_staking_limit:
            break
    log.info("Restart the node")
    node.start()
    result = client.staking.edit_candidate(address, address)
    log.info(result)
    assert_code(result, 301103)
    log.info("Next settlement period")
    economic.wait_settlement(node, 2)
    result = client.staking.create_staking(0, address, address)
    assert_code(result, 0)


@allure.title("Pledge has been made before, and the candidate is invalid (voluntarily withdraw)")
@pytest.mark.P1
def test_IV_029(client_new_node):
    """
    :param client_new_node_obj:
    :param get_generate_account:
    :return:
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 2000000)
    result = client_new_node.staking.create_staking(0, address, address)
    assert_code(result, 0)
    result = client_new_node.staking.withdrew_staking(address)
    log.info(result)
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(0, address, address)
    assert_code(result, 0)


@allure.title("Lockup pledge")
@pytest.mark.P1
def test_IV_030(client_new_node):
    """
    :param client_new_node_obj:
    :param get_generate_account:
    :return:
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, address, address)
    assert_code(result, 0)
    log.info("Into the next grandchild")
    client_new_node.economic.wait_settlement(client_new_node.node)
    result = client_new_node.staking.withdrew_staking(address)
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(0, address, address)
    log.info(result)
    assert_code(result, 301101)


@allure.title("Use a new wallet as pledge")
@pytest.mark.P2
def test_IV_031(client_new_node):
    """
    :param client_new_node_obj:
    :param get_generate_account:
    :return:
    """
    address, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                   10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, address, address)
    assert_code(result, 0)

    address1, _ = client_new_node.economic.account.generate_account(client_new_node.node.web3,
                                                                    10 ** 18 * 10000000)
    result = client_new_node.staking.create_staking(0, address1, address1)
    log.info(result)
    assert_code(result, 301101)


@pytest.mark.P1
def test_IV_032(client_new_node):
    """
    混合金额质押，仅使用锁仓
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.delegate_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    amount1 = node.web3.toWei(833, 'ether')
    amount2 = node.web3.toWei(837, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1},
            {'Epoch': 6, 'Amount': amount1},
            {'Epoch': 7, 'Amount': amount1},
            {'Epoch': 8, 'Amount': amount1},
            {'Epoch': 9, 'Amount': amount1},
            {'Epoch': 10, 'Amount': amount1},
            {'Epoch': 11, 'Amount': amount1},
            {'Epoch': 12, 'Amount': amount2}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['Released'] == 0
    assert candidate_info['RestrictingPlan'] == economic.create_staking_limit


@pytest.mark.P1
def test_IV_032_01(client_new_node):
    """
    混合金额质押，仅使用锁仓
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.delegate_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    amount1 = node.web3.toWei(833, 'ether')
    amount2 = node.web3.toWei(837, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1},
            {'Epoch': 6, 'Amount': amount1},
            {'Epoch': 7, 'Amount': amount1},
            {'Epoch': 8, 'Amount': amount1},
            {'Epoch': 9, 'Amount': amount1},
            {'Epoch': 10, 'Amount': amount1},
            {'Epoch': 11, 'Amount': amount1},
            {'Epoch': 12, 'Amount': amount2}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_balance = node.eth.getBalance(node.ppos.restrictingAddress)
    staking_balance = node.eth.getBalance(node.ppos.stakingAddress)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    restricting_balance1 = node.eth.getBalance(node.ppos.restrictingAddress)
    staking_balance1 = node.eth.getBalance(node.ppos.stakingAddress)
    assert restricting_balance - economic.create_staking_limit == restricting_balance1
    assert staking_balance + economic.create_staking_limit == staking_balance1

    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == 0
    assert candidate_info['RestrictingPlanHes'] == economic.create_staking_limit
    result = client.staking.withdrew_staking(staking_address)
    assert_code(result, 0)
    restricting_balance2 = node.eth.getBalance(node.ppos.restrictingAddress)
    staking_balance2 = node.eth.getBalance(node.ppos.stakingAddress)
    assert restricting_balance1 + economic.create_staking_limit == restricting_balance2
    assert staking_balance1 - economic.create_staking_limit == staking_balance2
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Code']
    assert candidate_info == 301204


@pytest.mark.P1
def test_IV_033(client_new_node):
    """
    混合金额质押，仅使用自由金额
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用自有金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 2)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['Released'] == economic.create_staking_limit
    assert candidate_info['RestrictingPlan'] == 0


@pytest.mark.P1
def test_IV_033_01(client_new_node):
    """
    混合金额质押，仅使用自由金额
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用自有金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 2)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    staking_balance = node.eth.getBalance(node.ppos.stakingAddress)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    staking_balance1 = node.eth.getBalance(node.ppos.stakingAddress)
    assert staking_balance + economic.create_staking_limit == staking_balance1

    candiate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candiate_info['ReleasedHes'] == economic.create_staking_limit
    assert candiate_info['RestrictingPlanHes'] == 0

    result = client.staking.withdrew_staking(staking_address)
    assert_code(result, 0)
    staking_balance2 = node.eth.getBalance(node.ppos.stakingAddress)
    assert staking_balance1 - economic.create_staking_limit == staking_balance2

    candiate_info = node.ppos.getCandidateInfo(node.node_id)
    assert candiate_info['Code'] == 301204


@pytest.mark.P2
@pytest.mark.parametrize('amount', [10000, 9999])
def test_IV_034(client_new_node, amount):
    """
    混合金额质押，质押金额足够、手续费不足
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用自有金额质押
    staking_address, _ = economic.account.generate_account(node.web3, node.web3.toWei(amount, 'ether'))
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 301111)


@pytest.mark.P2
def test_IV_035(client_new_node):
    """
    混合金额质押，质押金额低于最低门槛
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用自有金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 2)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address,
                                                    amount=node.web3.toWei(9000, 'ether'))
    assert_code(result, 301100)


@pytest.mark.P2
@pytest.mark.parametrize('amount', [10000, 9999])
def test_IV_036(client_new_node, amount):
    """
    混合金额质押，锁仓质押金额不足
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, 0)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    # amount1 = node.web3.toWei(833, 'ether')
    # amount2 = node.web3.toWei(837, 'ether')
    plan = [{'Epoch': 1, 'Amount': node.web3.toWei(amount, 'ether')}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    status = True
    try:
        result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
        assert_code(result, 301111)
        status = False
    except Exception as e:
        log.info("Use case success, exception information：{} ".format(str(e)))
        assert status, "ErrMsg:Transfer result {}".format(status)


@pytest.mark.P2
def test_IV_037(client_new_node):
    """
    混合金额质押，质押金额低于最低门槛
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.delegate_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    # amount1 = node.web3.toWei(833, 'ether')
    # amount2 = node.web3.toWei(837, 'ether')
    plan = [{'Epoch': 1, 'Amount': node.web3.toWei(9999, 'ether')}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 304015)


@pytest.mark.P1
def test_IV_038(client_new_node):
    """
    混合金额质押，锁仓金额足够质押金
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit * 2)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    amount1 = node.web3.toWei(833, 'ether')
    amount2 = node.web3.toWei(837, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1},
            {'Epoch': 6, 'Amount': amount1},
            {'Epoch': 7, 'Amount': amount1},
            {'Epoch': 8, 'Amount': amount1},
            {'Epoch': 9, 'Amount': amount1},
            {'Epoch': 10, 'Amount': amount1},
            {'Epoch': 11, 'Amount': amount1},
            {'Epoch': 12, 'Amount': amount2}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['RestrictingPlan'] == economic.create_staking_limit
    assert candidate_info['Released'] == 0
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == economic.create_staking_limit
    assert restricting_info['Pledge'] == economic.create_staking_limit
    assert restricting_info['debt'] == amount1


@pytest.mark.P1
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_039(client_new_node, gas_type):
    """
    混合金额质押，锁仓金额不足质押金
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['RestrictingPlan'] == node.web3.toWei(5000, 'ether')
    assert candidate_info['Released'] == node.web3.toWei(5000, 'ether')
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    assert restricting_info['Pledge'] == node.web3.toWei(5000, 'ether')
    assert restricting_info['debt'] == amount1
    balance1 = node.eth.getBalance(staking_address)
    assert balance - node.web3.toWei(5000, 'ether') - balance1 < node.web3.toWei(0.01, 'ether')


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_040(client_new_node, gas_type):
    """
    混合金额质押，锁仓+自由质押金额足够、手续费不足
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, node.web3.toWei(5000, 'ether'))
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address", balance)
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 304015)


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_041(client_new_node, gas_type):
    """
    混合金额质押，锁仓+自由质押金额不足
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, node.web3.toWei(4000, 'ether'))
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address", balance)
    amount1 = node.web3.toWei(500, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(2500, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 304015)


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_042(client_new_node, gas_type):
    """
    混合金额质押，质押金额低于最低门槛
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address", balance)
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address,
                                                    amount=node.web3.toWei(9000, 'ether'))
    assert_code(result, 301100)


@pytest.mark.P1
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_043(client_new_node, gas_type):
    """
    混合质押-锁仓释放
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance_tmp = node.web3.toWei(5000, 'ether')
    debt_amount_tmp = 0
    economic.wait_settlement(node)
    for i in range(4):
        print('number', i)
        balance_tmp = balance_tmp
        debt_amount_tmp = debt_amount_tmp + node.web3.toWei(1000, 'ether')
        restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
        print(restricting_info)
        assert restricting_info['balance'] == balance_tmp
        assert restricting_info['debt'] == debt_amount_tmp
        economic.wait_settlement(node)

    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    assert restricting_info['debt'] == node.web3.toWei(5000, 'ether')
    assert restricting_info['plans'] is None
    assert restricting_info['Pledge'] == node.web3.toWei(5000, 'ether')


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_044(client_new_node, gas_type):
    """
    混合质押-锁仓、自由增持
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 10)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 10)
    assert_code(result, 0)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['Released'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    assert candidate_info['RestrictingPlan'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 10)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 10)
    assert_code(result, 0)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['Released'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    assert candidate_info['RestrictingPlan'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 10
    assert candidate_info['ReleasedHes'] == economic.delegate_limit * 10
    assert candidate_info['RestrictingPlanHes'] == economic.delegate_limit * 10


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_045(client_new_node, gas_type):
    """
    混合质押-退回质押金
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print(result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['Released'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlan'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000

    result = client.staking.withdrew_staking(staking_address)
    assert_code(result, 0)
    balance1 = node.eth.getBalance(staking_address)
    log.info("退回质押后账号余额 {}".format(balance1))
    # restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    economic.wait_settlement(node, 3)
    balance2 = node.eth.getBalance(staking_address)
    log.info("退回质押后账号余额 {}".format(balance1))
    restricting_info1 = node.ppos.getRestrictingInfo(staking_address)
    assert restricting_info1['Code'] == 304005
    assert balance1 + node.web3.toWei(14000, 'ether') == balance2
    # assert restricting_info1['balance'] == node.web3.toWei(2000, 'ether')
    # assert restricting_info1['debt'] == 0
    # assert restricting_info['Pledge'] == 0


@pytest.mark.P2
@pytest.mark.parametrize('gas_type', [0, 1])
def test_IV_046(client_new_node, gas_type):
    """
    混合质押-犹豫期退回质押金
    """
    client = client_new_node
    economic = client.economic
    node = client.node
    if gas_type == 0:
        node.ppos.need_quota_gas = False
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print(result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    result = client.staking.withdrew_staking(staking_address)
    assert_code(result, 0)

    balance1 = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    print(result)
    assert balance + node.web3.toWei(5000, 'ether') - balance1 < 0.1
    assert restricting_info['balance'] == economic.create_staking_limit
    assert restricting_info['debt'] == 0
    assert restricting_info['Pledge'] == 0


@pytest.mark.P2
def test_IV_047(client_new_node, client_consensus):
    """
    混合质押-锁仓金额不足质押金、自由金额补上-零出块处罚
    """
    client = client_new_node
    client1 = client_consensus
    economic = client.economic
    node = client.node

    slash_block = economic.genesis.economicModel.slashing.slashBlocksReward
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print(result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000

    economic.wait_settlement(node)
    block_reward, staking_reward = client.economic.get_current_year_reward(client.node)
    node_id = node.node_id
    client.node.stop()
    client1.economic.wait_consensus(client1.node, 3)
    punishment_amonut = int(Decimal(str(block_reward)) * Decimal(str(slash_block)))
    print(punishment_amonut)
    candidate_info1 = client1.node.ppos.getCandidateInfo(node_id)['Ret']
    print(candidate_info1)
    assert candidate_info1['Released'] == candidate_info['ReleasedHes'] - punishment_amonut
    assert candidate_info1['RestrictingPlan'] == candidate_info['RestrictingPlanHes']


@pytest.mark.P2
def test_IV_048(client_new_node, client_consensus):
    """
    混合质押-锁仓金额足够质押金-零出块处罚
    """
    client = client_new_node
    client1 = client_consensus
    economic = client.economic
    node = client.node
    slash_block = economic.genesis.economicModel.slashing.slashBlocksReward
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(2000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == economic.create_staking_limit
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print(result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == 0
    assert candidate_info['RestrictingPlanHes'] == economic.create_staking_limit + economic.delegate_limit * 1000

    economic.wait_settlement(node)
    block_reward, staking_reward = client.economic.get_current_year_reward(client.node)
    node_id = node.node_id
    client.node.stop()
    client1.economic.wait_consensus(client1.node, 3)
    punishment_amonut = int(Decimal(str(block_reward)) * Decimal(str(slash_block)))
    print(punishment_amonut)
    candidate_info1 = client1.node.ppos.getCandidateInfo(node_id)['Ret']
    print(candidate_info1)
    assert candidate_info1['Released'] == 0
    assert candidate_info1['RestrictingPlan'] == candidate_info['RestrictingPlanHes'] - punishment_amonut


@pytest.mark.P2
def test_IV_049(new_genesis_env, clients_noconsensus):
    """
    混合质押-锁仓金额足够质押金-双签处罚
    """
    client = clients_noconsensus[0]
    client1 = clients_noconsensus[1]
    economic = client.economic
    node = client.node

    genesis = from_dict(data_class=Genesis, data=new_genesis_env.genesis_config)
    genesis.economicModel.slashing.slashFractionDuplicateSign = 6000
    new_file = new_genesis_env.cfg.env_tmp + "/genesis_0.15.0.json"
    genesis.to_file(new_file)
    new_genesis_env.deploy_all(new_file)

    # pledge_amount1, penalty_ratio, proportion_ratio = penalty_proportion_and_income(client)
    penalty_ratio = int(get_governable_parameter_value(client, 'slashFractionDuplicateSign'))
    proportion_ratio = int(get_governable_parameter_value(client, 'duplicateSignReportReward'))
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    report_address, _ = economic.account.generate_account(node.web3, node.web3.toWei(1, 'ether'))
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print(result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000

    economic.wait_settlement(node)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    print(candidate_info)
    assert candidate_info['Released'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlan'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    proportion_reward, incentive_pool_reward = economic.get_report_reward(candidate_info['Shares'], penalty_ratio,
                                                                          proportion_ratio)
    print(proportion_reward, incentive_pool_reward)
    for i in range(4):
        result = check_node_in_list(node.node_id, client.ppos.getValidatorList)
        log.info("Current node in consensus list status：{}".format(result))
        if result:
            # Get current block height
            current_block = node.eth.blockNumber
            log.info("Current block height: {}".format(current_block))
            report_address_balance = client1.node.eth.getBalance(report_address)
            print('report_address_balance', report_address_balance)
            incentive_pool_balance = client1.node.eth.getBalance(EconomicConfig.INCENTIVEPOOL_ADDRESS)
            print('incentive_pool_balance', incentive_pool_balance)
            staking_address_balance = client1.node.eth.getBalance(staking_address)
            print('staking_address_balance', staking_address_balance)
            # Report verifier Duplicate Sign
            result = verification_duplicate_sign(client, 1, 1, report_address, current_block)
            assert_code(result, 0)
            break
        else:
            # wait consensus block
            economic.wait_consensus(node)

    candidate_info1 = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info1['Released'] == 0
    assert candidate_info1['RestrictingPlan'] == candidate_info['RestrictingPlan'] - node.web3.toWei(1200, 'ether')

    client1.economic.wait_settlement(client1.node, 3)
    report_address_balance1 = client1.node.eth.getBalance(report_address)
    print('report_address_balance', report_address_balance1)
    incentive_pool_balance1 = client1.node.eth.getBalance(EconomicConfig.INCENTIVEPOOL_ADDRESS)
    print('incentive_pool_balance', incentive_pool_balance1)
    staking_address_balance1 = client1.node.eth.getBalance(staking_address)
    print('staking_address', staking_address_balance1)
    assert report_address_balance + proportion_reward - report_address_balance1 < client1.node.web3.toWei(0.01, 'ether')
    assert incentive_pool_balance + incentive_pool_reward == incentive_pool_balance1
    assert staking_address_balance + candidate_info['RestrictingPlan'] - node.web3.toWei(1200,
                                                                                         'ether') == staking_address_balance1


@pytest.mark.P2
def test_IV_050(client_new_node, client_consensus):
    """
    混合质押-锁仓金额足够质押金-单节点委托
    """
    client = client_new_node
    client1 = client_consensus
    economic = client.economic
    node = client.node
    # 使用锁仓金额质押
    staking_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    benifit_address, _ = economic.account.generate_account(node.web3, 0)
    delegate_address, _ = economic.account.generate_account(node.web3, economic.create_staking_limit)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    amount1 = node.web3.toWei(1000, 'ether')
    plan = [{'Epoch': 1, 'Amount': amount1},
            {'Epoch': 2, 'Amount': amount1},
            {'Epoch': 3, 'Amount': amount1},
            {'Epoch': 4, 'Amount': amount1},
            {'Epoch': 5, 'Amount': amount1}]
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    restricting_info = node.ppos.getRestrictingInfo(staking_address)['Ret']
    assert restricting_info['balance'] == node.web3.toWei(5000, 'ether')
    result = client_new_node.staking.create_staking(2, benifit_address, staking_address)
    assert_code(result, 0)
    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = client.restricting.createRestrictingPlan(staking_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.restricting.createRestrictingPlan(delegate_address, plan,
                                                      economic.account.account_with_money['address'])
    assert_code(result, 0)
    result = client.staking.increase_staking(0, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.staking.increase_staking(1, staking_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.delegate.delegate(0, delegate_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)
    result = client.delegate.delegate(1, delegate_address, amount=economic.delegate_limit * 1000)
    assert_code(result, 0)

    balance = node.eth.getBalance(delegate_address)
    log.info("delegate_address {}".format(balance))

    balance = node.eth.getBalance(staking_address)
    log.info("staking_address {}".format(balance))
    result = node.ppos.getRestrictingInfo(staking_address)
    print('staking_address', result)
    result = node.ppos.getRestrictingInfo(delegate_address)
    print('delegate_address', result)
    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    assert candidate_info['ReleasedHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['RestrictingPlanHes'] == node.web3.toWei(5000, 'ether') + economic.delegate_limit * 1000
    assert candidate_info['DelegateTotalHes'] == economic.delegate_limit * 2000
    economic.wait_settlement(node)
    delegate_address_balance = node.eth.getBalance(delegate_address)
    print('delegate_address_balance', delegate_address_balance)

    candidate_info = node.ppos.getCandidateInfo(node.node_id)['Ret']
    block_number = candidate_info['StakingBlockNum']
    result = client.delegate.withdrew_delegate(block_number, delegate_address, node.node_id,
                                               amount=economic.delegate_limit * 1500)
    assert_code(result, 0)

    delegate_address_balance1 = node.eth.getBalance(delegate_address)
    print('delegate_address_balance', delegate_address_balance1)
    restricting_info = node.ppos.getRestrictingInfo(delegate_address)['Ret']
    print(restricting_info)
    assert restricting_info['balance'] == node.web3.toWei(4000, 'ether')
    assert restricting_info['Pledge'] == node.web3.toWei(500, 'ether')
    assert delegate_address_balance + economic.delegate_limit * 1000 == delegate_address_balance1
