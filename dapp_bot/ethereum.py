from eth_utils.address import is_address



class EthereumApi:
    def __init__(self, project_id: str):
        self.api = 'https://mainnet.infura.io/v3/' + project_id
        self.template = {"jsonrpc": "2.0",
                         "id": 1,
                         "method": "",
                         "params": []}

    def _post(self, method, *args, **params):
        data = copy(self.template)

        data['method'] = method
        if params:
            data['params'].append(params)
        data['params'].extend([*args])

        print(data)
        return requests.post(self.api, json=data).json()['result']

    def is_address(self, addr):
        return is_address(addr)

    def __getattr__(self, item):
        return functools.partial(self._post, item)
