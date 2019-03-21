from mongoengine import *


class Author(Document):
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
    scopus_id = StringField()
    program_refs = ListField(ReferenceField(Author))
    non_program_refs = ListField(ReferenceField(Author))

    def getattr(self, key, default=""):
        return default if self.__getattribute__(key) is None else self.__getattribute__(key)


class Conference(Document):
    fullname = StringField()
    name = StringField()
    year = IntField()
    program_committee = ListField(ReferenceField(Author))
    papers = ListField(ReferenceField(Paper))
    wikicfp_url = StringField()
    wikicfp_id = StringField()

    def getattr(self, key, default=""):
        return default if self.__getattribute__(key) is None else self.__getattribute__(key)
    