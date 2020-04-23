import cbat
import xlrd

from cbat.models import Conference

# def load_from_xlsx(path):
#     """Loads conference names from xlsx file"""
#     workbook = xlrd.open_workbook(path, "rb")
#     sheets = workbook.sheet_names()
#     conferences = []
#     for sheet_name in sheets:
#         sh = workbook.sheet_by_name(sheet_name)
#         for rownum in range(2, sh.nrows):
#             row = sh.row_values(rownum)
#             conferences.append(Conference(name=row[1], acronym=row[2]))
#     return conferences

# confs = load_from_xlsx("./cbat/data/cini.xlsx")[0:10]

conf = Conference(name="IEEEEEEE", acronym="SIGCOMM")
cbat.add_conference(conf)