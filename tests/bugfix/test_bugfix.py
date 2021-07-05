from common.log import log

def test_issue_1769(client_consensus):
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
