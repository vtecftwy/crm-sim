import numpy as np
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import random
import seaborn as sns   
import simpy

from eccore.core import setup_logging, logthis
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import uuid4

from agents import BaseAgent, MarketingDpt, SalesRep, Account
from datetime import datetime, timedelta
from enums import AccountStatus, AccountType, AccountStage, Country, Industry, LeadSource
from enums import MktgIntents, SalesIntents, Actions
from utils import salesrep_name_generator, account_info_generator


class CustomerRelationManagerSimulator:

    def __init__(self,nb_salesreps=5, nb_mql=20, nb_sql=20, nb_others=15):
        self.name = 'CRMSim'
        self.uid = 'crm-' + str(uuid4())
        self.env = simpy.Environment()
        self.time_step_unit = 'Week'
        self.agents:Dict[str, List[Account|SalesRep|MarketingDpt]] = {} # List of Agents, dict with key as agent types and value as lists
        self.requests_in_progress = [] # queue where accounts with pending request are stored

        self.transactions = []

        self.marketing = MarketingDpt(self)
        self.salesrep_name_gen = salesrep_name_generator() # initialise salesrep name generator
        self.setup_salesreps(nb_salesreps)
        self.account_info_gen = account_info_generator()
        self.setup_accounts(nb_mql, nb_sql, nb_others)

        
        self.loprocesses = [] # List of all processes at the top level in the CRM
        self.register_processes()
        self.env.process(self.record_accounts_stats())  # Positionel last to ensure it is the last action


    # =============================================================================
    # Methods to setup the simulation
    # =============================================================================
    def setup_salesreps(self, nb_salesreps):
        """Initialize sales reps."""

        salesreps = self.agents.get('salesrep', [])
        if len(salesreps) > 0:
            return
        else:
            for _ in range(nb_salesreps):
                SalesRep(crm=self, name=next(self.salesrep_name_gen))
                
    def setup_accounts(self, nb_mql, nb_sql, nb_others=15):
        """Initialize accounts."""
        nb_mql, nb_sql = int(nb_mql), int(nb_sql)
        nb_prospects, nb_pitched, nb_bidded, nb_signed = int(nb_others),int(nb_others*.80),int(nb_others*.66),int(nb_others*.35)
        if nb_mql > 0:
            for i,_ in enumerate(range(nb_mql)):
                self.add_account(stage=AccountStage.MQL)
            print(f"Created {nb_mql} MQL accounts")
        if nb_sql > 0:
            for i,_ in enumerate(range(nb_sql)):
                self.add_account(stage=AccountStage.SQL)
            print(f"Created {nb_sql} SQL accounts")            
        if nb_prospects > 0:
            for i,_ in enumerate(range(nb_prospects)):
                self.add_account(stage=AccountStage.PROSPECT)
            print(f"Created {nb_prospects} PROSPECT accounts")
        if nb_pitched > 0:
            for i,_ in enumerate(range(nb_pitched)):
                self.add_account(stage=AccountStage.PITCHED)
            print(f"Created {nb_pitched} PITCHED accounts")
        if nb_bidded > 0:
            for i,_ in enumerate(range(nb_bidded)):
                self.add_account(stage=AccountStage.BIDDED)
            print(f"Created {nb_bidded} BIDDED accounts")
        if nb_signed > 0:
            for i,_ in enumerate(range(nb_signed)):
                self.add_account(stage=AccountStage.SIGNED)
            print(f"Created {nb_signed} SIGNED accounts")
        print(f"Total accounts created: {len(self.get_accounts())}")  # type: ignore

    def add_account(self, stage, **kwargs):
        co_info = next(self.account_info_gen)
        sales_rep_loop = itertools.cycle(self.get_salesreps())
        account = Account(
            crm=self, 
            name=co_info['Company Name'],
            marketing=self.marketing,
            country=co_info['Country'],
            industry=co_info['Industry'],
            account_type=kwargs.get('account_type', random.choice(list(AccountType))),
            lead_source=kwargs.get('lead_source', random.choice(list(LeadSource))),
            )
        account.stage = stage
        if stage != AccountStage.LEAD:
            account.assigned_salesrep = next(sales_rep_loop)
        # self.log(self.env, self, f"Account {account.name} added to CRM (total of {len(self.get_accounts())} accounts).")

    # =============================================================================
    # CRM related methods
    # =============================================================================
    def get_accounts(self, stage:Optional[AccountStage]=None) -> List[Account]:
        if stage is None:
            return [a for a in self.agents.get('account', [])] # type: ignore
        else:
            return [acct for acct in self.agents.get('account', []) if acct.stage == stage] # type: ignore

    def get_salesreps(self) -> List[SalesRep]:
        return self.agents.get('salesrep', []) # type: ignore

    def assign_salesrep(self, account:Account):
        """Assign a sales rep to an account."""
        salesreps = self.get_salesreps()
        if not salesreps:
            raise ValueError("No sales reps available to assign.")
        # Assign the first available sales rep
        selected_salerep = sorted(salesreps, key=lambda sr: len(sr.assigned_accounts))[0]
        account.assigned_salesrep = selected_salerep
        self.log(f"Assigned sales rep {selected_salerep.name} to account {account.name}", selected_salerep, self.env)
        self.record_transaction(
            msg={
                'suid': selected_salerep.uid,
                'ruid': account.uid,
                'intent': 'assign sales rep',
                'action': 'assign',
            },
            transaction_type='system',
        )

    def register_agent_to_crm(self, agent, category): 
        """Adds this agent to the collection stored in crm"""
        self.agents.setdefault(category, []).append(agent)

    # =============================================================================
    # CRM reporting methods
    # =============================================================================
    def record_transaction(self, msg, transaction_type, **kwargs):
        """Record a transaction in the environment system."""
        record = {
            'timestamp': self.env.now,
            'sender': msg['suid'],
            'reviever': msg['ruid'],
            'intent': msg['intent'],
            'action': msg.get('action', None),
            'type': transaction_type,
        }
        record.update(kwargs)
        if hasattr(self, 'transactions'):
            self.transactions.append(record)    
        else:
            self.transactions = [record]  

    def record_accounts_stats(self):
        """Record the number of accounts per stage in the environment."""
        while True:
            yield self.env.timeout(delay=1)
            record = {
                'timestamp': self.env.now,
                'nb_accounts': len(self.agents['account']),
                'LEAD': len([a for a in self.agents['account'] if a.stage == AccountStage.LEAD]), # type: ignore
                'MQL': len([a for a in self.agents['account'] if a.stage == AccountStage.MQL]), # type: ignore
                'SQL': len([a for a in self.agents['account'] if a.stage == AccountStage.SQL]), # type: ignore
                'PROSPECT': len([a for a in self.agents['account'] if a.stage == AccountStage.PROSPECT]), # type: ignore
                'PITCHED': len([a for a in self.agents['account'] if a.stage == AccountStage.PITCHED]), # type: ignore
                'BIDDED': len([a for a in self.agents['account'] if a.stage == AccountStage.BIDDED]), # type: ignore
                'SIGNED': len([a for a in self.agents['account'] if a.stage == AccountStage.SIGNED]), # type: ignore
                'ACTIVE': len([a for a in self.agents['account'] if a.stage == AccountStage.ACTIVE]), # type: ignore
                'STALE': len([a for a in self.agents['account'] if a.stage == AccountStage.STALE]), # type: ignore
            }
            if hasattr(self, 'account_stats'):
                getattr(self, 'account_stats').append(record)
            else:
                self.account_stats = [record]

    def transactions_to_df(self, day1:datetime=datetime(2026, 1, 1)) -> pd.DataFrame:
        """Convert transactions to a pandas DataFrame"""
        if hasattr(self, 'transactions'):
            df = pd.DataFrame(self.transactions)
            d1 = day1 + timedelta(days= 7 - day1.weekday())  # Align to the first Monday
            df['timestamp'] = df['timestamp'].apply(lambda x: d1 + timedelta(weeks=x))
            return df.set_index('timestamp', drop=True).sort_index()
        else:
            return pd.DataFrame(columns=['timestamp', 'sender', 'receiver', 'intent', 'action', 'type'])

    def account_stats_to_df(self, day1:datetime=datetime(2026, 1, 1), int_idx=False) -> pd.DataFrame:
        """Convert account stats to a pandas DataFrame"""
        if hasattr(self, 'account_stats'):
            df = pd.DataFrame(self.account_stats)
            if not int_idx:
                d1 = day1 + timedelta(days= 7 - day1.weekday())  # Align to the first Monday
                df['timestamp'] = df['timestamp'].apply(lambda x: d1 + timedelta(weeks=x))
                df = df.set_index('timestamp', drop=True).sort_index()
            return df
        else:
            return pd.DataFrame(columns=['sender', 'receiver', 'intent', 'action', 'type'])

    def accounts_per_stage(self, stage: AccountStage) -> List[Account]:
        accounts = self.agents['account']
        l = [a for a in  accounts if a.stage == stage] #type: ignore
        return l #type:ignore
    # =============================================================================
    # Process related methods
    # =============================================================================
    def register_processes(self):
        for p,kwargs in self.loprocesses:
            self.env.process(p(**kwargs))

    # =============================================================================
    # Simulation related methods
    # =============================================================================
    def run(self, until: int):
        """Run the simulation until a specified time

        Args:
            until (int): The time until which the simulation should run
        """
        self.env.run(until=until)

    def step(self):
        """Step the simulation until a specified time"""
        self.env.step()

    def iterate(self) -> None:
        """Perform one time step iteration"""
        self.env.run(self.env.peek() + 1)

    @staticmethod
    def log(txt, agent, env):
        # print(f"[{env.now:.2f}]-[{agent.name}] {txt}")
        logthis(f"[{env.now:.2f}]-[{agent.name}] {txt}")



if __name__ == "__main__":
    # Example usage
    pass