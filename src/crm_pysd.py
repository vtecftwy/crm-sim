import pandas as pd
import random
import simpy

from classes import SalesRep, Account, Opportunity
from enums import AccountStage, AccountType, LeadSource
from utils import salesrep_name_generator, account_info_generator



class CustomerRelationManagerSimulator:
    def __init__(self, nb_salesreps=3, nb_accounts=5):
        self.env = simpy.Environment()
        self.sales_reps = {}
        self.salesrep_name_gen = salesrep_name_generator()
        self.setup_salesreps(nb_salesreps)
        self.accounts = {}
        self.account_info_gen = account_info_generator()
        self.setup_accounts(nb_accounts)
        self.opportunities = {}

    # Methods to setup the simulation
    def setup_salesreps(self, nb_salesreps):
        """Initialize sales reps."""
        if len(self.sales_reps) > 0: 
            return
        else:
            for _ in range(nb_salesreps):
                salesrep = SalesRep(self.env, next(self.salesrep_name_gen))
                self.add_salesrep(salesrep)

    def setup_accounts(self, nb_accounts, account_type=None, lead_source=None):
        """Initialize accounts."""
        nb_accounts = int(nb_accounts)
        if nb_accounts == 0: return
        if account_type is None:
            account_type = random.choice(list(AccountType))
        lead_source = LeadSource.WEBSITE_CTA if lead_source is None else lead_source
        
        for _ in range(nb_accounts):
            co_info = next(self.account_info_gen) 
            account = Account(
                self.env, 
                name=co_info['Company Name'],
                country=co_info['Country'],
                industry=co_info['Industry'],
                account_type=account_type,
                lead_source=lead_source,
                )
            self.add_account(account)
            self.assign_random_salesrep(account)

    # Methods to manage accounts and sales reps
    def add_account(self, account):
        self.accounts[account.uid] = account
        # print(f"{self.env.now}: Account {account.name} added to CRM.")

    def add_salesrep(self, salesrep):
        self.sales_reps[salesrep.uid] = salesrep
        # print(f"{self.env.now}: Sales Rep {salesrep.name} added to CRM.")

    def assign_salesrep(self, account, salesrep):
        self.accounts[account.uid].set_sales_rep(salesrep)

    def assign_random_salesrep(self, account):
        """Assign a random sales rep to the account."""
        salesrep_keys = list(self.sales_reps.keys())
        key = random.choice(salesrep_keys)
        self.assign_salesrep(account, self.sales_reps[key])

    # Methods to manage opportunities
    def add_opportunities(self, idxs):
        pass

    def add_opportunity(self,account):
        pass

    # Methods to update accounts with SD Simulation
    def get_uids_per_stage(self):
        """Create indexes of account UID per stage"""
        acct_uid_per_stage = {}
        df = self.retrieve_accounts()
        for stage in list(AccountStage):
            # print(df.loc[df['stage'] == stage, :]['uid'].tolist())
            acct_uid_per_stage[stage] = df[df['stage'] == stage]['uid'].tolist()
        return acct_uid_per_stage

    def _create_new_accounts(self, row):
        website, campaign, events, salesreps  = row.loc[['mql website', 'mql online campaign', 'mql industry events', 'mql salesreps']]
        # print(website, campaign,events, salesreps)

        self.setup_accounts(
            nb_accounts=website,
            lead_source=LeadSource.WEBSITE_CTA,
        )
        self.setup_accounts(
            nb_accounts=campaign,
            lead_source=LeadSource.EMAIL_CAMPAIGN,
        )
        self.setup_accounts(
            nb_accounts=events,
            lead_source=LeadSource.INDUSTRY_EVENT,
        )
        self.setup_accounts(
            nb_accounts=salesreps,
            lead_source=LeadSource.SALES_REP,
    )

    def _remove_decayed_accounts(self, row):
        uids_per_stage = self.get_uids_per_stage()
        n_mql, n_sql, n_prospect = row.loc[['mql decay', 'sql decay', 'prospect decay']].astype(int)
        mql_idx = random.sample(uids_per_stage[AccountStage.MQL], n_mql)
        sql_idx = random.sample(uids_per_stage[AccountStage.SQL], n_sql)
        prospect_idx = random.sample(uids_per_stage[AccountStage.PROSPECT], n_prospect)
        # print(mql_idx, sql_idx, prospect_idx)
        for idx in mql_idx + sql_idx + prospect_idx:
            del self.accounts[idx]

    def _shift_accounts(self, row):
        """Shift accounts between stages"""
        def move_accounts(idxs, stage):
            for idx in idxs:
                self.accounts[idx].stage = stage

        flows = [
            'sales qualified', 'new prospects', 'presentations', 'bids', 'contracts', 
            'satisfied', 'unsatisfied', 'completed',
            'stale prospects', 'lost bids'
            ]
        sq, np, prez, bids, c, sta, unsat, comp, stalep, lost = row.loc[flows].astype(int)
        # print(sq, np, prez, bids, c, sta, unsat, stalep, lost)


        uids_per_stage = self.get_uids_per_stage()
            
        idxs = random.sample(uids_per_stage[AccountStage.MQL], sq)
        move_accounts(idxs, AccountStage.SQL)
        
        idxs = random.sample(uids_per_stage[AccountStage.SQL], np)
        move_accounts(idxs, AccountStage.PROSPECT)
        
        idxs = random.sample(uids_per_stage[AccountStage.PROSPECT], prez)
        move_accounts(idxs, AccountStage.PITCHED)
        
        idxs = random.sample(uids_per_stage[AccountStage.PITCHED], bids)
        move_accounts(idxs, AccountStage.BIDDED)
        self.add_opportunities(idxs)

        idxs = random.sample(uids_per_stage[AccountStage.BIDDED], c)
        move_accounts(idxs, AccountStage.SIGNED)
        
        idxs = random.sample(uids_per_stage[AccountStage.SIGNED], sta)
        move_accounts(idxs, AccountStage.ACTIVE)
        
        idxs = random.sample(uids_per_stage[AccountStage.ACTIVE], unsat)
        move_accounts(idxs, AccountStage.STALE)

        uids_per_stage = self.get_uids_per_stage()

        idxs = random.sample(uids_per_stage[AccountStage.PITCHED], stalep)
        move_accounts(idxs, AccountStage.SQL)

        idxs = random.sample(uids_per_stage[AccountStage.BIDDED], lost)
        move_accounts(idxs, AccountStage.SQL)
        
        idxs = random.sample(uids_per_stage[AccountStage.ACTIVE], comp)
        move_accounts(idxs, AccountStage.SQL)

    def update_accounts(self, df, verbose=False):
        """Update accounts based on the last step result df of data."""
        for idx, row in df.iterrows():
            if verbose: print([len(v) for k,v in self.get_uids_per_stage().items()])
            self._create_new_accounts(row)
            if verbose: print([len(v) for k,v in self.get_uids_per_stage().items()])
            self._remove_decayed_accounts(row)
            if verbose: print([len(v) for k,v in self.get_uids_per_stage().items()])
            self._shift_accounts(row)
            if verbose: 
                print([len(v) for k,v in self.get_uids_per_stage().items()])
                print('-----')

    # Methods for outputs and reports
    def retrieve_accounts(self) -> pd.DataFrame:
        return pd.DataFrame(data=[a() for a in self.accounts.values()])