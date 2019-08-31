def compose_wallets_one(list_w, i=0, pattern=['tron', 'ethereum']):
    compose_list_w = []
    for blockchain in pattern:
        some_blockchain_w_list = []
        for wallet in list_w:
            if wallet[i] == blockchain:
                some_blockchain_w_list.append(wallet)
        compose_list_w.append(some_blockchain_w_list)
    return compose_list_w


l = [['tron', 'asdfa34sd'],
     ['tron', '2gaweg345gghj'],
     ['ethereum', 'as3as'],
     ['tron', 'asdfa3sdfsdfsdfsdf4sd'],
     ['ethereum', 'as3aasdasds'],
     ['ethereum', 'aas'],
     ['tron', 'asdfa3sdfsdfsdfsdf4sdasdasd'],
     ['ethereum', '66hfsaas'],
     ]

