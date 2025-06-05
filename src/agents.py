import simpy
import random

from uuid import uuid4
from enum import Enum, auto
from enums import AccountStage, AccountType, Industry, Country, LeadSource
from enums import MarketingMessages, SalesRepMessages, SalesRejectionMessages, InternalMessages, OpsMessages

# Global parameters (can be tweaked)
LEAD_CONVERSION_RATES = {
    'inbound_mktg_event': 0.3,          # CTA on website, blogs, social media, webinars
    'outbound_mktg_event': 0.2,         # Email campaigns, ads, industry events, ...
    'inbound_sales_event': 0.2,         # CTA on website leading to a specific request for pricing
    'outbound_sales_event': 0.15,       # Cold calls
}
DELAY_RANGES = {
    'inbound_mktg_event': (2, 5),
    'outbound_mktg_event': (2, 5),
    'inbound_sales_event': (3, 5),
    'outbound_sales_event': (3, 5),
}


class MarketingDpt:
    """simpy agent representing the Marketing Department

    controls folowing processes"
    - sending email campaigns
    - checking inbox for responses from accounts, move accounts to MQL stage and assign SalesRep
    """

    msgs = MarketingMessages
    intmsgs = InternalMessages
    mktg_conversion_rates = {
        'inbound_mktg_event': 0.3,          # CTA on website, blogs, social media, webinars
        'outbound_mktg_event': 0.2,         # Email campaigns, ads, industry events, ...
        'inbound_sales_event': 0.2,         # CTA on website leading to a specific request for pricing
        'outbound_sales_event': 0.15,       # Cold calls
    }

    msg2stages = {
        msgs.EMAIL_CAMPAIGN.value: AccountStage.MQL,
        msgs.INDUSTRY_EVENT.value: AccountStage.MQL,
        msgs.WEBSITE_CTA.value: AccountStage.MQL
    }
    
    def __init__(self, env):
        self.env: simpy.Environment = env
        self.name:str = 'Marketing'
        self.uid:str = 'mktg-' + str(uuid4())
        self.inbox = simpy.Store(env)
        self.nb_targetted_accounts:int = 3
        self.nb_yearly_campaigns:float = 52/3
        # Register processes 
        self.env.process(self.send_email_campaign())
        self.env.process(self.check_inbox())

    # Utility Functions
    def get_mql_accounts(self):
        return [a for a in self.env.accounts if a.stage == AccountStage.MQL] # type: ignore

    def assign_salesrep(self, account):
        """Get the list of sales reps in the environment."""
        salesrep = self.pick_salesrep(account)
        account.assigned_salesrep = salesrep
        salesrep.assigned_accounts.append(account)
        self.log(f"Assigned {account.name} to {salesrep.name}")

    def pick_salesrep(self, account):
        return sorted(self.env.salesreps, key=lambda x: len(x.assigned_accounts), reverse=False)[0] # type: ignore

    # Processes
    def send_email_campaign(self):
        while True:
            targetted = self.pick_targetted_accounts()
            self.log(f"{len(targetted)} accounts targetted for email campaign")
            for account in targetted:
                yield account.inbox.put('email campaign')
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=self.msgs.EMAIL_CAMPAIGN.value,
                    type_trans='External')
                self.log(f"Sent email targeting {account.name}")
            time_to_next_campaign = self.compute_time_to_next_campaign()
            self.log(f"Next campaign at {self.env.now + time_to_next_campaign:.2f}")
            yield self.env.timeout(time_to_next_campaign)

    def pick_targetted_accounts(self):
        mql = self.get_mql_accounts()
        nb_mql = len(mql)
        self.log(f"Found {nb_mql} MQL accounts")
        return random.sample(mql, min(self.nb_targetted_accounts,nb_mql))

    def compute_time_to_next_campaign(self):
        """Compute the time in weeks to the next campaign"""
        return int(52 / max(self.nb_yearly_campaigns, 1))

    def check_inbox(self):
        while True:
            # Receive confirmation from account
            msg = yield self.inbox.get()
            self.log(f"Received message: {msg}")
            uid, msg = msg.split('|||')
            self.record_crm_transaction(
                initiator_uid=uid, 
                recipient_uid=self.uid, 
                msg=msg,
                type_trans='External'
                )
            if msg in list(self.msg2stages.keys()):
                mql = self.get_mql_accounts()
                loa = [a for a in mql if a.uid == uid]
                account = loa[0] if loa else None
                if account:
                    account.stage = AccountStage.SQL
                    self.log(f"Converted {account.name} to {account.stage.name} stage")
                    self.assign_salesrep(account)
                    self.record_crm_transaction(
                        initiator_uid=self.uid, 
                        recipient_uid=uid, 
                        msg=self.intmsgs.MQL2SQL.name,
                        type_trans='Internal'
                        )

    # Reporting and Stats
    def record_crm_transaction(self, initiator_uid, recipient_uid, msg, type_trans, **kwargs):
        """Record a transaction in the environment system."""
        record = {
            'timestamp': self.env.now,
            'initiator': initiator_uid,
            'recipient': recipient_uid,
            'message': msg,
            'type': type_trans,
        }
        record.update(kwargs)
        if hasattr(self.env, 'crm_transactions'):
            self.env.crm_transactions.append(record)    # type: ignore
        else:
            self.env.crm_transactions = [record]  # type: ignore

    def log(self, msg):
        print(f"[{self.env.now:.2f}] {self.name}: {msg}")


class SalesRep:
    """simpy agent representing a Sales Representative

    controls following processes:
    - reviewing user needs of assigned accounts in SQL stage
    - sending request for presentations to assigned accounts in PROSPECT stage
    - sending bids to assigned accounts in PITCHED stage
    - holds contract negotiation  to assigned accounts in BIDDED stage
    - checking inbox for messages from accounts, updating account stages
    """

    msgs = SalesRepMessages
    reject = SalesRejectionMessages
    intmsgs = InternalMessages

    msg2stages = {
        msgs.USER_NEED.value: AccountStage.PROSPECT,
        reject.USER_NEED.value: AccountStage.SQL,
        msgs.PRESENTATION.value: AccountStage.PITCHED,
        reject.PRESENTATION.value: AccountStage.PROSPECT,
        msgs.BID.value: AccountStage.BIDDED,
        reject.BID.value: AccountStage.PROSPECT,
        msgs.CONTRACT_NEGO.value: AccountStage.SIGNED,
        reject.CONTRACT_NEGO.value: AccountStage.SQL,
        OpsMessages.PROJECT_POSITIVE.value: AccountStage.ACTIVE,
        OpsMessages.PROJECT_NEGATIVE.value: AccountStage.STALE,
    }
    
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.uid = 'srep-' + str(uuid4())
        self.created = env.now
        self.inbox = simpy.Store(env)
        self.assigned_accounts = []
        self.wkly_review_needs = 10
        self.wkly_request_for_presentation = 10
        self.wkly_request_for_bid = 5
        self.wkly_negotiation = 5
        self.wkly_completion_handover = 5
        # Register processes
        self.env.process(self.review_user_need())
        self.env.process(self.meeting_request_for_presentation())
        self.env.process(self.bid_request())
        self.env.process(self.contract_negotiation())
        self.env.process(self.check_inbox())
        # Register this sales rep in the environment
        if hasattr(self.env, 'salesreps'): 
            self.env.salesreps.append(self)
        else:
            self.env.salesreps = [self]

    def get_accounts_per_stage(self):
        acct_per_stage = {k: [a for a in self.assigned_accounts if a.stage == k] for k in list(AccountStage)}
        return acct_per_stage

    def review_user_need(self):
        """Attempt to review user needs of assigned accounts in SQL stage

        Account will react or not, and will progress to PROSPECT accordingly
        """
        while True:
            sql = self.get_accounts_per_stage()[AccountStage.SQL]
            nb_sql = len(sql)
            self.log(f"sql: {nb_sql}, {[a.name for a in sql]}")
            targetted = random.sample(sql,min(nb_sql, self.wkly_review_needs))
            for account in targetted:
                msg = self.msgs.USER_NEED.value
                yield account.inbox.put(msg)
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=msg,
                    type_trans='External',
                    )
                self.log(f"Sent {msg} for {account.name} ({account.uid})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            print(time_to_next_week)
            yield self.env.timeout(time_to_next_week) 

    def meeting_request_for_presentation(self):
        """Send a request for presentation to accounts in PROSPECT stage
       
        Account will accept or not, and will progress to PITCHED accordingly
        """
        while True:
            accts = self.get_accounts_per_stage()[AccountStage.PROSPECT]
            nb_a = len(accts)
            self.log(f"accts: {nb_a}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_a, self.wkly_request_for_presentation))
            for account in targetted:
                msg = self.msgs.PRESENTATION.value
                yield account.inbox.put(msg)
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=msg,
                    type_trans='External',
                    )
                self.log(f"Sent {msg} for {account.name} ({account.uid})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def bid_request(self):
        """Send a bid to accounts in PITCHED stage

        Account will accept or not, and will progress to BIDDED accordingly
        """
        while True:
            accts = self.get_accounts_per_stage()[AccountStage.PITCHED]
            nb_a = len(accts)
            self.log(f"prospects: {nb_a}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_a, self.wkly_request_for_bid))
            for account in targetted:
                msg = self.msgs.BID.value
                yield account.inbox.put(msg)
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=msg,
                    type_trans='External',
                    )
                self.log(f"Sent {msg} for {account.name} ({account.uid})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def contract_negotiation(self):
        """Hold bid and contract negotiation request to accounts in BIDDED stage

        Account will award project or not, and will progress to SIGNED accordingly
        """
        while True:
            accts = self.get_accounts_per_stage()[AccountStage.BIDDED]
            nb_a = len(accts)
            self.log(f"prospects: {nb_a}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_a, self.wkly_request_for_bid))
            for account in targetted:
                msg = self.msgs.CONTRACT_NEGO.value
                yield account.inbox.put(msg)
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=msg,
                    type_trans='External',
                    )
                self.log(f"Sent {msg} for {account.name} ({account.uid})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def completion_signoff(self):
        """Hold review of the project implementation for project in the SIGNED stage

        Account will award project or not, and will progress to ACTIVE or STALE accordingly
        """
        while True:
            accts = self.get_accounts_per_stage()[AccountStage.SIGNED]
            nb_a = len(accts)
            self.log(f"prospects: {nb_a}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_a, self.wkly_completion_handover))
            for account in targetted:
                msg = OpsMessages.PROJECT_FEEDBACK.value
                yield account.inbox.put(msg)
                self.record_crm_transaction(
                    initiator_uid=self.uid, 
                    recipient_uid=account.uid, 
                    msg=msg,
                    type_trans='External',
                    )
                self.log(f"Sent {msg} for {account.name} ({account.uid})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def check_inbox(self):
        while True:
            # Receive confirmation from accounts
            msg = yield self.inbox.get()
            self.log(f"Received message: {msg}")
            uid, msg = msg.split('|||')
            self.record_crm_transaction(
                initiator_uid=uid, 
                recipient_uid=self.uid, 
                msg=msg,
                type_trans='External'
                )
            if msg in list(self.msg2stages.keys()):
                loa = [a for a in self.assigned_accounts if a.uid == uid]
                account = loa[0] if loa else None
                if account:
                    if msg in self.expected_messages(account.stage):
                        msg2send = getattr(self.intmsgs, f"{account.stage.name.upper()}2{self.msg2stages[msg].name}").name  # type: ignore
                        account.stage = self.msg2stages[msg]
                        self.record_crm_transaction(
                            initiator_uid=self.uid, 
                            recipient_uid=account.uid, 
                            msg=msg2send,
                            type_trans='Internal'
                            )
                        self.log(f"Converted {account.name} from {account.stage.name} to {self.msg2stages[msg].name} stage")

    def record_crm_transaction(self, initiator_uid, recipient_uid, msg, type_trans, **kwargs):
        """Record a transaction in the environment system."""
        record = {
            'timestamp': self.env.now,
            'initiator': initiator_uid,
            'recipient': recipient_uid,
            'message': msg,
            'type': type_trans
        }
        record.update(kwargs)
        if hasattr(self.env, 'crm_transactions'):
            self.env.crm_transactions.append(record)    # type: ignore
        else:
            self.env.crm_transactions = [record]  # type: ignore

    
    def expected_messages(self, stage):
        if stage == AccountStage.LEAD:
            return []
        elif stage == AccountStage.SQL:
            return [SalesRepMessages.USER_NEED.value]
        elif stage == AccountStage.PROSPECT:
            return [SalesRepMessages.PRESENTATION.value]
        elif stage == AccountStage.PITCHED:
            return [SalesRepMessages.BID.value]
        elif stage == AccountStage.BIDDED:
            return [SalesRepMessages.CONTRACT_NEGO.value]
        elif stage == AccountStage.SIGNED:
            return [OpsMessages.PROJECT_POSITIVE.value, OpsMessages.PROJECT_NEGATIVE.value]
        elif stage == AccountStage.ACTIVE:
            return self.expected_messages(AccountStage.SQL)
        else:
            return []
            
    def __repr__(self):
        return f"SalesRep(name={self.name} uid={self.uid})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the account."""
        # ['assigned_accounts', 'created', 'env', 'inbox', 'msg2stages', 'name', 'uid', 'wkly_review_needs']
        a2drop = ['env', 'inbox', 'msg2stages']
        a2keep = []
        attrs = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]
        aoi = set(attrs).difference(set(a2drop)).union(set(a2keep))
        return {a:getattr(self,a) for a in dir(self) if a in list(aoi)}

    def log(self, msg):
        print(f"[{self.env.now:.2f}] {self.name}: {msg}")


class Account:
    """simpy agent representing an Account

    controls following processes:
    - checking inbox for messages from MarketingDpt and SalesRep
    - sending confirmation messages to MarketingDpt and SalesRep
    """

    _counter_start = 0

    @classmethod
    def _counter(cls):
        cls._counter_start += 1
        return cls._counter_start

    @classmethod
    def reset_counter(cls):
        cls._counter_start = 0

    mktg_conversion_rates = {
        MarketingMessages.EMAIL_CAMPAIGN.value: 0.15,
        MarketingMessages.INDUSTRY_EVENT.value: 0.3,
        MarketingMessages.WEBSITE_CTA.value: 0.41 * 0.02
    }
    mktg_conversion_delays = {
        MarketingMessages.EMAIL_CAMPAIGN.value: .6, # one time step is one week
        MarketingMessages.INDUSTRY_EVENT.value: .6,
        MarketingMessages.WEBSITE_CTA.value: .2
    }
    sales_conversion_rates = {
        SalesRepMessages.USER_NEED.value: 0.9,
        SalesRepMessages.PRESENTATION.value: 0.6,
        SalesRepMessages.BID.value: 0.5,
        SalesRepMessages.CONTRACT_NEGO.value: 0.5,
    }
    sales_conversion_delays = {
        SalesRepMessages.USER_NEED.value: 1,
        SalesRepMessages.PRESENTATION.value: 4 * 1,
        SalesRepMessages.BID.value: 4 * 3,
        SalesRepMessages.CONTRACT_NEGO.value: 4 * 2,
    }
    ops_conversion_rates = {
        OpsMessages.PROJECT_FEEDBACK.value: 1,
        OpsMessages.PROJECT_POSITIVE.value: 0.95,
    }
    ops_conversion_delays = {
        OpsMessages.PROJECT_FEEDBACK.value: 6 * 4,
        OpsMessages.PROJECT_POSITIVE.value: 6 * 4
    }

    srmsg = SalesRepMessages
    srrej = SalesRejectionMessages
    
    def __init__(self, env, name, marketing, **kwargs):
        self.env = env
        self.name = name
        self.handle_kwargs(**kwargs)
        self.uid = f"acct-{uuid4()}"
        self.stage = AccountStage.MQL
        self.marketing:MarketingDpt = marketing
        self.assigned_salesrep:SalesRep|None = None
        self.inbox = simpy.Store(env)
        # Register processes
        self.env.process(self.check_inbox())
        # Register account
        if hasattr(self.env, 'accounts'): 
            self.env.accounts.append(self)
        else:
            self.env.accounts = [self]

        self.record_crm_transaction(
            initiator_uid=self.marketing.uid,
            recipient_uid=self.uid,
            msg=f"NewMQL",
            type_trans='Internal'
            )

    def handle_kwargs(self, **kwargs):
        """Handle keyword arguments for account creation."""
        self.country = kwargs.get("country", Country.EU)
        if isinstance(self.country, str):
            self.country = getattr(Country, self.country, Country.EU)
        self.industry = kwargs.get("industry", Industry.ConsumerGoods)
        if isinstance(self.industry, str):
            self.industry = getattr(Industry, self.industry, Industry.ConsumerGoods)
        self.account_type = kwargs.get("account_type", random.choice(list(AccountType)))
        self.lead_source = kwargs.get("lead_source", LeadSource.WEBSITE_CTA)

    def random_delay(self, event_name):
        low, high = 1,3
        return random.uniform(low, high)

    def decide(self, conversion_rates, key):
        return random.random() <= conversion_rates[key]

    def check_inbox(self):
        while True:
            msg = yield self.inbox.get()
            self.log(f"{self.name} received message: {msg}")
            if msg in list(self.mktg_conversion_rates.keys()):
                # self.log(f"Conversion rate: {self.mktg_conversion_rates[msg]}")
                if self.decide(self.mktg_conversion_rates, msg):                    
                    yield self.env.timeout(self.mktg_conversion_delays[msg])
                    self.log(f"Processing marketing message: {msg}")
                    self.marketing.inbox.put(f"{self.uid}|||{msg}")                    
            elif msg in list(self.sales_conversion_rates.keys()):
                # self.log(f"Conversion rate: {self.sales_conversion_rates[msg]}")
                if self.decide(self.sales_conversion_rates, msg):
                    # self.log(self.assigned_salesrep)
                    # mgs = getattr(self.reject,self.('user need review').name)
                    if self.assigned_salesrep:
                        yield self.env.timeout(self.sales_conversion_delays[msg])
                        self.log(f"Processing sales message: {msg}")
                        # self.log(f"{self.uid}|||{msg}")
                        self.assigned_salesrep.inbox.put(f"{self.uid}|||{msg}")
                    else:
                        raise RuntimeError(f"No sales rep assigned for {self.name}, cannot send message {msg}")
            elif msg in list(self.ops_conversion_rates.keys()):
                # self.log(f"Conversion rate: {self.ops_conversion_rates[msg]}")
                if self.decide(self.ops_conversion_rates, msg):
                    msg = OpsMessages.PROJECT_POSITIVE.value
                else:
                    msg = OpsMessages.PROJECT_NEGATIVE.value
                if self.assigned_salesrep:
                    yield self.env.timeout(self.ops_conversion_delays[msg])
                    self.log(f"Processing sales message: {msg}")
                    # self.log(f"{self.uid}|||{msg}")
                    self.assigned_salesrep.inbox.put(f"{self.uid}|||{msg}")
                else:
                    raise RuntimeError(f"No sales rep assigned for {self.name}, cannot send message {msg}")

    def log(self, msg):
        print(f"[{self.env.now:.2f}] {self.name}: {msg}")

    def __repr__(self):
        return f"Account(name={self.name} uid={self.uid})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the account."""
        a2drop = ['env', 'inbox', 'marketing', 'mktg_conversion_rates', 'mktg_conversion_delays',  'sales_conversion_delays', 'sales_conversion_rates']
        a2keep = ['assigned_salesrep']
        attrs = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]
        aoi = set(attrs).difference(set(a2drop)).union(set(a2keep))
        return {a:getattr(self,a) for a in dir(self) if a in list(aoi)}

    def record_crm_transaction(self, initiator_uid, recipient_uid, msg, type_trans, **kwargs):
        """Record a transaction in the environment system."""
        record = {
            'timestamp': self.env.now,
            'initiator': initiator_uid,
            'recipient': recipient_uid,
            'message': msg,
            'type': type_trans,
        }
        record.update(kwargs)
        if hasattr(self.env, 'crm_transactions'):
            self.env.crm_transactions.append(record)    # type: ignore
        else:
            self.env.crm_transactions = [record]  # type: ignore

def record_accounts_stats(env):
        """Record the number of accounts per stage in the environment."""
        while True:
            yield env.timeout(delay=1)
            record = {
                'timestamp': env.now,
                'nb_accounts': len(env.accounts),
                'LEAD': len([a for a in env.accounts if a.stage == AccountStage.LEAD]),
                'MQL': len([a for a in env.accounts if a.stage == AccountStage.MQL]),
                'SQL': len([a for a in env.accounts if a.stage == AccountStage.SQL]),
                'PROSPECT': len([a for a in env.accounts if a.stage == AccountStage.PROSPECT]),
                'PITCHED': len([a for a in env.accounts if a.stage == AccountStage.PITCHED]),
                'BIDDED': len([a for a in env.accounts if a.stage == AccountStage.BIDDED]),
                'SIGNED': len([a for a in env.accounts if a.stage == AccountStage.SIGNED]),
                'ACTIVE': len([a for a in env.accounts if a.stage == AccountStage.ACTIVE]),
                'STALE': len([a for a in env.accounts if a.stage == AccountStage.STALE]),
            }
            if hasattr(env, 'account_stats'):
                env.account_stats.append(record)
            else:
                env.account_stats = [record]  

def accounts_created_before(t, env):
    return [acc for acc in env.accounts if acc.created_at <= t]

def report_account_stages(env):
    print(f"\n--- Report at time {env.now} ---")
    for account in env.accounts:
        print(f"{account.name}: {account.stage.name} (created at {account.created_at})")
    print("-------------------------------\n")

# ... Account class and other functions ...

def periodic_reporter(env, interval):
    # First report at time 1
    yield env.timeout(1)
    report_account_stages(env)
    while True:
        yield env.timeout(interval)
        report_account_stages(env)

# Run simulation
def main():
    random.seed(1988)
    env = simpy.Environment()
    env.accounts = []   # List to hold all accounts # type: ignore
    initial_accounts = 5
    arrival_rate = 0.5  # on average, one new account every 2 units of time
    # env.process(account_arrival(env, initial_accounts, arrival_rate))
    env.run(until=20)

if __name__ == "__main__":
    main()