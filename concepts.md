# CRM Simulation App

## Overall concept
This CRM simulation is used as a tool for MBA student exercise. The main principles are as follows:
- Application populates a CRM with relevant and consistent data
- The CRM is populated based on a company model using 7 steps, and using efficiency/conversion parameters for each steps
- Students query the system to understand the dynamic and performance of the sales team and the company
- Students can then propose sales process changes, resulting in the change of some of the efficiency/conversion parameters
- CRM Simulation systems run another quarter or semester and we can see the impact on performance


## Sales Process Model

### Sales Process Steps:
Models the sales funnel:
1. **Prospecting**:  Identifying potential customers.
2. **Qualification**:  Assessing fit and buying intent.
3. **Needs Assessment**:  Understanding specific requirements.
4. **Presentation**:  Demonstrating the solution's value.
5. **Objection Handling**:  Addressing concerns.
6. **Closing**:  Securing commitment.
7. **Post-Sale Follow-up**:  Ensuring satisfaction and fostering loyalty.

### Prospecting
Generates raw leads and their conversion into MQL for generation of marketing qualified leads into the pipeline. The **sources** for raw leads are:
- **Website CTA**: inquiry from contact using website, identification of users registered but not client, identified contacts from other online CTA results
    - A reasonable and typical number of unique visitors for a B2B machinery or industrial manufacturing website is approximately 2,700 to 3,100 unique visitors per month.
- **Online Campaigns**: Typically emailing campaigns, with a fixed number of targets
    - click-to-lead conversion rates for B2B email campaigns can be around 5% to 15%
- **Exhibition and Conferences**: contacts from exhibition and conferences
    - 3 days x 8 hours x 4 staff x 3 interaction / person / hour = 288 contacts
    - 67% of contacts are leads (i.e. not from existing customers)
    - 33% of contacts are from existing customers
- **Sales Representatives** also go out on cold calls and identify leads
    - 20 to 50 new leads per quarter per sales rep

The model will use company parameters to define how many raw leads are created each month. From this and qualification conversion into MQL, the model will create specific MQLs with related info (name, source, type, etc.) and populate the CRM with these leads. These Marketing Qualified Leads (MQLs) represent those leads to be nurtured by Marketing. It will be used in the next phase to select Sales Qualified Leads (SQLs) for the sales team to work on.

Parameters:
- `nb_monhtly_visitors`: Number of unique visitors per month on website
- `nb_online_campaigns`: Number of online campaigns per quarter
- `nb_industry_events`: Number of industry events per quarter, i.e. exhibitions, conferences, etc.
- `nb_daily_contacts_industry_event`: Number of contacts per day at industry events
- `nb_sales_reps`: Number of sales representatives

- Key Model Variables:
    - `raw_leads_from_website`: Number of raw leads generated from the website CTA
    - `raw_leads_from_online_campaigns`: Number of raw leads generated from online campaigns
    - `raw_leads_from_industry_events`: Number of raw leads generated from industry events
    - `raw_leads_from_sales_reps`: Number of raw leads generated from sales representatives

- Rates:
    - `website_cta`: 3% to 4% of unique visitors fill out forms or self-identify as leads
    - `online_campaigns_clickthru`: 5% to 15% click-to-lead conversion rate
    - `industry_event_lead_rate`: 30% of contacts are MQL while 9% are SQL and the remaining 69% are either unqualified leads or existing customers
    - `sales_rep_lead_generation`: 20 to 50 new leads per quarter per sales rep

- Marketing Qualified Leads (MQL):
    - Website CTA:
        - `rawlead2mql`: 41%
    - Online Campaigns:
        - `rawlead2mql`: 38%
    - Industry Events: 39% of leads are qualified prospects
        - `rawlead2mql`: 30% of contacts qualified for nurturing
        - **`rawlead2sql`**: 9 % of contacts qualified for sales 
    - Sales direct calls:
        - `rawlead2mql`: 1% to 3% of cold calls convert to MQL
        > note: cold call to meeting conversion rate: 1% to 5%, averaging around 2%.

### Qualification
From marketing leads being nurtured by marketing to sales qualified leads (SQL). The model used two sources for SQLs
- **MQL**: `mql2sql`: 13% to 18%
- **Sales direct calls**: `salesrep_monhtly_sql`: 20 to 50


### Needs Assessment
*SQL-to-opportunity* split in two: `sql2prospect` and `prospect2prez`
SQL-to-opportunity is about 50% to 62%
- `sql2prospect`: 70% ($\sqrt[]{0.5}$) to 78%

### Presentation
- `prospect2presentation`: 70% ($\sqrt[]{0.5}$) to 78%

### Objection Handling/Bidding
SQL to close is about 13% in B2B Mfg, meaning that opportunity-to-close is 13%/50% = 26% (range 20% to 33%)
- `prez2bid`: 50% to 80% (average 65%)

### Closing
- `bid2close`: 20% to 50% (average 30%)

### Post-Sale Follow-up
- `customer_satisfaction_rate` = 95% to 99%

## Reference info:

### Sources of Leads

#### Website CTA Stats
- A reasonable and typical number of unique visitors for a B2B machinery or industrial manufacturing website is approximately 2,700 to 3,100 unique visitors per month.
- Only about 3% to 4% of these visitors typically fill out forms or self-identify as leads, highlighting the importance of leveraging anonymous visitor data and nurturing strategies

#### Industry Events Stats
- Exhibition Hours and Staffing: A typical 3-day trade show might have around 8 hours per day, totaling approximately 24 exhibition hours. Assuming 4 staff members manning the booth, each capable of engaging about 3 prospects per hour, the total interaction capacity is: 
    - 24 hours × 4 staff × 3 interactions/hour = 288 interactions.
- Lead Qualification Rate: Not all interactions convert into qualified leads. Research shows about 39% of interactions convert into qualified leads in B2B exhibitions. Applying this: 
    - 39% qualified leads
    - 30% qualified as MQL
    - 9% qualified as SQL
    - balance is either not qualified or not new customers
 - Lead Conversion Rate: Of these qualified leads, typically 5-10% convert into actual customers after follow-up

#### Sales Reps Cold Call to Meeting and MQL Conversion
call_to_meeting:
- Typical cold call to meeting conversion rate: 1% to 5%, averaging around 2%.
- Improved rates with training and personalization: Up to 6-10%.
- Calls needed to secure one meeting: Approximately 40-50 calls on average.
- Multiple follow-ups required: Often 5 or more calls to convert a prospect.

call_to_mql:
- Estimated range: Approximately 1% to 3%.
- This aligns with general B2B lead-to-MQL conversion rates in manufacturing, which average around 26% from leads to MQLs overall, but cold calls are an earlier and more challenging channel with lower conversion.
- Since cold calls have an average success rate of about 2% to 5% for converting to meetings or qualified engagements, the rate to MQL (a softer qualification than a meeting) would be slightly lower or similar, often around 1-3% due to the nature of cold outreach.
- The overall average lead conversion rate across B2B industries is about 2.6% to 3.3%, which supports this range.

#### Lead-to-MQL Conversion Rate Stats
Lead-to-MQL Conversion Rate Benchmark by Industry

| Industry                   | Lead-to-MQL Conversion Rate |
|----------------------------|-----------------------------|
| Aerospace & Defense        | 34%                         |
| Addiction Treatment        | 23%                         |
| **Automotive**             | 31%                         |
| **Aviation**               | 37%                         |
| B2B SaaS                   | 39%                         |
| Biotech                    | 42%                         |
| Business Consulting        | 28%                         |
| Commercial Insurance       | 40%                         |
| Construction               | 17%                         |
| Cybersecurity              | 39%                         |
| eCommerce                  | 23%                         |
| **Engineering**            | 35%                         |
| Entertainment              | 34%                         |
| Environmental Services     | 45%                         |
| Financial Services         | 29%                         |
| Higher Education & College | 45%                         |
| HVAC Services              | 42%                         |
| Industrial IoT             | 22%                         |
| IT & Managed Services      | 25%                         |
| Legal Services             | 32%                         |
| **Manufacturing**          | 26%                         |
| Medical Device             | 24%                         |
| Oil & Gas                  | 32%                         |
| PCB Design & Manufacturing | 42%                         |
| Pharmaceutical             | 41%                         |
| Real Estate                | 27%                         |
| Software Development       | 32%                         |
| Solar Energy               | 45%                         |
| Transportation & Logistics | 36%                         |

Lead-to-MQL Conversion Rate Benchmark by Marketing Channel
| Channel                | Lead-to-MQL Conversion Rate |
|------------------------|-----------------------------|
| SEO/Website            | 41%                         |
| PPC                    | 29%                         |
| **Email Marketing**    | 38%                         |
| Webinar                | 19%                         |
| Conferences            | 28%                         |
| Trade Shows            | 24%                         |
| Executive Events       | 54%                         |
| Client Referrals       | 56%                         |
| Social Media Marketing | 30%                         |
| Podcasts               | 21%                         |
| Outdoor Advertising    | 14%                         |





#### MQL_to_SQL Conversion Rates
Industry-wide average MQL to SQL conversion rates generally range from 12% to 21% depending on the sector. For **B2B manufacturing-related industries** often around **13% to 18%**


#### Sales Rep Direct Call Stats
- New Prospects Contacted: 20 to 50 new qualified prospects per quarter, depending on market maturity and lead generation support.

- New Customers Acquired (closed): Typically 1 to 5 new customers per quarter, reflecting the complexity and length of the sales cycle in packaging machinery.

### Account Sizes and Opportunities

The **typical value of a purchase order for a packaging machine** depends heavily on the **type, size, automation level, and industry application** of the machine. 

Below is a general breakdown to help you simulate realistic values in your CRM tool:

#### 1. Entry-Level Semi-Automatic Packaging Machines
- **Use Case**: Small businesses or low-volume production.
- **Examples**: Manual baggers, semi-automatic case sealers, vacuum packagers.
- **Price Range**: **$10,000 – $50,000 USD**

#### 2. Mid-Range Fully Automatic Packaging Systems
- **Use Case**: Medium-sized operations with moderate throughput.
- **Examples**: Automatic cartoners, form-fill-seal machines, labeling systems.
- **Price Range**: **$50,000 – $250,000 USD**

#### 3. High-End Industrial Packaging Lines
- **Use Case**: Large-scale manufacturing (e.g., food & beverage, pharmaceuticals, consumer goods).
- **Examples**: Integrated robotic packaging lines, high-speed bottling lines, complete turnkey systems.
- **Price Range**: **$250,000 – $1,000,000+ USD**

#### 4. Specialized or Custom Packaging Equipment
- **Use Case**: Highly regulated industries like pharma or aerospace.
- **Examples**: Cleanroom-compatible machines, sterile packaging, tamper-evident systems.
- **Price Range**: **$500,000 – $2,000,000+ USD**

#### Factors That Influence Purchase Order Value:
| Factor | Impact on Price |
|-------|------------------|
| **Automation Level** | Manual < Semi-Auto < Fully Auto |
| **Production Speed** | Higher speed = higher cost |
| **Material Type** | Food-grade, medical-grade, or hazardous materials increase complexity |
| **Integration Needs** | PLCs, IoT connectivity, MES integration add cost |
| **Customization** | Special features or compliance requirements increase price |
| **Vendor Origin** | European/American vendors often charge more than Asian suppliers |

#### Industry-Specific Examples (Average PO Value):
| Industry | Packaging Machine Type | Typical PO Value (USD) |
|----------|------------------------|-------------------------|
| Food & Beverage | Form-Fill-Seal Machine | $80,000 – $300,000 |
| Pharmaceuticals | Blister Packaging Line | $150,000 – $750,000 |
| Cosmetics | Tube Filling & Sealing Machine | $60,000 – $250,000 |
| E-commerce | Cartoning & Labeling System | $50,000 – $200,000 |
| Automotive | Custom Palletizing System | $100,000 – $500,000 |

#### Suggested Use in CRM Simulation Tool:
You can assign **realistic purchase orders** based on company size and industry:
- **SMALL**: $10,000 – $100,000 for SMEs
- **MEDIUM**: $100,000 – $500,000 for mid market companies
- **LARGE**: $500,000 – $2,000,000+ for large enterprises


### Other refs
> Average B2B funnel conversion rates?
> Data from [FirstPageSage](https://firstpagesage.com/reports/lead-to-mql-conversion-rate-benchmarks-by-industry-channel-fc/) and [Gartner](https://www.gartner.com/en/sales/topics/sales-pipeline) provide rough benchmarks for average B2B funnel conversion rates:

|Step|Rate|
|---|---|
|Lead to MQL: |25% to 35%|
|MQL to SQL: |13% to 26%|
|SQL to Opportunity: |50% to 62%|
|Opportunity to Close: |15% to 30%|


> **SQL to Sales from direct calls**:
> Expected conversion rate to customer: 20 to 50 -> 1 to 5 that is a conversion rate of 1:20 to 1:10
> Factor influencing this: time spent by sales person, access to database, tools to prequalify, skill of salesperson to pitch and ask questions


> The manufacturers AGI surveyed expect, on average, **10 percent of revenue to come from new accounts** and 12 percent from new products. Nearly **a quarter of revenue**, that is, must come from new sources. For **building systems manufacturers, over 40 percent of revenue comes from new sources**. Sales leaders indicated that these ratios will only grow. What does this mean if a company does not focus heavily on new customer and product growth? Quite simply, growth will lag and more innovative competitors will dominate the market space.

> On average, **manufacturers invest 3-10 percent of revenues** in the sales force. This includes seller compensation, management compensation, sales enablement, field marketing and a few other core investment categories. 
>
> Alexander Group’s sales benchmarking database provides a powerful set of benchmarks that consistently provide sales leaders with actionable insights. Focus areas include:
>
> - Sales productivity
> - Sales time
> - Sales deployment ratios (by role type)
> - Sales investment/expense
> - Sales readiness
> - Sales compensation pay levels and practices
> - Industry-specific benchmarks and practices

> **Average Sales Call Conversion stats** [url](https://focus-digital.co/average-sales-call-conversion-rate-by-industry/)
> Industrial Equipment and Machinery:
> - 6.61 % Industrial Equipment and Machinery
>
> Price Range
> - USD 100k to 500k: 13.33%
> - USD 500k to 1000k: 11.78%
> - USD 1000k to 5000k: 8.9%
> - USD 5M to 10M: 7.18%
>
> Source:
> - Email Marketing: 18.02%
> - Industry Events: 10.73%
> - Direct Call: 7.41%

# Reference Conversion Rates

- nb mthly website visitor=2900
- website cta rate=0.03
- online campaigns clickthru=0.1
- online campaigns targets=1000
- nb industry events=1
- rawleads industry events=80 * nb industry events
- rawleads salesreps=30
- 
- rawlead2mql website=0.41
- rawlead2mql online campaign=0.38
- rawlead2mql industry event=0.3
- salesrep leads2mql=0.02
- 
- mql2sql=0.15
- sql2prospect=0.7
- prospect2prez=0.7
- prez2bid=0.6
- bid2close=0.3
- customer satisfaction rate=0.98
- 
- decay rate=0.15