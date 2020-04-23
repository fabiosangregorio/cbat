from cbat.main import add_conference
from cbat.models import Conference

if __name__ == "__main__":
    conference = Conference(name="IEEEEEEE", acronym="SIGCOMM")
    add_conference(conference)