from mongoengine import *


class Author(Document):
    _id = StringField()
    fullname = StringField()
    firstname = StringField()
    middlename = StringField()
    lastname = StringField()
    affiliation = StringField()
    dblp_url = StringField()
    eid_list = ListField(StringField())

    def getattr(self, key, default=""):
        return default if self.__getattribute__(key) is None else self.__getattribute__(key)



class Paper(Document):
    _id = StringField()
    scopus_id = StringField()
    references = ListField(ReferenceField(Author))

    def getattr(self, key, default=""):
        return default if self.__getattribute__(key) is None else self.__getattribute__(key)


class Conference(Document):
    _id = StringField()
    fullname = StringField()
    name = StringField()
    year = IntField()
    program_committee = ListField(ReferenceField(Author))
    papers = ListField(ReferenceField(Paper))
    wikicfp_url = StringField()

    def getattr(self, key, default=""):
        return default if self.__getattribute__(key) is None else self.__getattribute__(key)
    