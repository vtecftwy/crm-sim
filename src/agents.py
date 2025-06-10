import json
import simpy
import random


from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Callable, Dict, List, Sequence, Tuple
from uuid import uuid4

from enum import Enum, auto
from enums import AccountStage, AccountType, Industry, Country, LeadSource
from enums import MktgIntents, SalesIntents, OpsIntents, Actions, BusinessValues, InternalMessages

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

class BaseAgent(ABC):
    """Base Agent class, used to create any other agent in the CRM simulation

    Provides the following functionalities:
    - inbox for receiving messages
    - message handling
    - handle processes based on intent in incoming messages.
    """

    _category = "baseagent" 
    
    def __init__(self, crm):
        self.crm = crm
        # Define aliases for convenience
        self.env = self.crm.env

        # call property method to check that category was defined the this class
        self.category 

        # Create agent standard attributes
        self.inbox = simpy.Store(self.env)

        # Register agent to collection crm.agents:dict
        self.crm.register_agent_to_crm(self, self.category)

        # Register all processes
        self.env.process(self.handle_inbox())
        # print(f"{self.category} registered process {self.handle_inbox.__name__}")

        self.register_processes()

        # Customise general crm log function
        self.log = partial(self.crm.log, env=self.env, agent=self)

        self.record_instance_creation()

    # Agent Standard Processes
    def handle_inbox(self):
        """Process: handle incoming messages and triger relevant further process"""
        while True:
            json_msg = yield self.inbox.get()
            self.log(f"Received message: {json_msg}")
            msg = json.loads(json_msg)
            intent = msg.get('intent', None)
            # self.log(f"Processing intent: {intent}")
            if intent:
                fn = self.process_map.get(intent, self.no_action)
                self.log(f"Handling intent: {intent} with process {fn.__name__} {fn} and {msg}")
                yield from fn(msg)


    def no_action(self, msg):
        # print(f"No_action called on {self.name}")
        yield self.env.timeout(0)
        # print(f"No action called on {self.name}")
            
    def register_processes(self):
        """Register all processes in the agent to the environment"""
        for p,kwargs in self.loprocesses:
            if kwargs: self.env.process(p(**kwargs))
            else: self.env.process(p())
            # print(f"{self.category} registered process: {p.__name__} with kwargs: {kwargs}")

    def record_instance_creation(self):
        self.crm.record_transaction(
            msg={
                'suid': self.crm.uid,
                'ruid': self.uid,
                'intent': f"new {self.category} instance",
                'action': 'create',
            },
            transaction_type='system',
        )
    
    @property
    def category(self):
        if self._category == "baseagent":
            raise NotImplementedError(f"Class attribute '_category' in {self.__class__.__name__} class must be defined to another value then 'baseagent'")
        return self._category
    
    # Properties to implement in practical classes
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent"""
        pass

    @property
    @abstractmethod
    def uid(self) -> str:
        """Unique identifier for the agent"""
        pass

    @property
    @abstractmethod
    def process_map(self) -> Dict[str, Callable]:
        """Map of "intent" to process functions"""
        pass
    
    @property
    @abstractmethod
    def loprocesses(self) -> Sequence[Tuple[Callable, Dict]]:
        """List of processes available in this agent

        each process is defined as a tuple of (function, kwargs)
        """
        pass


class MarketingDpt(BaseAgent):
    """Marketing Department Agent

    Outgoing processes:
    - sending email campaigns
    Incoming processes, triggered upon related message:
    - move accounts to MQL stage and assign SalesRep to the account
    """

    _category = 'marketing'
    
    def __init__(self, crm):
        """Initialize the Marketing Department Agent"""
        self._name:str = 'Marketing Dpt'
        self._uid:str = 'mktg-' + str(uuid4())

        # Define process parameters
        self._loprocesses = [
            (self.send_email_campaign, None)
            ]
        self._process_map = {
            MktgIntents.EMAIL_CAMPAIGN.value: self.process_email_campaign_replies,
        }
        self.marketing_parameters = {
            MktgIntents.EMAIL_CAMPAIGN.value: {
                'nb_targetted_accounts': 10, # Number of accounts to target in each campaign
                'nb_yearly_campaigns': 52 / 3,
            },
            MktgIntents.INDUSTRY_EVENT.value: {
                'nb_leads_per_event': 280, # Number of accounts to target in each event
                'industry_event_conversion_rate': 0.6,
                'nb_yearly_events': 12,
            }
        }

        super().__init__(crm)

    # Processes
    def process_email_campaign_replies(self, msg):
        """Analyse reply to email campain and takes appropriate action"""
        # self.log(f"Processing email campaign reply: {msg}")
        # Steps when action accounts is ACCEPT
        account = next((a for a in self.crm.agents['account'] if a.uid == msg['suid']), None)
        if account:
            if msg['action'] == Actions.ACCEPT.value:
                # Retrieve account from its suid
                # account = self.crm.agents['account'].get(msg['suid'])
                self.log(f"Transitioning {account.name} to SQL")
                account.transition(fr=AccountStage.MQL, to=AccountStage.SQL)
                self.crm.assign_salesrep(account)
            elif msg['action'] == Actions.REJECT.value:
                self.log(f"{account.name} rejected the email, no transition")
            
        yield self.env.timeout(0)
 
    def send_email_campaign(self):
        while True:
            targetted = self.pick_targetted_accounts()
            msg = {
                'suid': self.uid,
                'intent': MktgIntents.EMAIL_CAMPAIGN.value,
                'action': Actions.REQUEST.value,
            }
            for account in targetted:
                msg.update(ruid=account.uid)
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(msg, transaction_type='external')
            time_to_next_campaign = self.compute_time_to_next_campaign()
            self.log(f"Next campaign at {self.env.now + time_to_next_campaign:.2f}")
            yield self.env.timeout(time_to_next_campaign)

    # Utility functions
    def pick_targetted_accounts(self):
        nb_accts = self.marketing_parameters[MktgIntents.EMAIL_CAMPAIGN.value]['nb_targetted_accounts']
        mql = self.crm.get_accounts(stage=AccountStage.MQL)
        nb_mql = len(mql)
        # self.log(f"Found {nb_mql} MQL accounts")
        return random.sample(mql, min(nb_accts, nb_mql))

    def compute_time_to_next_campaign(self):
        """Compute the time in weeks to the next campaign"""
        n = self.marketing_parameters[MktgIntents.EMAIL_CAMPAIGN.value]['nb_yearly_campaigns']
        return int(52 / max(n, 1))

    @property
    def name(self) -> str: return self._name

    @property
    def uid(self) -> str: return self._uid

    @property
    def process_map(self) -> Dict[str, Callable]:
        """Map of "intent" to process functions"""
        return self._process_map

    @property
    def loprocesses(self) -> List[Tuple[Callable, Dict]]:
        """List of processes available in this agent

        each process is defined as a tuple of (function, kwargs)
        """
        return [(self.send_email_campaign, {})]


class SalesRep(BaseAgent):

    _category = 'salesrep'

    def __init__(self, crm, name):
        self._name = name
        self._uid = 'srep-' + str(uuid4())
        self.assigned_accounts = []

        # Define process parameters   
        self._process_map = {
            SalesIntents.USER_NEED.value: self.process_sales_request_replies,
            SalesIntents.PRESENTATION.value: self.process_sales_request_replies,
            SalesIntents.BID.value: self.process_sales_request_replies, 
            SalesIntents.NEGO.value: self.process_sales_request_replies,    
            OpsIntents.FEEDBACK_AT_COMPLETION.value: self.process_sales_request_replies,
        }
        self._loprocesses = [
            (self.request_user_need_discovery, None),
            (self.request_meeting_for_presentation, None),
            (self.request_invitation_to_bid, None), 
            (self.request_negotiation, None),
            (self.request_project_feedback, None),
        ]
        super().__init__(crm)

        self.wkly_review_needs = 2
        self.wkly_request_for_presentation = 2
        self.wkly_request_for_bid = 2
        self.wkly_request_for_nego = 2
        self.wkly_completion_handover = 2

    # Intent Handlers
    def request_user_need_discovery(self):
        """Attempt to review user needs of assigned accounts in SQL stage

        Account will react or not, and will progress to PROSPECT accordingly
        """
        while True:
            ref_stage = AccountStage.SQL
            # self.log(f"queue: {sorted([a.name for a in self.crm.requests_in_progress])}")
            # self.log(f"Entering 'request_user_need_discovery' for {self.wkly_review_needs} accounts")
            accts = [a for a in self.crm.accounts_per_stage(ref_stage) if a not in self.crm.requests_in_progress]
            nb_accts = len(accts)
            # self.log(f"{ref_stage.name}: {nb_accts}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_accts, self.wkly_review_needs))
            # queue targetted accounts to avoid sending them a new request before their reply
            self.crm.requests_in_progress.extend(targetted)
            self.log(f"Added to queue: {sorted([a.name for a in targetted])}")
            for account in targetted:
                msg = {
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': SalesIntents.USER_NEED.value,
                    'action': Actions.REQUEST.value,
                }
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(
                    msg=msg,
                    transaction_type='External',
                    )
                self.log(f"Sent to {account.name}: {msg})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def request_meeting_for_presentation(self):
        """Attempt to get a pitch presentation at PROSPECT and ACTIVE accounts"""
        while True:
            ref_stage = AccountStage.PROSPECT
            # self.log(f"Entering 'request_user_need_discovery' for {self.wkly_review_needs} accounts")
            accts = [a for a in self.crm.accounts_per_stage(ref_stage) if a not in self.crm.requests_in_progress]
            accts = accts + self.crm.accounts_per_stage(AccountStage.ACTIVE)
            nb_accts = len(accts)
            # self.log(f"{ref_stage.name}: {nb_accts}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_accts, self.wkly_request_for_presentation))
            # queue targetted accounts to avoid sending them a new request before their reply
            self.crm.requests_in_progress.extend(targetted)
            self.log(f"Added to queue: {sorted([a.name for a in targetted])}")
            for account in targetted:
                msg = {
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': SalesIntents.PRESENTATION.value,
                    'action': Actions.REQUEST.value,
                }
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(
                    msg=msg,
                    transaction_type='External',
                    )
                self.log(f"Sent to {account.name}: {msg})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 
                
    def request_invitation_to_bid(self):
        while True:
            ref_stage = AccountStage.PITCHED
            # self.log(f"Entering 'request_user_need_discovery' for {self.wkly_review_needs} accounts")
            accts = [a for a in self.crm.accounts_per_stage(ref_stage) if a not in self.crm.requests_in_progress]
            nb_accts = len(accts)
            # self.log(f"{ref_stage.name}: {nb_accts}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_accts, self.wkly_request_for_bid))
            # queue targetted accounts to avoid sending them a new request before their reply
            self.crm.requests_in_progress.extend(targetted)
            self.log(f"Added to queue: {sorted([a.name for a in targetted])}")
            for account in targetted:
                msg = {
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': SalesIntents.BID.value,
                    'action': Actions.REQUEST.value,
                }
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(
                    msg=msg,
                    transaction_type='External',
                    )
                self.log(f"Sent to {account.name}: {msg})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def request_negotiation(self):
        while True:
            ref_stage = AccountStage.BIDDED
            # self.log(f"Entering 'request_user_need_discovery' for {self.wkly_review_needs} accounts")
            accts = [a for a in self.crm.accounts_per_stage(ref_stage) if a not in self.crm.requests_in_progress]
            nb_accts = len(accts)
            # self.log(f"{ref_stage.name}: {nb_accts}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_accts, self.wkly_request_for_nego))
            # queue targetted accounts to avoid sending them a new request before their reply
            self.crm.requests_in_progress.extend(targetted)
            self.log(f"Added to queue: {sorted([a.name for a in targetted])}")
            for account in targetted:
                msg = {
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': SalesIntents.NEGO.value,
                    'action': Actions.REQUEST.value,
                }
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(
                    msg=msg,
                    transaction_type='External',
                    )
                self.log(f"Sent to {account.name}: {msg})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def request_project_feedback(self):
        while True:
            ref_stage = AccountStage.SIGNED
            # self.log(f"Entering 'request_user_need_discovery' for {self.wkly_review_needs} accounts")
            accts = [a for a in self.crm.accounts_per_stage(ref_stage) if a not in self.crm.requests_in_progress]
            nb_accts = len(accts)
            # self.log(f"{ref_stage.name}: {nb_accts}, {[a.name for a in accts]}")
            targetted = random.sample(accts,min(nb_accts, self.wkly_completion_handover))
            # queue targetted accounts to avoid sending them a new request before their reply
            self.crm.requests_in_progress.extend(targetted)
            self.log(f"Added to queue: {sorted([a.name for a in targetted])}")
            for account in targetted:
                msg = {
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': OpsIntents.FEEDBACK_AT_COMPLETION.value,
                    'action': Actions.REQUEST.value,
                }
                yield account.inbox.put(json.dumps(msg))
                self.crm.record_transaction(
                    msg=msg,
                    transaction_type='External',
                    )
                self.log(f"Sent to {account.name}: {msg})")
            time_to_next_week = self.env.now - int(self.env.now) + 1
            yield self.env.timeout(time_to_next_week) 

    def process_sales_request_replies(self, msg):
        """Analyse reply to sales request and takes appropriate further action"""
        self.log(f"Processing reply to {msg['intent']}: {msg}")
        # Steps when action accounts is ACCEPT
        action_mapping = {
            SalesIntents.USER_NEED.value: {
                Actions.ACCEPT.value: (AccountStage.SQL, AccountStage.PROSPECT),
                Actions.REJECT.value: (AccountStage.SQL, AccountStage.SQL),
            },
            SalesIntents.PRESENTATION.value: {
                Actions.ACCEPT.value: (AccountStage.PROSPECT, AccountStage.PITCHED),
                Actions.REJECT.value: (AccountStage.PROSPECT, AccountStage.SQL),
            },
            SalesIntents.BID.value: {
                Actions.ACCEPT.value: (AccountStage.PITCHED, AccountStage.BIDDED),
                Actions.REJECT.value: (AccountStage.PITCHED, AccountStage.SQL),
            },
            SalesIntents.NEGO.value: {
                Actions.ACCEPT.value: (AccountStage.BIDDED, AccountStage.SIGNED),
                Actions.REJECT.value: (AccountStage.BIDDED, AccountStage.SQL),
            },
            OpsIntents.FEEDBACK_AT_COMPLETION.value: {
                # Actions.POSITIVE.value: (AccountStage.SIGNED, AccountStage.ACTIVE),
                Actions.POSITIVE.value: (AccountStage.SIGNED, AccountStage.PROSPECT),
                Actions.NEGATIVE.value: (AccountStage.SIGNED, AccountStage.STALE),
            }
        }

        account = next((a for a in self.crm.agents['account'] if a.uid == msg['suid']), None)
        if account:
            intent, action = msg['intent'], msg['action']
            fr,to = action_mapping[intent][action]
            self.log(f"Transitioning {account.name} from {fr.name} to {to.name}")
            account.transition(fr=fr, to=to)
            self.crm.record_transaction(
                msg={
                    'suid': self.uid,
                    'ruid': account.uid,
                    'intent': f"{fr.name} to {to.name}",
                    'action': 'transition',
                },
                transaction_type='internal',
            )
            self.crm.requests_in_progress.remove(account)
            self.log(f"Removed {account.name} from queue, remaining: {sorted([a.name for a in self.crm.requests_in_progress])}")

        yield self.env.timeout(0)

    @property
    def name(self) -> str: return self._name

    @property
    def uid(self) -> str: return self._uid

    @property
    def process_map(self) -> Dict[str, Callable]: return self._process_map

    @property
    def loprocesses(self) -> List[Tuple[Callable, Dict]]: return self._loprocesses # type: ignore

    def __repr__(self):
        return f"SaleRep(name={self.name} uid={self.uid})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the sales rep."""
        # a2drop = ['crm', 'env', 'inbox', 'marketing','category', 'assigned_salesrep', 'sales_conversion_rates', 'mktg_conversion_rates', 'account_parameters', 'loprocesses',  'ops_conversion_delays', 'process_map', 'sales_conversion_delays', 'mktg_conversion_delays', 'ops_conversion_rates']
        a2drop = ['crm', 'env', 'inbox', 'marketing','category','process_map', 'wkly_completion_handover', 'wkly_request_for_nego', 'wkly_request_for_presentation', 'loprocesses', 'assigned_accounts','wkly_review_needs', 'wkly_request_for_bid']
        a2keep = []
        attrs = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]
        aoi = set(attrs).difference(set(a2drop)).union(set(a2keep))
        # print(aoi)
        return {a:getattr(self,a) for a in dir(self) if a in list(aoi)}


class Account(BaseAgent):
    """Account Agent

    Outgoing processes:
    - handle sales rep requests
    - handle email campaign replies
    """

    _category = 'account'

    mktg_conversion_rates = {
        MktgIntents.EMAIL_CAMPAIGN.value: 0.15, # mql2sql=0.15
        MktgIntents.INDUSTRY_EVENT.value: 0.3,  # 0.3
    }
    mktg_conversion_delays = {
        MktgIntents.EMAIL_CAMPAIGN.value: .9,   # one time step is one week
        MktgIntents.INDUSTRY_EVENT.value: .9,
    }
    sales_conversion_rates = {
        SalesIntents.USER_NEED.value: 0.8,      # sql2prospect=0.7
        SalesIntents.PRESENTATION.value: 0.6,   # prospect2prez=0.7
        SalesIntents.BID.value: 0.6,            # prez2bid=0.6
        SalesIntents.NEGO.value: 0.5 ,          # bid2close=0.3
    }
    sales_conversion_delays = {
        SalesIntents.USER_NEED.value: 0.3,      # conversation withing the week
        SalesIntents.PRESENTATION.value: 2,     # 2 weeks before presentation
        SalesIntents.BID.value: 0.3,            # 4 weeks before bid requested and submitted
        SalesIntents.NEGO.value: 0.3,           # 6 weeks before contract signed or lost
    }
    ops_conversion_rates = {
        OpsIntents.FEEDBACK_AT_COMPLETION.value: 0.95, # 5% not satisfied and will not buy again
    }
    ops_conversion_delays = {
        OpsIntents.FEEDBACK_AT_COMPLETION.value: 4 * 2, # 2 months for implementation
    }

    opportunity_sizes = {
        AccountType.SMALL: (10_000,50_000),
        AccountType.MEDIUM: (50_000,250_000),
        AccountType.LARGE: (250_000,1_000_000),
    }
    

    def __init__(self, crm, name, marketing, **kwargs):
        """Initialize the Account Agent"""
        self._name = name
        self._uid = f"acct-{uuid4()}"
        self.store_kwargs(**kwargs)
        self.stage = AccountStage.MQL
        self.marketing:MarketingDpt = marketing
        self.assigned_salesrep:SalesRep|None = None
        self.nb_opportunities = 0
        self.cumulative_opportunity_value = 0
        self.active_opportunity = 0
        self.nb_purchases = 0
        self.cumulative_purchase_value = 0
        self.active_purchase = 0

        # Define process parameters        
        self._loprocesses = []
        self.account_parameters = {}
        self._process_map = {
            MktgIntents.EMAIL_CAMPAIGN.value: self.reply_to_email_campaign,
            SalesIntents.USER_NEED.value: self.reply_to_salesrep_request,
            SalesIntents.PRESENTATION.value: self.reply_to_salesrep_request,
            SalesIntents.BID.value: self.reply_to_salesrep_request,
            SalesIntents.NEGO.value: self.reply_to_salesrep_request, 
            OpsIntents.FEEDBACK_AT_COMPLETION.value: self.reply_to_ops_request,
        }

        super().__init__(crm)

    def reply_to_email_campaign(self, msg):
        """Reply with an 'accept' or 'deny' action to the email campaign message"""
        # self.log(f"Entering in 'reply_to_email_campaign' with {msg}")
        if msg['action'] == Actions.REQUEST.value:
            # Make decision whether to accept of deny
            convrate = self.mktg_conversion_rates[MktgIntents.EMAIL_CAMPAIGN.value]
            # self.log(f"Conversion Rate of {convrate}")
            if random.random() <= convrate:
                action = Actions.ACCEPT.value
            else:
                action = Actions.REJECT.value
            # Build reply message
            reply_msg = {
                'suid': self.uid,
                'ruid': msg['suid'],
                'intent': MktgIntents.EMAIL_CAMPAIGN.value,
                'action': action,
            }
            # Define the delay to reply
            delay = self.mktg_conversion_delays[MktgIntents.EMAIL_CAMPAIGN.value]
            self.log(f"Will reply to email at {self.env.now + delay:.2f} ({delay} weeks)")
            yield self.env.timeout(delay)
            # Send reply to marketing inbox
            yield self.marketing.inbox.put(json.dumps(reply_msg))
            self.crm.record_transaction(
                msg=reply_msg,
                transaction_type='external',
            )
            self.log(f"Replied to email campaign with {reply_msg}")
        else:
            yield self.env.timeout(0)

    def conversion_rate_factor(self, msg):
        factor_country = {
            Country.EU: 1,
            Country.US: 0.75,
            Country.CN: 0.66,
        }
        factor_industry = {
            Industry.FoodnBeverage: 1,
            Industry.ConsumerGoods: 1,
            Industry.Chemicals: 0.75,
            Industry.Pharmaceuticals: 0.75
        }
        factor_type = {
            AccountType.SMALL: 0.50,
            AccountType.MEDIUM: 1.0,
            AccountType.LARGE: 1.0
        }

        if msg['intent'] == SalesIntents.USER_NEED.value:
            return factor_country.get(self.country, 1)
        elif msg['intent'] == SalesIntents.PRESENTATION.value:
            return factor_country.get(self.country, 1)
        elif msg['intent'] == SalesIntents.BID.value:
            return  factor_industry.get(self.industry, 1)
        elif msg['intent'] == SalesIntents.NEGO.value:
            return  factor_type.get(self.account_type,1)
        elif msg['intent'] == OpsIntents.FEEDBACK_AT_COMPLETION.value:
            return  factor_country.get(self.country, 1)
        else:
            return 1

    def reply_to_salesrep_request(self, msg):
        self.log(f"Received sales rep request: {msg}")
        if msg['action'] == Actions.REQUEST.value:
            convrate = self.sales_conversion_rates.get(msg['intent'], 0)
            factor =  self.conversion_rate_factor(msg)
            self.log(f"{convrate} {factor}")
            convrate = min(convrate * factor, 1)
            if random.random() <= convrate:
                reply_msg = {'suid': self.uid, 'ruid': msg['suid'], 'intent': msg['intent'], 'action': Actions.ACCEPT.value}
                if msg['intent'] in [SalesIntents.BID.value, SalesIntents.NEGO.value]:
                    self.update_business_value(msg)
            else:
                reply_msg = {'suid': self.uid, 'ruid': msg['suid'], 'intent': msg['intent'], 'action': Actions.REJECT.value}

            # Define the delay to reply
            delay = self.sales_conversion_delays.get(msg['intent'], 0.0)
            self.log(f"Will reply to email at {self.env.now + delay:.2f} ({delay} weeks)")
            yield self.env.timeout(delay)

            # Send reply to SalesRep inbox
            srep = next(sr for sr in self.crm.agents['salesrep'] if sr.uid == msg['suid'])
            yield srep.inbox.put(json.dumps(reply_msg))
            self.crm.record_transaction(
                msg=reply_msg,
                transaction_type='external',
            )
            self.log(f"Replied to {msg['intent']} with {reply_msg}")
        yield self.env.timeout(0)

    def reply_to_ops_request(self, msg):
        self.log(f"Received operation request: {msg}")
        if msg['action'] == Actions.REQUEST.value:
            convrate = self.ops_conversion_rates.get(msg['intent'], 0)
            # self.log(f"{convrate}")
            if random.random() <= convrate:
                reply_msg = {'suid': self.uid, 'ruid': msg['suid'], 'intent': msg['intent'], 'action': Actions.POSITIVE.value}
            else:
                reply_msg = {'suid': self.uid, 'ruid': msg['suid'], 'intent': msg['intent'], 'action': Actions.NEGATIVE.value}

            # Define the delay to reply
            delay = self.ops_conversion_delays.get(msg['intent'], 0.0)
            self.log(f"Will reply to email at {self.env.now + delay:.2f} ({delay} weeks)")
            yield self.env.timeout(delay)

            # Send reply to SalesRep inbox
            srep = next(sr for sr in self.crm.agents['salesrep'] if sr.uid == msg['suid'])
            yield srep.inbox.put(json.dumps(reply_msg))
            self.crm.record_transaction(
                msg=reply_msg,
                transaction_type='external',
            )
            self.log(f"Replied to {msg['intent']} with {reply_msg}")
        yield self.env.timeout(0)

    def transition(self, fr:AccountStage, to:AccountStage):
        """Transition the account from one stage to another"""
        if self.stage == fr:
            self.log(f"Transitioning from {fr.name} to {to.name}")
            self.stage = to
            self.crm.record_transaction(
                msg={
                    'suid': self.crm.uid,
                    'ruid': self.uid,
                    'intent': f"{fr.name} to {to.name}",
                    'action': 'transition',
                },
                transaction_type='system',
            )
        else:
            err = f"{self.name} cannot transition from {self.stage} to {to}, expected {fr}"
            err = err + f"\n{self.stage} {self.uid}"
            raise ValueError(err)

    def update_business_value(self, msg):
            # Add opportunity value
            self.log(f"Entering add_business_value: {msg['intent']}|{SalesIntents.BID.value}|{SalesIntents.NEGO.value}")
            self.log(f"Current business values: {self.cumulative_opportunity_value:,d} {self.cumulative_purchase_value:,d}")
            if msg['intent'] == SalesIntents.BID.value:
                val_min, val_max = self.opportunity_sizes[self.account_type]
                val = int(random.uniform(val_min, val_max)/1000)*1000
                self.active_opportunity = val
                self.cumulative_opportunity_value += val
                self.nb_opportunities += 1
                self.log(f"New opportunity value of {val:,d} of {self.nb_opportunities} adding to {self.cumulative_opportunity_value:,d}")
                self.crm.record_transaction(
                    msg={
                        'suid': self.uid,
                        'ruid': self.assigned_salesrep.uid,
                        'intent': BusinessValues.OPPORTUNITY.value,
                        'action': Actions.FORECAST.value
                    },
                    transaction_type='external',
                    value=self.active_opportunity,
                )
            elif msg['intent'] == SalesIntents.NEGO.value:
                self.log(f"Set purchase value to {self.active_opportunity:,d}")
                self.active_purchase = self.active_opportunity
                self.cumulative_purchase_value += self.active_purchase
                self.active_opportunity = 0
                self.crm.record_transaction(
                    msg={
                        'suid': self.uid,
                        'ruid': self.assigned_salesrep.uid,
                        'intent': BusinessValues.PURCHASE.value,
                        'action': Actions.PURCHASE.value
                    },
                    transaction_type='external',
                    value=self.active_purchase,
                )
                    
    def store_kwargs(self, **kwargs):
        """Store keyword arguments for account creation."""
        self.country = kwargs.get("country", Country.EU)
        if isinstance(self.country, str):
            self.country = getattr(Country, self.country, Country.EU)
        self.industry = kwargs.get("industry", Industry.ConsumerGoods)
        if isinstance(self.industry, str):
            self.industry = getattr(Industry, self.industry, Industry.ConsumerGoods)
        self.account_type = kwargs.get("account_type", random.choice(list(AccountType)))
        self.lead_source = kwargs.get("lead_source", LeadSource.WEBSITE_CTA)

    def __repr__(self):
        return f"Account(name={self.name} uid={self.uid})"

    def __call__(self) -> dict:
        """Return a dictionary representation of the account."""
        a2drop = ['crm', 'env', 'inbox', 'marketing','category', 'assigned_salesrep', 'sales_conversion_rates']
        a2drop.extend(['mktg_conversion_rates', 'account_parameters', 'loprocesses',  'ops_conversion_delays'])
        a2drop.extend(['process_map', 'sales_conversion_delays', 'mktg_conversion_delays', 'ops_conversion_rates'])
        a2drop.extend(['active_opportunity', 'active_purchase', 'cumulative_opportunities', 'cumulative_purchases','opportunity_sizes'])
        a2keep = ['assigned_salesrep']
        attrs = [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]
        aoi = set(attrs).difference(set(a2drop)).union(set(a2keep))
        return {a:getattr(self,a) for a in dir(self) if a in list(aoi)}

    @property
    def name(self) -> str: return self._name

    @property
    def uid(self) -> str: return self._uid

    @property
    def loprocesses(self): return self._loprocesses

    @property
    def process_map(self): return self._process_map



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

if __name__ == "__main__":
    pass