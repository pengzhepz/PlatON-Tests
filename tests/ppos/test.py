from alaya import HTTPProvider, Web3, WebsocketProvider
# from client_sdk_python import HTTPProvider, Web3, WebsocketProvider, Account
from client_sdk_python.eth import Eth
from client_sdk_python.middleware import geth_poa_middleware
# from client_sdk_python.packages.platon_keys
# from client_sdk_python.packages.platon_keys.utils.address import MIANNETHRP
from client_sdk_python.packages.platon_keys.utils.address import address_bytes_to_bech32_address
from client_sdk_python.pip import Pip
from client_sdk_python.ppos import Ppos
from hexbytes import HexBytes

# from conf.settings import TMP_ADDRES, ACCOUNT_FILE, BASE_DIR

accounts = {}


def connect_web3(url, chain_id=201018):
    if "ws" in url:
        w3 = Web3(WebsocketProvider(url), chain_id=chain_id)
    else:
        w3 = Web3(HTTPProvider(url), chain_id=chain_id)
    w3.middleware_stack.inject(geth_poa_middleware, layer=0)
    return w3


def createRestrictingPlan(url, account, plan, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.createRestrictingPlan(account, plan, pri_key)
    print(result)

#
# def createstaking(url, typ, pri_key, amount, reward_per=1000):
#     web3 = connect_web3(url)
#     admin = Admin(web3)
#     ppos = Ppos(web3)
#     print("==== create staking =====")
#     # w3 = Web3(HTTPProvider(node_url), chain_id=chain_id)
#     program_version = admin.getProgramVersion()['Version']
#     version_sign = admin.getProgramVersion()['Sign']
#     bls_proof = admin.getSchnorrNIZKProve()
#     bls_pubkey = admin.nodeInfo['blsPubKey']
#     node_id = admin.nodeInfo['id']
#     benifit_address = Account.privateKeyToAccount(pri_key, MIANNETHRP).address
#     result = ppos.createStaking(typ, benifit_address, node_id, 'external_id', 'node_name', 'website', 'details',
#                                 amount, program_version, version_sign, bls_pubkey, bls_proof, pri_key, reward_per)
#     print(f"create staking result = {result}")


def increase_staking(url, type, node_id, amount, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.increaseStaking(type, node_id, amount, pri_key)
    print(result)


def withdrewStaking(url, node_id, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.withdrewStaking(node_id, pri_key)
    print(result)


def delegate(url, typ, node_id, amount, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.delegate(typ, node_id, amount, pri_key)
    print(result)


def withdraw_delegate(url, staking_blocknum, node_id, amount, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    # ppos.need_analyze == False
    result = ppos.withdrewDelegate(staking_blocknum, node_id, amount, pri_key)
    print("赎回委托状态", result)


def withdraw_delegate_reward(url, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.withdrawDelegateReward(pri_key)
    print(result)


def editCandidate(url, benifit_address, node_id, reward_per, pri_key):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    external_id = ''
    node_name = ''
    website = ''
    details = ''
    result = ppos.editCandidate(benifit_address, node_id, external_id, node_name, website, details, pri_key, reward_per,
                                transaction_cfg=None)
    print(result)


def sendTransaction(url, from_address, prikey, to_address, value, chain_id):
    web3 = connect_web3(url)
    platon = Eth(web3)
    nonce = platon.getTransactionCount(from_address)
    gasPrice = platon.gasPrice
    # gasPrice = 100000000
    transaction_dict = {
        "to": to_address,
        "gasPrice": gasPrice,
        "gas": 21000,
        "nonce": nonce,
        "data": '',
        "chainId": chain_id,
        "value": value,
    }

    signedTransactionDict = platon.account.signTransaction(
        transaction_dict, prikey
    )

    data = signedTransactionDict.rawTransaction
    result = HexBytes(platon.sendRawTransaction(data)).hex()
    # print(result)
    # log.debug("result:::::::{}".format(result))
    res = platon.waitForTransactionReceipt(result)
    print(res)


def get_candidatelist(url):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getCandidateList()
    # print(result)
    return result


def get_VerifierList(url):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getVerifierList()
    print(result)
    return result


def getValidatorList(url):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getValidatorList()
    print(result)


def get_candinfo(url, node_id):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getCandidateInfo(node_id)
    print(result)


def get_RestrictingPlan(url, address):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getRestrictingInfo(address)
    # print(result)
    return result


def getDelegateReward(url, address):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getDelegateReward(address)
    print(result)


def getDelegateInfo(url, staking_blocknum, del_address, node_id):
    web3 = connect_web3(url)
    ppos = Ppos(web3)
    result = ppos.getDelegateInfo(staking_blocknum, del_address, node_id)
    print(result)


def create_account(HRP='atp'):
    address_bytes_to_bech32_address()


# def get_listGovernParam(url, module=None, from_address=None):
#     web3 = connect_web3(url)
#     ppos = Ppos(web3)
#     # ppos.web3.platon
#     if module is None:
#         module = ""
#     data = rlp.encode([rlp.encode(int(2106)), rlp.encode(module)])
#     raw_data = ppos.call_obj(ppos, from_address, Web3.pipAddress, data)
#     data = str(raw_data, encoding="utf-8")
#     if data == "":
#         return ""
#     print(json.loads(data))

#
# def create_address(url):
#     """
#     创建新钱包地址
#     """
#     web3 = connect_web3(url)
#     platon = Eth(web3)
#     account = platon.account.create(net_type=web3.net_type)
#     address = account.address
#     prikey = account.privateKey.hex()[2:]
#     account = {
#         "address": address,
#         "nonce": 0,
#         "balance": 0,
#         "prikey": prikey,
#     }
#     accounts = {}
#     raw_accounts = LoadFile(ACCOUNT_FILE).get_data()
#     print(raw_accounts)
#     for account1 in raw_accounts:
#         accounts[account1['address']] = account1
#     print(accounts)
#     accounts[address] = account
#     # todo delete debug
#     accounts = list(accounts.values())
#     with open(os.path.join(BASE_DIR, "deploy/tmp/accounts.uat.yml"), mode="w", encoding="UTF-8") as f:
#         yaml.dump(accounts, f, Dumper=yaml.RoundTripDumper)
#
#
# def cycle_sendTransaction(url):
#     """
#
#     """
#
# with open(TMP_ADDRES, 'a', encoding='utf-8') as f:
#     f.write("2")

def submitVersion(url, nodeid, pip_id, new_version, rounds, pri_key):
    web3 = connect_web3(url)
    pip = Pip(web3)
    resutl = pip.submitVersion(nodeid, pip_id, new_version, rounds, pri_key)
    print(resutl)

def fff(url):
    web3 = connect_web3(url)
    platon = Eth(web3)
    # print(platon.g)
    a = Web3.fromWei(6657754010695187165780, 'ether')
    print(a)
    # result = platon.getTransactionCount(from_address)
    # result = platon.getBalance(from_address)
    # print(platon.blockNumber)
    # print(result)


if __name__ == '__main__':
    url = 'http://192.168.10.224:6790'
    # url = 'http://192.168.9.221:6789'
    # url = 'http://192.168.120.141:6789'
    # url = 'http://10.1.1.51:6789'
    # url = 'http://192.168.120.121:6789'
    # url = 'http:// 47.241.4.217:6789'
    # url = 'http://154.85.35.163:80'
    # url = 'http://154.85.34.8:6789'
    # url = 'http://192.168.21.186:6771'
    # url = 'https://openapi.alaya.network/rpc'
    account = '0x1000000000000000000000000000000000000002'
    pri_key = 'a872ee498a5a92b87b1780b1d3d71dd0cfce2980f59960b76318f5d409908303'
    account1 = 'atx1zkrxx6rf358jcvr7nruhyvr9hxpwv9unj58er9'
    pri_key1 = 'f51ca759562e1daf9e5302d121f933a8152915d34fcbc27e542baf256b5e4b74'
    # from_address = 'atx1zkrxx6rf358jcvr7nruhyvr9hxpwv9unj58er9'
    # epoch1 = 10
    # epoch2 = 20
    # create_account(url)
    amount1 = Web3.toWei(833, 'ether')
    amount2 = Web3.toWei(837, 'ether')
    # list = ['atx1r8pvmt7hk6lk8uk7dtnfyrpcy9l8rfjry34uq9',
    #         'atx1nccsq48wery09qlma3rapree588cafwlpll8cr',
    #         'atx14w3m34dmx5xjr7wc5yhg6xtp59j3qy4m77t4vl',
    #         'atx10u83ynv0sdjrjg4na66pg3fqyx8uc89g7zvnyu',
    #         'atx13e2hlak7jytcdlv47vmqa2hkaeyv62ggv3hymk',
    #         'atx1z4e77tam2lv8vsrzkazz659avlvx3v8jyh0ywt',
    #         'atx1pvd37yxnmdtdujaf3dwc4xpcukdzsf5q2hyc9a',
    #         'atx17rf2ylcauvse5sxsvnn05c30zscey0zwzhs5wp',
    #         'atx1cux96yve5d335hqt3a7pdjygpj77pny3xqq7qu',
    #         'atx1s9qht6yzg6f53u26fe69vl4qrt6fs0sphth3ez',
    #         'atx1ckxg24sa4clv239y93talm79h7ac8r20t4dl8e',
    #         'atx19qtc92y2s9a6dyvuqxrqwpsaztz95mel4xuhkv']
    # ac = 'atx1r8pvmt7hk6lk8uk7dtnfyrpcy9l8rfjry34uq9'
    # privateKey = ['b1b59658038c80d8f6f2b1f3d968417e938af6f5ea3c29d01aee4a4fb7f1a26f',
    #               '798c9a1a06564f4d9533c3a1d6fb96348b62a92c049d16669b871896c3bcd873',
    #               'ae5acd5e594a459bbe3faadc00ac64be79aa93251f0bd0243f05628a14657a2e',
    #               '127e0451e60c9c1df551dc9050362ab9ab7deeafa160672857aaf00f2b8c0139',
    #               '5d6514d3878eb2b98ae77d7d4cb687e17411f338fac61a5c24fb0e25d3499b45',
    #               '7b4a75bd91933c30d15f5aab5ce79cd4f886373d307fa91619f1e145a5f5c622',
    #               '4298456cd70c306cb4827f57bb59ec311b22d4694e8b4793344fcd2a96bafa7a',
    #               '969502cd2da5aac9eab511c0f85fd544db48e4311f34a2037e8479b9b412f9c0',
    #               'd01ccb8952c0107a5c49396bb7915ca6dbc1ad913b5e36370f540b5938f238c3',
    #               '3832e25a1f6feb6eb5e8c26c66494c7c9467181a635b8fa38cc51dd040f40bae',
    #               '2f98ef83dffae0ee71b9b5d9ad70901a671b6d718e36e8cbab9b9de6d6d76ecd',
    #               '80d9a69bff3eb0131c6237365399666a09a6b2c77ac861b858cc7dbf16efbb54',
    #               'e4633d9261cf53f5320e5af29273ba3a3e990d042b0f9dae89169db9e66b5a56',
    #               '504523e07a4d5c6a2e44fa18df316bfedfe58dedfa5a29c20d7153e70fd99850',
    #               'fbef6de59dd738e192dee8efbd96dc8a8432447173bbb835ecca43b39efd4b28',
    #               '687e466709fff60a681d58a892532a4673baebcb10f59dc559328611cbb1e41f',
    #               'b452ac93e4a65114eae569607460ae7b53a9f64c45c9e675ce79d7022fb2197c',
    #               'a0e6c7d073c13df70f8b85a5b9f9bc137a3c75c489f03f1497cc34ae2947d97b',
    #               '9085ec2a136adb886990419794528945f1b750fb770bf07e5778a124c6058c83',
    #               '3c1d0950c6329ba7376a5e7d06713edd34012947aa95dd78c1954d56e5d5632e',
    #               '71108275ade39f514162869f52183b19ce7ba70c9ac8ddccc86113e871fd1c03',
    #               '3f2ed71cba9c15decf008819a3c4d93dd0dffbb7888acb22ea4a0ad4c7bf35e8',
    #               '3a3fbabfddf9934c6ca1395b486db656be9e3a7fc66f7340a6332209432c3575',
    #               '4fe61a44da26bf1a09771f6b26d22a40e03250dc1ef2141208611485f0ea79d1',
    #               '7cb35bcebe5900bcdc7ea7fd47486128f4b22b8ecd1595bb47e8f8866b190d17',
    #               'a4a026cb5c7d10c7ebef0069528e43358b63de2dd707715b566fd177429d66b2',
    #               'c8cfb8fbc397a11dc5b9c3ce61b9498166edd1051abb4c30f61fa948d1cbba0c']
    # list = ['atp1n2yckcf0lp8fd4x3u4gqndyf7at4j9auanjd9r', 'atp1sga8gepxjlznwy6z9emerja95cqh57zrrsxa4z']
    # plan = [{'Epoch': 32, 'Amount': Web3.toWei(1000, 'ether')}]
    # createRestrictingPlan(url, account, plan, pri_key)
    # delegate(url, 0, nodeid, amount, pri_key)
    # plan = [{'Epoch': 1, 'Amount': amount1},
    #         {'Epoch': 8, 'Amount': amount1},
    #         {'Epoch': 16, 'Amount': amount1},
    #         {'Epoch': 32, 'Amount': amount1},
    #         {'Epoch': 64, 'Amount': amount1},
    #         {'Epoch': 128, 'Amount': amount1},
    #         {'Epoch': 300, 'Amount': amount1},
    #         {'Epoch': 400, 'Amount': amount1},
    #         {'Epoch': 500, 'Amount': amount1},
    #         {'Epoch': 600, 'Amount': amount1},
    #         {'Epoch': 700, 'Amount': amount1},
    #         {'Epoch': 800, 'Amount': amount2}]
    plan = [{'Epoch': 200, 'Amount': Web3.toWei(1000, 'ether')}]
    # address = 'atp1xsp5qwy9hgj26yujead2jmjlknhp2s7cqyh37u'
    # address = 'atx1lmcpsdp8cw899lu3wzmr5hxxplze82s2y3k4h9'
    node_id = 'f7a07f6ff8c282a4a1c1febaf68531bbb557fa262c641d022f249e926e222c9190602b502d2772fa4a2834ffb4bf6298f4c80467178e90728c5a852504f571ad'
    # print(Web3.fromWei(1000000000000000000000, 'ether'))
    node_id1 = 'd3f54cf2fbcb06e372573079f432513f328dde846ceebcc8915ea1ea9abf91e4ffefe42dc42f411850c23e177e81271703bbc16add6754c7df1a9c6ac6cbe63f'
    # pri_key1 = 'd357920de1df4ecb00cbce60ded2d73f3f51fd1e9fb79b08f366e301e849bd9d'
    # for i in list:
    #     print(i)
    #     createRestrictingPlan(url, i, plan, pri_key)
    # createRestrictingPlan(url, account, plan, pri_key1)
    # time.sleep(2)
    # get_RestrictingPlan(url, account)
    # fff(url)
    # sendTransaction(url, account1, pri_key1, account, Web3.toWei(1, 'ether'), 201030)
    web3 = connect_web3(url)
    print(web3.chain_id)
    # ppos = Ppos(web3)
    # platon = Eth(web3)
    # print(web3.is)
    # print(platon.blockNumber)
    # # print(platon.gasPrice)
    # tmp_amount = 0
    # tmp_amount1 = 0
    # for i in range(13):
    #     number = 160 * (i + 1)
    #     amount = platon.getBalance(account, number)
    #     print(account, amount)
    #     if amount is not None:
    #         y = amount - tmp_amount1
    #         tmp_amount1 = amount
    #         print("账户余额差：", y)
    #     amount = platon.getBalance(web3.restrictingAddress, number)
    #     print(web3.restrictingAddress, amount)
    #     if amount is not None:
    #         x = amount - tmp_amount
    #         tmp_amount = amount
    #         print("锁仓合约余额差：", x)
    # amount = platon.getBalance(account)
    # print(account, amount)
    # amount = platon.getBalance(ppos.restrictingAddress)
    # print(ppos.restrictingAddress, amount)
    # amount = platon.getBalance(web3.stakingAddress)
    # print(amount)
    # print(Web3.fromWei(2035626000000000000, 'ether'))
    # platon.gasPrice
    # withdrewStaking(url, node_id1, pri_key)
    # stakingnum = 335
    # node_id = '8ec906e2fdb09c8a45dbc193afe36ae7542e6c8efc96f06c566bf504c7b509691ef119accb0f95d6c9e51e053bd15c6ac5a568bd6f708508100e58d4d7a9036b'
    # resutl = get_VerifierList(url)['Ret']
    # print(len(resutl))
    # get_candidatelist(url)
    # StakingBlockNum = 515
    # get_candidatelist(url)
    # addresss = 'lat13l39glde394a6kkrm5aenj4ty7m7565x8sgtrf'
    # print(Web3.fromWei(1000000000000000000000, 'ether'))
    # fff()
    # get_listGovernParam(url)
    # getDelegateReward(url, account)
    # get_VerifierList(url)
    # withdraw_delegate_reward(url, pri_key)
    # node_config = LoadFile(os.path.abspath(os.path.join(BASE_DIR, "deploy/node/node-32.yml"))).get_data()
    # noconsensus_node_config_list = node_config.get("noconsensus", [])
    # node_id_list = [i['id'] for i in noconsensus_node_config_list]
    # for i in node_id_list:
    #     print(i)
    # delegate(url, 0, i, amount, pri_key)
    #     time.sleep(1)
    # getValidatorList(url)
    # amount = Web3.toWei(1000, 'ether')
    # amount = 6167000000000000000000
    # delegate(url, 1, node_id, amount, pri_key)
    # for pri_key in privateKey:
    # withdraw_delegate(url, 14, node_id, amount, pri_key)
    # time.sleep(2)
    # increase_staking(url, 1, node_id1, amount, pri_key)
    # createstaking(url, 1, pri_key, Web3.toWei(10000, 'ether'))
    # get_candinfo(url, node_id)
    # getDelegateInfo(url, 127, account, node_id)
    # get_RestrictingPlan(url, account)
    # get_RestrictingPlan(url, 'atp10llx4zpnjv52sst2skwyzxsd29lzk45neyspuy')
    list = ["atp1eshshnxuva6f4zqmwj9xszfj65y5vhalr7nyed",
            "atp166ue9gzupre59qsj9xvdxjwrzdrheentp9xlue",
            "atp13fd8zf6gp8jjn46uvlr5q5ayz73qgpzrzcwfdv",
            "atp15ftdv7s5sn7tswnqwegaxrdzhh9cezyaeuv7us",
            "atp1sp0uwm79fnva0x86kzj979psk7f8zpa9zark8j",
            "atp1std7ff5cjdezwe6pz7eq278jpmcaq2mef6d4e6",
            "atp1uyu68y0ygk5gzhg8402qmtg8hj8qwc4je3a2ym",
            "atp1hgerqd2erw89a6f0n9cch6azdm3mlkn7lnq0gp",
            "atp16wrzwyktqc09kjeydnq4jdtuuu793ced6jwyh2",
            "atp1wt9j640hw046jt86ttp7h0mvv66ctkplazxdxx",
            "atp1gkaqpw6q0syy8865yg7f9zd5fmt9mec4k4kx2z",
            "atp1d8paww9mxjar5rrek4mken8ca448xyp2hxsmx0",
            "atp1u9xc3rejevx4ux5p6fl5ghlgml5sa7mnnrwfkv",
            "atp1t0p4xrxq3rw24709rqvudc4ydph5gv43nfe9gj",
            "atp1fklu5nnuvjwhx50vz44y32upf69glx40yux69x",
            "atp1pv4eep9vzyy4rekyfs5xnve3kv20hhgqkdpnnm",
            "atp1jp7m5g4lwmk36932hxnxeupul93kcdwtlfq4p4",
            "atp1zsjz0zapqxe82amc98208x5992nnclvgynhhe4",
            "atp12jsctngpm8tn30scuc0dmpg9ncsc82rlz9vwjj",
            "atp1tql5puw2kf84d7czgh7lucrpd9vhm77h8fc5j6",
            "atp1g60w9nkqehx0w32hc8lhncyar3u9tgdhtyrpgp",
            "atp143u7s2rxqslvqsw8ehuj362kqfjsjlv8d3vjv8",
            "atp19kls6uhznrfcc2yg2q79sdcjfu780e6fhhg472",
            "atp1fj30cwd58djru06h8wwdrcdwh8w0p8qvjytck3",
            "atp1k5fh43wnd0gw339glgeyusjdzfm8cxdcw0nhgq",
            "atp1j6uj6dl06rjqxw73aknejalp78u04ru4ljwswf",
            "atp1guuc25qpqjghellen7uzhpetfdgevcx038nw4f",
            "atp1nvuk3v90cttx3zt5vzy7rnh4kny7tcy9uzftjh",
            "atp1mu0aws2g65hw0z77gzukzed83j3tcjuz366wn3",
            "atp1cwar0uy0lgz3vmfnu5ffagkrmqslpsh82v0vpc",
            "atp12k5nrdn29msfalhfe6jqw8y66m7fq4r5an376z",
            "atp1rknphx8hdq7rnkphy9j4p3cfa8y604fu5cxzew",
            "atp1m6l2jjr39qwf6kuwea5cfa0mn9nv96yt5kxxzx",
            "atp1krv3qnd08ke4y52ylvurdfxen7aq7wehlzqm9n",
            "atp18xtt0sqrg9qcd83u6659nhhdcs7kxzmyr3f44w",
            "atp1t32d3ellldszx5j240ru9qp568umpve9ps7pnk",
            "atp175z4sfjg33r0svp9cdra8hpasgfuxeug4h8fps",
            "atp1vxc0074lv8y3078v3ms9r0trktqqcgpu36xuz9",
            "atp1x8fv9scyvsmfnkf3utzpszrs52hv7e5z07z8sx",
            "atp18c6mfgzy68pfwqu4cnu4nwtl367qmsjy3j20d5",
            "atp1t5e4qzgygkhtj8tjgn72qtqtfu88jdmemsd59t",
            "atp1x2xgnxd3939h9yh07ay3xm7dh6peunsyae3mtz",
            "atp1y4z8ny5c0nhy6uan4nzx2mzv8jp9ntq7quxvgp",
            "atp1q3ffp495wavsuljmgrg3ds06z9ykpgepqa3ypx",
            "atp1npnfxe5gfcczw2659p4pk2ezwrprgvmjruhzfq",
            "atp1225wvv6ug5y28dp0rrr8w9nxedkm8hcglfnk0d",
            "atp1s3rfmcmm4zdz529rvwuagfvqrq5c44e2ja46kz",
            "atp1fnehxk8jcwaquerf4trx03l9na7a56yyfcjklh"]
    # fix_account = []
    # for i in list:
    #     restricting_info = get_RestrictingPlan(url, i)['Ret']
    #     pledge = restricting_info['Pledge']
    #     debt = restricting_info['debt']
    #     balance = restricting_info['balance']
    #     if pledge > balance:
    #         print(i, balance, debt, pledge, pledge - balance)
            # fix_account.append(i)

    # print(fix_account)
    # staking_address_list = []
    # candidatelist = get_candidatelist(url)['Ret']
    # for i in candidatelist:
    #     staking_address = i['StakingAddress']
    #     staking_address_list.append(staking_address)
    # for j in list:
    #     for k in staking_address_list:
    #         if k == j:
    #             # fix_account.append(i)
    #             print(j)

    # print(fix_account)
