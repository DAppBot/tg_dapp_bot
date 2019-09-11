import math

def compose_wallets(list_w, i=0, pattern=['ethereum', 'tron']):
    compose_list_w = []
    for blockchain in pattern:
        some_blockchain_w_list = []
        for wallet in list_w:
            if wallet[i] == blockchain:
                some_blockchain_w_list.append(wallet[1])
        compose_list_w.append(some_blockchain_w_list)
    return compose_list_w

def reduction_addr(addr, lenght=15):
    if len(addr) <= lenght:
        return addr
    len_visible_part = math.ceil(lenght/2 - 1.5)
    number_points  = lenght - len_visible_part*2
    return addr[:len_visible_part + 2] + '.' * number_points + addr[-len_visible_part + 2:]



l = [['tron', 'asdfa34sd'],
     ['tron', '2gaweg345gghj'],
     ['ethereum', 'as3as'],
     ['tron', 'asdfa3sdfsdfsdfsdf4sd'],
     ['ethereum', 'as3aasdasds'],
     ['ethereum', 'aas'],
     ['tron', 'asdfa3sdfsdfsdfsdf4sdasdasd'],
     ['ethereum', '66hfsaas'],
     ]

