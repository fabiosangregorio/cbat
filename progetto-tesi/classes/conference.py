class Conference:
    def __init__(self, fullname, name=None, year=None, papers=None):
        self.fullname = fullname
        self.name = name
        self.year = year
        self.papers = papers
    
    def getattr(self, key, default=""):
        if self.__getattribute__(key) is None:
            return default
        else:
            return self.__getattribute__(key)