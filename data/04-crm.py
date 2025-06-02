"""
Python model '04-crm.py'
Translated using PySD
"""

from pathlib import Path
import numpy as np

from pysd.py_backend.functions import integer
from pysd.py_backend.statefuls import Integ
from pysd import Component

__pysd_version__ = "3.14.3"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 100,
    "time_step": lambda: 1,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    The final time for the simulation.
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Month", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    The initial time for the simulation.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    The frequency with which output is stored.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP",
    units="Month",
    limits=(0.0, np.nan),
    comp_type="Constant",
    comp_subtype="Normal",
)
def time_step():
    """
    The time step for the simulation.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="active",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_active": 1},
    other_deps={
        "_integ_active": {"initial": {}, "step": {"satisfied": 1, "completed": 1}}
    },
)
def active():
    return _integ_active()


_integ_active = Integ(lambda: satisfied() - completed(), lambda: 0, "_integ_active")


@component.add(name="bid2close", comp_type="Constant", comp_subtype="Normal")
def bid2close():
    return 0.3


@component.add(
    name="bidded",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_bidded": 1},
    other_deps={
        "_integ_bidded": {
            "initial": {},
            "step": {"bids": 1, "contracts": 1, "lost_bids": 1},
        }
    },
)
def bidded():
    return _integ_bidded()


_integ_bidded = Integ(
    lambda: bids() - contracts() - lost_bids(), lambda: 0, "_integ_bidded"
)


@component.add(
    name="bids",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"pitched": 1, "prez2bid": 1},
)
def bids():
    return integer(pitched() * prez2bid())


@component.add(
    name="completed",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"active": 1},
)
def completed():
    return integer(0.9 * active())


@component.add(
    name="contracts",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"bidded": 1, "bid2close": 1},
)
def contracts():
    return integer(bidded() * bid2close())


@component.add(
    name="customer satisfaction rate", comp_type="Constant", comp_subtype="Normal"
)
def customer_satisfaction_rate():
    return 0.98


@component.add(name="decay rate", comp_type="Constant", comp_subtype="Normal")
def decay_rate():
    return 0.15


@component.add(
    name="lost bids",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"bidded": 1, "bid2close": 1},
)
def lost_bids():
    return integer(bidded() * bid2close())


@component.add(
    name="mql",
    units="Co",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_mql": 1},
    other_deps={
        "_integ_mql": {
            "initial": {},
            "step": {"new_mql": 1, "mql_decay": 1, "sales_qualified": 1},
        }
    },
)
def mql():
    return _integ_mql()


_integ_mql = Integ(
    lambda: new_mql() - mql_decay() - sales_qualified(), lambda: 100, "_integ_mql"
)


@component.add(
    name="mql decay",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"mql": 1, "decay_rate": 1},
)
def mql_decay():
    return integer(mql() * decay_rate())


@component.add(
    name="mql industry events",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rawleads_industry_events": 1, "rawlead2mql_industry_event": 1},
)
def mql_industry_events():
    return integer(rawleads_industry_events() * rawlead2mql_industry_event())


@component.add(
    name="mql online campaign",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rawleads_online_campaign": 1, "rawlead2mql_online_campaign": 1},
)
def mql_online_campaign():
    return integer(rawleads_online_campaign() * rawlead2mql_online_campaign())


@component.add(
    name="mql salesreps",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rawleads_salesreps": 1, "salesrep_leads2mql": 1},
)
def mql_salesreps():
    return integer(rawleads_salesreps() * salesrep_leads2mql())


@component.add(
    name="mql website",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"raw_leads_from_website": 1, "rawlead2mql_website": 1},
)
def mql_website():
    return integer(raw_leads_from_website() * rawlead2mql_website())


@component.add(name="mql2sql", comp_type="Constant", comp_subtype="Normal")
def mql2sql():
    return 0.15


@component.add(name="nb industry events", comp_type="Constant", comp_subtype="Normal")
def nb_industry_events():
    return 1


@component.add(
    name="nb mthly website visitor", comp_type="Constant", comp_subtype="Normal"
)
def nb_mthly_website_visitor():
    return 2900


@component.add(
    name="new mql",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "mql_website": 1,
        "mql_online_campaign": 1,
        "mql_industry_events": 1,
        "mql_salesreps": 1,
    },
)
def new_mql():
    return integer(
        mql_website() + mql_online_campaign() + mql_industry_events() + mql_salesreps()
    )


@component.add(
    name="new prospects",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sql": 1, "sql2prospect": 1},
)
def new_prospects():
    return integer(sql() * sql2prospect())


@component.add(
    name="online campaigns clickthru", comp_type="Constant", comp_subtype="Normal"
)
def online_campaigns_clickthru():
    return 0.1


@component.add(
    name="online campaigns targets",
    units="Co",
    comp_type="Constant",
    comp_subtype="Normal",
)
def online_campaigns_targets():
    return 1000


@component.add(
    name="pitched",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_pitched": 1},
    other_deps={
        "_integ_pitched": {
            "initial": {},
            "step": {"presentations": 1, "bids": 1, "stale_prospects": 1},
        }
    },
)
def pitched():
    return _integ_pitched()


_integ_pitched = Integ(
    lambda: presentations() - bids() - stale_prospects(), lambda: 0, "_integ_pitched"
)


@component.add(
    name="presentations",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"prospects": 1, "prospect2prez": 1},
)
def presentations():
    return integer(prospects() * prospect2prez())


@component.add(name="prez2bid", comp_type="Constant", comp_subtype="Normal")
def prez2bid():
    return 0.6


@component.add(
    name="prospect decay",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"prospects": 1, "decay_rate": 1},
)
def prospect_decay():
    return integer(prospects() * decay_rate())


@component.add(name="prospect2prez", comp_type="Constant", comp_subtype="Normal")
def prospect2prez():
    return 0.7


@component.add(
    name="prospects",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_prospects": 1},
    other_deps={
        "_integ_prospects": {
            "initial": {},
            "step": {"new_prospects": 1, "presentations": 1, "prospect_decay": 1},
        }
    },
)
def prospects():
    return _integ_prospects()


_integ_prospects = Integ(
    lambda: new_prospects() - presentations() - prospect_decay(),
    lambda: 0,
    "_integ_prospects",
)


@component.add(
    name="raw leads from website",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"website_cta_rate": 1, "nb_mthly_website_visitor": 1},
)
def raw_leads_from_website():
    return integer(website_cta_rate() * nb_mthly_website_visitor())


@component.add(
    name="rawlead2mql industry event", comp_type="Constant", comp_subtype="Normal"
)
def rawlead2mql_industry_event():
    return 0.3


@component.add(
    name="rawlead2mql online campaign", comp_type="Constant", comp_subtype="Normal"
)
def rawlead2mql_online_campaign():
    return 0.38


@component.add(name="rawlead2mql website", comp_type="Constant", comp_subtype="Normal")
def rawlead2mql_website():
    return 0.41


@component.add(
    name="rawleads industry events",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"nb_industry_events": 1},
)
def rawleads_industry_events():
    return 80 * nb_industry_events()


@component.add(
    name="rawleads online campaign",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"online_campaigns_clickthru": 1, "online_campaigns_targets": 1},
)
def rawleads_online_campaign():
    return integer(online_campaigns_clickthru() * online_campaigns_targets())


@component.add(
    name="rawleads salesreps", units="Co", comp_type="Constant", comp_subtype="Normal"
)
def rawleads_salesreps():
    return 30


@component.add(
    name="sales qualified",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"mql": 1, "mql2sql": 1, "sql_salesreps": 1},
)
def sales_qualified():
    return integer(mql() * mql2sql() + sql_salesreps())


@component.add(name="salesrep leads2mql", comp_type="Constant", comp_subtype="Normal")
def salesrep_leads2mql():
    return 0.02


@component.add(
    name="satisfied",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"signed": 1, "customer_satisfaction_rate": 1},
)
def satisfied():
    return integer(signed() * customer_satisfaction_rate())


@component.add(
    name="signed",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_signed": 1},
    other_deps={
        "_integ_signed": {
            "initial": {},
            "step": {"contracts": 1, "satisfied": 1, "unsatisfied": 1},
        }
    },
)
def signed():
    return _integ_signed()


_integ_signed = Integ(
    lambda: contracts() - satisfied() - unsatisfied(), lambda: 0, "_integ_signed"
)


@component.add(
    name="sql",
    units="Co",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sql": 1},
    other_deps={
        "_integ_sql": {
            "initial": {},
            "step": {
                "completed": 1,
                "lost_bids": 1,
                "sales_qualified": 1,
                "stale_prospects": 1,
                "new_prospects": 1,
                "sql_decay": 1,
            },
        }
    },
)
def sql():
    return _integ_sql()


_integ_sql = Integ(
    lambda: completed()
    + lost_bids()
    + sales_qualified()
    + stale_prospects()
    - new_prospects()
    - sql_decay(),
    lambda: 0,
    "_integ_sql",
)


@component.add(
    name="sql decay",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sql": 1, "decay_rate": 1},
)
def sql_decay():
    return integer(sql() * decay_rate())


@component.add(
    name="sql salesreps",
    units="Co",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rawleads_salesreps": 1, "salesrep_leads2mql": 1},
)
def sql_salesreps():
    return rawleads_salesreps() * (1 - salesrep_leads2mql())


@component.add(name="sql2prospect", comp_type="Constant", comp_subtype="Normal")
def sql2prospect():
    return 0.7


@component.add(
    name="stale",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_stale": 1},
    other_deps={"_integ_stale": {"initial": {}, "step": {"unsatisfied": 1}}},
)
def stale():
    return _integ_stale()


_integ_stale = Integ(lambda: unsatisfied(), lambda: 0, "_integ_stale")


@component.add(
    name="stale prospects",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"pitched": 1, "prez2bid": 1},
)
def stale_prospects():
    return integer(pitched() * (1 - prez2bid()))


@component.add(
    name="unsatisfied",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"signed": 1, "customer_satisfaction_rate": 1},
)
def unsatisfied():
    return integer(signed() * (1 - customer_satisfaction_rate()))


@component.add(name="website cta rate", comp_type="Constant", comp_subtype="Normal")
def website_cta_rate():
    return 0.03
