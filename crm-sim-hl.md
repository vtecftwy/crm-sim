# Architecture and Concepts

## Concepts
- Source: 
    - Website, IndustryEvent, ColdCall, OnlineCampaign, PriorProject, Referral
- AccountStage: 
    - MQL, SQL, NeedDefined, Presented, BidSubmitted, Signed, Stale
- AccountProject: 
- SalesRep
- MktgDpt
- Project/Opportunity


In agent-centric event handling (where agents like SalesRep or MktgDpt actively manage Accounts by sending and receiving events), you need a way for an agent process to send an event to a specific account process, rather than broadcasting it to all accounts.

## Agent-Centric Event Handling
Each agent (MktgDept, SalesRep, BiddingDpt) is a process that actively manages a set of Accounts or AccountProjects.

For example, the marketing department process cycles through all accounts in the MQL state and generates qualification events.

Once an Account becomes sales qualified (SQL), the marketing process emits an event assigning it to a SalesRep process.

SalesReps manage their assigned Accounts and generate opportunity events, which presales processes listen to and act upon.

Accounts themselves might be passive data holders or minimal processes that update state only when notified.

This approach distributes control among agent processes, which create and listen to events relevant to their roles.

| Process Type   | Creates Events                                  | Listens to Events                          | Role in Simulation                           |
|----------------|-------------------------------------------------|--------------------------------------------|----------------------------------------------|
| Account        | State transition events (e.g., assign salesrep) | Marketing qualification, salesrep actions  | Maintains funnel state, reacts to outreach   |
| Marketing Dept | Lead qualification, outreach events             | Account state changes (e.g., new leads)    | Drives leads from general to sales qualified |
| Salesrep       | Opportunity pitch, bid submission, deal closure | Assigned account events, presales feedback | Manages assigned accounts and opportunities  |
| Presales Dept  | Bid evaluation, technical approval              | Opportunity bid events                     | Influences bid outcomes                      |
| Opportunity    | Bid events, win/loss events                     | Salesrep and presales actions              | Represents sales deals in progress           |


## Store-Based Communication (for Robustness and Flexibility)
If you prefer to decouple agents and accounts, use a SimPy Store per account (or a dictionary mapping account IDs to their stores). Agents put messages/events into the store of the target account.

```python
import simpy

class Account:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.inbox = simpy.Store(env)

    def run(self):
        while True:
            msg = yield self.inbox.get()
            print(f"{self.env.now}: Account {self.name} received {msg}")

def agent(env, account_store):
    yield env.timeout(5)
    yield account_store.put("marketing outreach")
    print(f"{env.now}: Agent sent event to account")

env = simpy.Environment()
account1 = Account(env, "A1")
account2 = Account(env, "A2")

env.process(account1.run())
env.process(account2.run())

env.process(agent(env, account1.inbox))

env.run(until=10)
```


