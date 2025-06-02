import matplotlib.pyplot as plt
import pandas as pd
import pysd

from pathlib import Path
from pysd.py_backend.output import ModelOutput

import warnings
# warnings.filterwarnings('ignore')

ROOT = Path(__file__).parent.parent

stocks = [
    'mql',
    'sql', 
    'prospects', 
    'pitched',
    'presentations', 
    'bidded',
    'signed', 
    'active',
    'stale', 
]

class SDModel:

    p2model = ROOT /'data/04-crm.mdl'
    assert p2model.suffix == '.mdl', f"Expected model file to have .mdl extension, got {p2model.suffix}."
    assert p2model.is_file(), f"Model file {p2model} does not exist."

    def __init__(self, p2model=None, final_time=200, params=None):
        if p2model is not None:
            self.p2model = Path(p2model)
            assert p2model.suffix == '.mdl', f"Expected model file to have .mdl extension, got {p2model.suffix}."
            assert p2model.is_file(), f"Model file {p2model} does not exist."
        self.model = pysd.read_vensim(self.p2model)
        self.final_time = final_time
        self.params = params if params else {}
        self.all_results_df = None
        self.step_results_df = None
        # Remove previous output file if it exists
        self.p2model.with_suffix('.pic').unlink(missing_ok=True)  

    def steps(self, num_steps=1, params=None):
        model = pysd.load(self.p2model.with_suffix('.py'))
        output = ModelOutput()
        if self.p2model.with_suffix('.pic').exists():
            model.set_stepper(output,
                            final_time=self.final_time,
                            initial_condition=str(self.p2model.with_suffix('.pic')),
                            # return_columns=coi,
                            # step_vars=["nb industry events"],
                            )
        else:
            model.set_stepper(output,
                            final_time=self.final_time,
                            )
        model.step(
            num_steps=num_steps,
            # step_vars={"nb industry events": 1}
            )
        model.export(self.p2model.with_suffix('.pic'))
        self.step_results_df = output.collect(model)
        if self.all_results_df is None:
            self.all_results_df = self.step_results_df
        else:
            # concatenate new results to existing results, dropping the first row of new result equal to last row
            self.all_results_df = pd.concat([self.all_results_df, self.step_results_df.iloc[1:,]])

    def plot_results(self, coi, title='ModelOutput Results'):
        if self.all_results_df is None: 
            print("No results to plot. Please run the model first.")
            return
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            self.all_results_df[coi].plot(ax=ax)
            plt.title(title)
            plt.xlabel('Month')
            plt.ylabel('Value')
            plt.legend()
            plt.show()


var_of_interest = [
    # MQL Flows
    # 'mql',
    'mql website', 'mql online campaign', 'mql industry events', 'mql salesreps',  
    'mql decay', 
    # SQL Flows
    # 'sql',
    'sales qualified', 'stale prospects', 'lost bids', 'completed', 
    'new prospects',
    'sql decay',
    # PROSPECTS FLOW
    # 'prospects', 
    'new prospects',
    'presentations','prospect decay', 
    # PITCHED FLOW
    # 'pitched',
    'presentations','stale prospects',
    'bids', 
    # BIDDED FLOW
    # 'bidded',
    'bids', 
    'contracts','lost bids',
    # SIGNED Flow
    # 'signed', 
    'contracts',
    'satisfied', 'unsatisfied',
    # ACTIVE FLOW
    # 'active',
    'satisfied',
    'completed', 
    # STALE Flow
    # 'stale', 
    'unsatisfied',
]

var_of_interest = [
    # MQL Flows
    # 'mql',
    'mql website', 'mql online campaign', 'mql industry events', 'mql salesreps',  
    'mql decay', 
    # SQL Flows
    # 'sql',
    'sales qualified', 'stale prospects', 'lost bids', 'completed', 
    'new prospects',
    'sql decay',
    # PROSPECTS FLOW
    # 'prospects', 
    'new prospects',
    'presentations','prospect decay', 
    # PITCHED FLOW
    # 'pitched',
    'presentations','stale prospects',
    'bids', 
    # BIDDED FLOW
    # 'bidded',
    'bids', 
    'contracts','lost bids',
    # SIGNED Flow
    # 'signed', 
    'contracts',
    'satisfied', 'unsatisfied',
    # ACTIVE FLOW
    # 'active',
    'satisfied',
    'completed', 
    # STALE Flow
    # 'stale', 
    'unsatisfied',
]

var_of_interest = [
    # MQL Flows
    # 'mql',
    'mql website', 'mql online campaign', 'mql industry events', 'mql salesreps',  
    'mql decay', 
    # SQL Flows
    # 'sql',
    'sales qualified', 'stale prospects', 'lost bids', 'completed', 
    'new prospects',
    'sql decay',
    # PROSPECTS FLOW
    # 'prospects', 
    'new prospects',
    'presentations','prospect decay', 
    # PITCHED FLOW
    # 'pitched',
    'presentations','stale prospects',
    'bids', 
    # BIDDED FLOW
    # 'bidded',
    'bids', 
    'contracts','lost bids',
    # SIGNED Flow
    # 'signed', 
    'contracts',
    'satisfied', 'unsatisfied',
    # ACTIVE FLOW
    # 'active',
    'satisfied',
    'completed', 
    # STALE Flow
    # 'stale', 
    'unsatisfied',
]

var_of_interest = [
    # MQL Flows
    # 'mql',
    'mql website', 'mql online campaign', 'mql industry events', 'mql salesreps',  
    'mql decay', 'sales qualified',
    # SQL Flows
    # 'sql',
    'sales qualified', 'stale prospects', 'lost bids', 'completed', 
    'new prospects',
    'sql decay',
    # PROSPECTS FLOW
    # 'prospects', 
    'new prospects',
    'presentations','prospect decay', 
    # PITCHED FLOW
    # 'pitched',
    'presentations','stale prospects',
    'bids', 
    # BIDDED FLOW
    # 'bidded',
    'bids', 
    'contracts','lost bids',
    # SIGNED Flow
    # 'signed', 
    'contracts',
    'satisfied', 'unsatisfied',
    # ACTIVE FLOW
    # 'active',
    'satisfied',
    'completed', 
    # STALE Flow
    # 'stale', 
    'unsatisfied',
]

flows_mql = [
    'mql',
    'mql website', 'mql online campaign', 'mql industry events', 'mql salesreps',  
    'sales qualified', 'mql decay',
]
flows_sql = [
    'sql',
    'sales qualified', 'stale prospects', 'lost bids', 'completed', 
    'new prospects',
    'sql decay',
]
flows_prospects = [
    'prospects', 
    'new prospects',
    'presentations','prospect decay', 
]
flows_pitched = [
    'pitched',
    'presentations','stale prospects',
    'bids', 
]
flows_bidded = [
    'bidded',
    'bids', 
    'contracts','lost bids',
]
flows_signed = [
    'signed', 
    'contracts',
    'satisfied', 'unsatisfied',
]
flows_active = [
    'active',
    'satisfied',
    'completed', 
]
flows_stale = [
    'stale', 
    'unsatisfied',
]

flows = {
    'mql': flows_mql,
    'sql': flows_sql,
    'prospects': flows_prospects,
    'pitched': flows_pitched,
    'bidded': flows_bidded,
    'signed': flows_signed,
    'active': flows_active,
    'stale': flows_stale,
}

coi_wip = [
    'new mql',
    'mql decay', 'mql industry events', 'mql online campaign', 'mql salesreps', 'mql website', 
    'mql2sql', 
    'mql',
    'sql', 
    # 'prospects', 
    # 'pitched',
    # 'presentations', 
    # 'bidded',
    # 'signed', 
    # 'active',
    # 'stale', 
    # 'contracts',
    # 'bid2close', 
    # 'bids', 'completed', 
    # 'customer satisfaction rate', 'decay rate', 'lost bids', 
    # 'nb industry events',
    # 'nb mthly website visitor', 
    # 'new prospects',
    # 'online campaigns clickthru', 'online campaigns targets', 
    # 'prez2bid', 'prospect decay', 'prospect2prez',
    # 'raw leads from website', 'rawlead2mql industry event',
    # 'rawlead2mql online campaign', 'rawlead2mql website',
    # 'rawleads industry events', 'rawleads online campaign',
    # 'rawleads salesreps', 'sales qualified', 'salesrep leads2mql',
    # 'satisfied', 
    # 'sql decay', 'sql salesreps',
    # 'sql2prospect', 
    # 'stale prospects', 'unsatisfied',  'website cta rate'
]



if __name__ == "__main__":
    pass
    model = SDModel()