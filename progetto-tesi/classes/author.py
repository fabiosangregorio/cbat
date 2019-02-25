class Author:
    def __init__(self, fullname, firstname=None, middlename=None, lastname=None, affiliation=None, dblp_url=None, eid_list=None):
        self.fullname = fullname
        self.firstname = firstname
        self.middlename = middlename
        self.lastname = lastname
        self.affiliation = affiliation
        self.dblp_url = dblp_url
        self.eid_list = eid_list
    
    def getattr(self, key, default=""):
        if self.__getattribute__(key) is None:
            return default
        else:
            return self.__getattribute__(key)