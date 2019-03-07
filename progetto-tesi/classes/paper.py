class Paper:
    def __init__(self, scopus_id, references=list()):
        self.scopus_id = scopus_id
        self.references = references
    
    def getattr(self, key, default=""):
        if self.__getattribute__(key) is None:
            return default
        else:
            return self.__getattribute__(key)


class Reference:
    def __init__(self, paper_id, authors):
        self.paper_id = paper_id
        self.authors = authors

    def getattr(self, key, default=""):
        if self.__getattribute__(key) is None:
            return default
        else:
            return self.__getattribute__(key)