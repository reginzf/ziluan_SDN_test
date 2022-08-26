class HttpCodeException(Exception):
    def __init__(self, info, code: int):
        self.info = info
        self.code = code

    def __str__(self):
        return 'HttpCode:{}\n{}'.format(self.code, self.info)
