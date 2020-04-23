import cbat
from cbat.models import Conference

if __name__ == "__main__":
    conf = Conference(name="Conference on Applications, Technologies, Architectures, and Protocols for Computer Communication", acronym="SIGCOMM")
    cbat.add_conference(conf)
    corr_coeff = cbat.plot_refs()
