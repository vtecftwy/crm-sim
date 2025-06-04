from enum import Enum, auto

class AccountStage(Enum):
    """
    Enum representing the state of a sales process.
    """
    # Latent
    LEAD = auto()
    # Prospecting
    MQL = auto()
    # Qualification
    SQL = auto()
    # Needs Assessment
    PROSPECT = auto()   
    # Presentation
    PITCHED = auto()
    # Objection Handling, Bidding
    BIDDED = auto()
    # Negotiating, Closing
    SIGNED = auto()
    # Post-Sales Follow-up
    ACTIVE = auto()
    STALE = auto()

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

class Industry(Enum):
    FoodnBeverage = auto()
    ConsumerGoods = auto()
    Pharmaceuticals = auto()
    IndustrialManufacturing = auto()
    Chemicals = auto()
    Electronics = auto()
    AutomotiveParts = auto()
    PackagingSI = auto()

class Country(Enum):
    EU = auto()
    US = auto
    CN = auto()

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