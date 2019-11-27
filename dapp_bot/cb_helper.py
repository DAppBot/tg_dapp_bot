def cb_filter(name, args=None):
    def nested_filter(callback):
        if callback.data.endswith(name):
            if not args:
                return True
            args_from_cb = callback.data.split(name)[0].rstrip('_').split('_')
            print(dict(zip(args, args_from_cb)))
            return dict(zip(args, args_from_cb))

    return nested_filter

