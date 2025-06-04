import simpy
import random

from uuid import uuid4
from enum import Enum, auto
from enums import AccountStage, AccountType, Industry, Country

# 1. Define the sales funnel stages
# class Stage(Enum):
#     LEAD = auto()
#     MQL = auto()
#     SQL = auto()
#     PROSPECT = auto()
#     OPPORTUNITY = auto()
#     CUSTOMER = auto()
#     LOST = auto()
    # PROSPECTS = auto()   
    # PITCHED = auto()
    # BIDDED = auto()
    # SIGNED = auto()
    # ACTIVE = auto()
    # STALE = auto()

# 2. Global parameters (can be tweaked)
LEAD_CONVERSION_RATES = {
    'inbound_mktg_event': 0.3,          # CTA on website, blogs, social media, webinars
    'outbound_mktg_event': 0.2,         # Email campaigns, ads, industry events, ...
    'inbound_sales_event': 0.2,         # CTA on website leading to a specific request for pricing
    'outbound_sales_event': 0.15,       # Cold calls
}
DELAY_RANGES = {
    'inbound_mktg_event': (1, 3),
    'outbound_mktg_event': (2, 5),
    'inbound_sales_event': (1, 2),
    'outbound_sales_event': (2, 4),
}

# 3. Account agent
class Account:

    _counter_start = 0

    @classmethod
    def acct_counter(cls):
        cls._counter_start += 1
        return cls._counter_start

    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.uid = uuid4()
        self.stage = AccountStage.LEAD
        self.name, self.country, self.industry, self.account_type = self.get_account_info()

        self.source = None
        self.salesrep = None  # Placeholder for sales rep, if needed
        
        self.action = env.process(self.run())
        self.created_at = env.now   # Record creation time
        
        self.action = env.process(self.run())
        self.env.accounts.append(self)
        self.log(f"Account created: {self.name} (UID: {self.uid}) at stage {self.stage.name}")

    def get_account_info(self):
        # Placeholder for setting account type logic
        name = f'Acct {Account.acct_counter()}'
        country = Country.EU
        industry = Industry.Electronics
        acct_type = AccountType.SMALL
        return name, country, industry, acct_type

    def random_delay(self, event_name):
        low, high = DELAY_RANGES[event_name]
        return random.uniform(low, high)

    def decide(self, event_name):
        return random.random() < LEAD_CONVERSION_RATES[event_name]

    def log(self, msg):
        print(f"[{self.env.now:.2f}] {self.name}: {msg}")

    def run(self):
        # Events when Account is a LEAD: can convert to MQL, or SQL (through inbound sales)
        if self.stage == AccountStage.LEAD:
            # Conversion from LEAD to MQL
            if self.decide('inbound_mktg_event'):
                yield self.env.timeout(self.random_delay('inbound_mktg_event'))
                self.stage = AccountStage.MQL
                self.log("Lead converted via inbound marketing to MQL")
            elif self.decide('outbound_mktg_event'):
                yield self.env.timeout(self.random_delay('outbound_mktg_event'))
                self.stage = AccountStage.MQL
                self.log("Lead converted via outbound marketing to MQL")
            # Conversion from LEAD to SQL
            if self.decide('inbound_sales_event'):
                yield self.env.timeout(self.random_delay('inbound_sales_event'))
                self.stage = AccountStage.SQL
                self.log("Lead converted via inbound sales to SQL")
            elif self.decide('outbound_sales_event'):
                yield self.env.timeout(self.random_delay('outbound_sales_event'))
                self.stage = AccountStage.SQL
                self.log("Lead converted via outbound sales to MQL")
            else:
                self.log("Lead did not yet convert to MQL or SQL")
                return

        # Continue as needed for further stages...

# 4. Account arrival process
def account_arrival(env, initial_n, arrival_rate):
    # Initial batch
    for i in range(initial_n):
        Account(env, f"Company_{i+1}")
    idx = initial_n
    # Arrivals over time
    while True:
        yield env.timeout(random.expovariate(arrival_rate))
        idx += 1
        Account(env, f"Company_{idx}")

def accounts_created_before(t, env):
    return [acc for acc in env.accounts if acc.created_at <= t]

# Run simulation
def main():
    random.seed(1988)
    env = simpy.Environment()
    env.accounts = []  # List to hold all accounts
    initial_accounts = 5
    arrival_rate = 0.5  # on average, one new account every 2 units of time
    env.process(account_arrival(env, initial_accounts, arrival_rate))
    env.run(until=20)

if __name__ == "__main__":
    main()