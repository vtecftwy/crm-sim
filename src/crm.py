import numpy as np
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import random
import seaborn as sns   
import simpy

from agents import MarketingDpt, SalesRep, Account, record_accounts_stats
from datetime import datetime, timedelta
from enums import AccountStage, AccountType, LeadSource
from utils import salesrep_name_generator, account_info_generator

from pathlib import Path
from uuid import uuid4

from agents import MarketingDpt, SalesRep, Account, record_accounts_stats
from enums import AccountStatus, AccountType, AccountStage, Country, Industry
from enums import LeadSource
from enums import MarketingMessages, SalesRepMessages
from utils import account_info_generator, salesrep_name_generator


class CustomerRelationManagerSimulator:
    def __init__(self, nb_salesreps=5, nb_mql_accounts=20, nb_sql_accounts=20):
        self.env = simpy.Environment()
        self.env.sales_reps = []  # type: ignore
        self.env.accounts = []   # type: ignore
        self.marketing = MarketingDpt(self.env)
        self.salesrep_name_gen = salesrep_name_generator()
        self.setup_salesreps(nb_salesreps)
        self.account_info_gen = account_info_generator()
        self.setup_accounts(nb_mql_accounts, nb_sql_accounts)

        self.env.process(self.new_mql_arrival(arrival_rate=0.25)) # MQL arrival rate
        self.env.process(record_accounts_stats(self.env))

    # Methods to setup the simulation
    def setup_salesreps(self, nb_salesreps):
        """Initialize sales reps."""
        if len(self.env.sales_reps) > 0: # type: ignore
            return
        else:
            for _ in range(nb_salesreps):
                salesrep = SalesRep(self.env, next(self.salesrep_name_gen))
                self.add_salesrep(salesrep)

    def setup_accounts(self, nb_mql_accounts, nb_sql_accounts, nb_others=15):
        """Initialize accounts."""
        nb_mql = int(nb_mql_accounts)
        nb_sql = int(nb_sql_accounts)
        nb_prospects = int(nb_others)
        nb_pitched = int(nb_others * .80)
        nb_bidded = int(nb_others * .66)
        nb_signed = int(nb_others * .35)
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
        print(f"Total accounts created: {len(self.env.accounts)}")  # type: ignore

    # Methods to manage accounts and sales reps
    def add_salesrep(self, salesrep):
        self.env.sales_reps.append(salesrep)  # type: ignore

    def add_account(self, stage, **kwargs):
        co_info = next(self.account_info_gen)
        sales_rep_loop = itertools.cycle(self.env.sales_reps) # type: ignore
        account = Account(
            self.env, 
            name=co_info['Company Name'],
            marketing=self.marketing,
            country=co_info['Country'],
            industry=co_info['Industry'],
            account_type=kwargs.get('account_type', random.choice(list(AccountType))),
            lead_source=kwargs.get('lead_source', random.choice(list(LeadSource))),
            )
        account.stage = stage
        if stage == AccountStage.SQL:
            account.assigned_salesrep = next(sales_rep_loop)
        # print(f"[{self.env.now:.2f}]: Account {account.name} added to CRM ({len(self.env.accounts)}).")

    # Processes
    def new_mql_arrival(self, arrival_rate):
        while True:
            delay = random.expovariate(arrival_rate)
            t = self.env.now + delay
            yield self.env.timeout(delay)
            self.add_account(stage=AccountStage.MQL)

    # Reporting and Plotting
    def convert_lists_to_df(self):
        salesrep_df = pd.DataFrame({sr.uid: sr() for sr in self.env.sales_reps})  # type: ignore
        return salesrep_df.T

    def get_crm_transactions(self):
        """Get CRM transactions as a DataFrame."""
        if hasattr(self.env, 'crm_transactions'):
            return pd.DataFrame(self.env.crm_transactions) # type: ignore
        else:
            print("No CRM transactions found. Returning empty dataframe")
            return pd.DataFrame(columns=['timestamp', 'initiator', 'recipient', 'message', 'type'])

    def get_account_stats(self):
        """Get account statistics as a DataFrame."""
        if hasattr(self.env, 'account_stats'):
            df = pd.DataFrame(self.env.account_stats).set_index('timestamp', drop=False).sort_index() # type: ignore

            d1 = datetime(year=2026, month=1, day=5, hour=0, minute=0, second=0)
            week = timedelta(weeks=1)
            df.index = df.loc[:, 'timestamp'].apply(lambda x: d1 + week * x) #type: ignore
            df_monthly = df.resample('ME').last().drop(columns=['timestamp'])
            return df_monthly
        else:
            print("No account stats found. Returning empty dataframe")
            return pd.DataFrame(columns=['LEAD', 'MQL', 'SQL', 'OPPORTUNITY', 'CLOSED_WON', 'CLOSED_LOST', 'STALE', 'nb_accounts'])

    def plot_account_stats(self, as_share=True, hide_mql=True, hide_mql_sql=True):
        """Plot account statistics."""
        if hide_mql_sql:
            df = self.get_account_stats().drop(columns=['LEAD', 'MQL', 'SQL', 'STALE', 'nb_accounts'])        
        elif hide_mql:
            df = self.get_account_stats().drop(columns=['LEAD','STALE', 'MQL', 'nb_accounts'])
        else:
            df = self.get_account_stats().drop(columns=['LEAD', 'STALE', 'nb_accounts'])

        if as_share: 
            df_pct = df.div(df.sum(axis=1), axis=0)  # Normalize to share
        else:
            df_pct = df.copy()

        # Use month start for index for better bar alignment
        df_pct.index = df_pct.index.to_period('M').to_timestamp('M')  # type: ignore

        # Calculate bar width as number of days in each month
        month_days = df_pct.index.days_in_month * 0.75  #type: ignore
        bar_widths = pd.to_timedelta(month_days, unit='D')

        # Prepare for stacking
        x = df_pct.index
        bottom = np.zeros(len(df_pct))
        colors = sns.color_palette("tab10", n_colors=len(df_pct.columns))

        plt.figure(figsize=(8,4))
        for i, col in enumerate(df_pct.columns):
            plt.bar(x, df_pct[col], width=bar_widths, bottom=bottom, label=col, color=colors[i])
            bottom += df_pct[col].values #type: ignore

        plt.xlabel("Timestamp")
        plt.ylabel("Share of Total")
        plt.title("Account Stages as Share of Total Over Time")
        plt.legend(title="Stage", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    # Helper for simulation
    def run(self, until=None):
        self.env.run(until=until)

    def step(self):
        """Run one step of the simulation."""
        self.env.step()

    def iterate(self):
        self.env.run(until=self.env.peek() + 1)


if __name__ == "__main__":
    # Example usage
    crm_simulator = CustomerRelationManagerSimulator(nb_salesreps=5, nb_mql_accounts=20, nb_sql_accounts=20)
    crm_simulator.run(until=100)  # Run the simulation for 100 time units
    crm_simulator.plot_account_stats(as_share=True)
    print(crm_simulator.get_crm_transactions())
    print(crm_simulator.convert_lists_to_df())