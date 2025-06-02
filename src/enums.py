from enum import Enum, auto

class AccountStage(Enum):
    """
    Enum representing the state of a sales process.
    """
    # Prospecting
    MQL = 1
    # Qualification
    SQL = 2
    # Needs Assessment
    PROSPECTS = 3   
    # Presentation
    PITCHED = 4
    # Objection Handling, Bidding
    BIDDED = 5
    # Negotiating, Closing
    SIGNED = 6
    # Post-Sales Follow-up
    ACTIVE = 7
    STALE = 8

class OpportunityStage(Enum):
    """
    Enum representing the stage of an opportunity in the sales process.
    """
    IDENTIFIED = auto()
    PITCHED = auto()
    BIDDED = auto()
    CLOSED_WON = auto()
    CLOSED_LOST = auto()
    CLOSED_STALE = auto()

class AccountStatus(Enum):
    LEAD = auto()
    PROSPECT = auto()
    OPPORTUNITY = auto()
    ACTIVE = auto()
    STALE = auto()
    

class AccountType(Enum):
    """
    Enum representing the type of account.
    """
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()


class PurchaseOrderSize(Enum):
    """
    Enum representing the size of a purchase order.


    
    """
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    ENTERPRISE = auto()

class LeadSource(Enum):
    """
    Enum representing the source of a lead.
    """
    WEBSITE_CTA = auto()
    EMAIL_CAMPAIGN = auto()
    INDUSTRY_EVENT = auto()
    SALES_REP = auto()
    EXISTING_CUSTOMER = auto()

class Month(Enum):
    """Enum representing one month in various time periods"""
    IN_MONTH = 1
    IN_WEEKS = IN_MONTH * 4
    IN_DAYS = IN_WEEKS * 5
    IN_HOURS = IN_DAYS * 8