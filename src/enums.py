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

class MktgIntents(Enum):
    """Enum for all possible intents from Marketing to Accounts"""
    EMAIL_CAMPAIGN = "email campaign"
    INDUSTRY_EVENT = "industry event"

class SalesIntents(Enum):
    """Enum for all possible messages from SalesRep to Accounts"""
    USER_NEED = "user need discovery"
    PRESENTATION = "rv for presentation"
    BID = "opportunity to bid"
    NEGO = "negotiation"

class OpsIntents(Enum):
    """Enum for all possible intents from Operations to Accounts"""
    FEEDBACK_AT_COMPLETION = "feedback after project completion"

class Actions(Enum):
    """Enum for all possible actions in the CRM"""
    REQUEST = 'request'
    ACCEPT = 'accept'
    REJECT = 'reject'
    POSITIVE = 'satisfied'
    NEGATIVE = 'unsatisfied'

class InternalMessages(Enum):
    MQL2SQL = 'MQL to SQL conversion'
    SQL2SQL = 'No conversion out of SQL'
    SQL2PROSPECT = 'SQL 2 PROSPECT conversion'
    PROSPECT2PROSPECT = 'No conversion out of PROSPECT'
    PROSPECT2PITCHED = 'PROSPECT to PITCHED conversion'
    PITCHED2BIDDED = 'PITCHED to BIDDED conversion'
    PITCHED2PROSPECT = 'Back to PROSPECT, not invited for bidding'
    BIDDED2SIGNED = 'BIDDED to SIGNED conversion'
    BIDDED2SQL = 'Back to SQL, bid lost'
    SIGNED2ACTIVE = 'SIGNED to SATISFIED'
    SIGNED2STALE = 'SIGNED to UNSATISFIED'
