import sys
from pathlib import Path
from uuid import uuid4

from enums import LeadSource, AccountType, AccountStage, OpportunityStage
from utils import draw_value_beta


class Account:
    def __init__(self, 
                 env, 
                 name,
                 country=None,
                 industry=None,
                 lead_source=LeadSource.WEBSITE_CTA, 
                 account_type=AccountType.MEDIUM
                 ):
        self.env = env
        self.uid = 'acct-' + str(uuid4())
        self.name = name
        self.country = country if country else 'Unknown'
        self.industry = industry if industry else 'Unknown'
        self.account_type = account_type
        self.stage = AccountStage.MQL
        self.sales_rep = SalesRep(env, 'default_sales_rep')
        self.created = env.now
        self.lead_source = lead_source

    def set_sales_rep(self, sales_rep):
        self.sales_rep = sales_rep
        
    def __repr__(self):
        return f"Account(name={self.name}, type={self.account_type}, stage={self.stage})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the account."""
        attrs_2_include = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))] + ['sales_rep']
        return {a:getattr(self,a) for a in attrs_2_include}


class Opportunity:

    _osizes = {
        AccountType.SMALL:{'val_min': 10_000, 'val_max': 100_000},
        AccountType.MEDIUM:{'val_min': 100_000, 'val_max': 500_000},
        AccountType.LARGE:{'val_min': 500_000, 'val_max': 2_000_000},
    }

    def __init__(
        self, 
        env,
        account, 
        name, 
        stage=OpportunityStage.IDENTIFIED, 
        source=None
        ):

        self.env = env
        self.account = account
        self.name = name
        self.stage = stage
        self.source = source if source else account.lead_source
        self.id = uuid4()
        self.created_at = env.now
        self.value = self.draw_value()

    def draw_value(self) -> int:
        """Draw a random value for the opportunity within the range for the account type"""
        acct_type = self.account.account_type
        val_min, val_max = self._osizes.get(acct_type, {'val_min': 10_000, 'val_max': 100_000}).values()
        value = draw_value_beta(val_min, val_max)
        return value

    def __repr__(self) -> str:
        return f"Opportunity({self.id}, {self.name} {self.account}, {self.stage}, {self.source})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the opportunity."""
        attrs = set([a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))])
        attrs_2_exclude = set(['env'])           # exclude 
        attrs_2_include = set(['account'])      # callable classes to still include
        attrs = sorted(list(attrs.difference(attrs_2_exclude).union(attrs_2_include)))
        return {a:getattr(self,a) for a in attrs}


class SalesRep:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.uid = 'srep-' + str(uuid4())
        self.created = env.now

    def __repr__(self):
        return f"SalesRep(name={self.name} uid={self.uid})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the account."""
        return {a:getattr(self,a) for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))}