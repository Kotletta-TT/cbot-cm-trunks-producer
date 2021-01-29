class Trunk:

    def __init__(self, provider, obj, trunk_username, trunk_password, phone=None, attributes=None):
        self.provider = provider
        self.obj = obj
        self.trunk_username = trunk_username
        self.trunk_password = trunk_password
        self.phone = phone
        self.active = True if self.phone is not None else False
        self.attributes = attributes
