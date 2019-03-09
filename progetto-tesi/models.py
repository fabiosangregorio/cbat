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


class Paper(Document):
    _id = StringField()
    scopus_id = StringField()
    references = ListField(ReferenceField(Author))


class Conference(Document):
    _id = StringField()
    fullname = StringField()
    name = StringField()
    year = IntField()
    program_committee = ListField(ReferenceField(Author))
    papers = ListField(ReferenceField(Paper))
    wikicfp_url = StringField()
    
