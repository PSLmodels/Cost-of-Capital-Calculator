(overview)=
# Overview and Assumptions

The `Cost of Capital Calculator` model produces estimates of the marginal effective tax rates on new investment under the baseline tax policy and user-specified tax reforms.  These effective rate calculations take two forms.  The *marginal effective tax rate* (METR) provides the tax wedge on new investment at the level of the business entity.  The *marginal effective total tax rate* (METTR) includes individual level taxes in the measure of the tax wedge on new investment.  One can think of the former as indicating the effect of taxes on incentives to invest from the perspective of the firm and the latter as representing effect of taxes on incentives to invest from the perspective of the saver.

As {cite}`FullertonMETR` notes, calculations of METRs depend on several assumptions.  These include those relating to equilibrium in capital markets. discount rates, inflation rates, investor expectations, churning, how investments are financed, how risk is treated, and whether one believes the "old view" or "new view" of dividend taxes better represents investment incentives.  `Cost of Capital Calculator`'s equilibrium assumptions include the assumption that the marginal investment earns an after-tax rate of return equal to the market rate of return, returns across asset types are equalized, investors' risk-adjusted returns from debt and equity are equalized.  Real discount rates and inflation rates are taken from the Congressional Budget Offices forecasts of nominal interest rates and inflation.  `Cost of Capital Calculator` assumes no uncertainty in investment returns.  We use historical data on the time equities are held and how investment is financed to inform effective tax rates on capital gains and financial policy decisions, respectively.  `Cost of Capital Calculator` assumes the "old view" of dividend taxation in our calculations of the METTRs, implying that dividend taxes affect investment incentives.

The methodology to calculate METRs and METTRs follows closely {cite}`CBO_ETRs`.

One should note that these METR and METTR calculations include only federal tax policy (current law or the user specified proposal) and therefore exclude the effects of state and local tax policy on investment incentives.  Integrating such policies is a worthwhile project, but the results here are generally sufficient for comparing alternative federal tax proposals.


This guide is organized as follows.  Section {ref}`sec:METR` and Section {ref}`sec:METTR` describe how the cost of capital and effective tax rates are computed.  Next, we describe how we measure fixed assets by asset type, industry, and tax treatment in Section {ref}`sec:assets`.  The methodology to allocate land and inventories across industry and tax treatment is described in Sections {ref}`sec:land` and {ref}`sec:inventories`.  Finally, we discuss how the values of the model parameters are determined in Section {ref}`sec:params`.

(sec:CoC)=
# The Cost of Capital

 By definition, the marginal investment is the investment whose before tax return is equivalent to the cost of capital, $\rho_{i,m,j}$. The cost of capital is given by:

```{math}
:label: eqn:coc
\rho_{i,m,j} = \frac{(r_{m,j}-\pi+\delta_{i})}{1-u_{j}}(1-u_{j}z_{i})+w_{i,m,j}-\delta_{i},
```

 where $\delta_{i}$ is the rate of economic depreciation, $u_{j}$ is the statutory income tax rate at the first level of taxation (e.g., at the business entity level for C-corporations and at the individual level for pass-through business entities), $z_{i}$ is the net present value of deprecation deductions from a dollar of new investment, and $w_{i,m,j}$ is the property tax rate.


The `Cost-of-Capital-Calculator` calculates the cost of capital, $\rho_{i,m,j}$, separately for each type of asset, production industry, and tax treatment (corporate or non-corporate).
The after-tax rate of return is given by:

```{math}
:label: eqn:after_tax_rate_return
r^{'}_{m,j}-\pi = f_{m,j}\left[i-\pi\right] + (1-f_{m,j})E_{j},
```

 where $f_{m,j}$ represents the fraction of the marginal investment financed with debt by firms in industry $m$ and of tax entity type $j$.

In addition to the cost of capital, the `Cost-of-Capital-Calculator` reports two related measures:
* The user cost of capital (ucc): $ucc_{i,m,j} = \rho_{i,m,j} + delta_{i}$
* The tax wedge, which is the difference between the before tax rate of return (which is equivalent to the cost of capital for marginal investments) and the after-tax return top savings. The tax wedge = $\rho_{i,m,j}-s_{m,j}$

(sec:METR)=
# Marginal Effective Tax Rates

The marginal effective tax rate is calculated as the expected pre-tax rate of return on a marginal investment minus the real after-tax rate of return to the business entity, divided by the pre-tax rate of return on the marginal investment.  That is:

```{math}
:label: eqn:metr
METR_{i,m,j} = \frac{\rho_{i,m,j} - (r^{'}_{m,j}-\pi)}{\rho_{i,m,j}},
```

where the subscripts $i$, $m$, and $j$ refer to the type of asset, the production industry, and the tax entity type (e.g., C-corporation, partnership, S-corporation).  The variable $\rho_{i,m,j}$ is the pre-tax rate of return on the marginal investment, $r^{'}_{m,j}$ is the business entity's nominal after-tax rate of return and $\pi$ is the rate of inflation (so that $r_{m,j}-\pi$ is the real after-tax rate of return).  It is assumed that the business entity discounts future cash flow by the rate $r_{m,j}$ (the prime in $r^{'}_{m,j}$ differentiates the after-tax rate of return from the firm's discount rate).

At times users may be interested in the variation in $METR$s across asset types, in which case we can use the $METR$ calculation outlined above. At other times users may wish to view the variation in $METR$s across industry.  In this case, we compute a weighted average cost of capital for each production industry and tax treatment as follows:

```{math}
:label: eqn:wacc
\rho_{m,j} = \frac{\sum_{i=1}^{I}\widetilde{FA}_{i,m,j}\rho_{i,j}}{\sum_{i=1}^{I}\widetilde{FA}_{i,m,j}},
```

 where the subscripts $i$, $m$, and $j$, refer to the asset type, production industry, and tax entity type.  The calculation of the variable $\widetilde{FA}_{i,m,c}$ is discussed below.

With the cost of capital for all fixed assets in an industry-tax treatment grouping, we then compute the $METR$ of the industry and tax treatment as:

```{math}
:label: eqn:metr_minor
METR_{m,j} =  \frac{\rho_{m,j} - (r^{'}_{m,j}-\pi)}{\rho_{m,j}},
```

## Modifications to the METR Calculations for Certain Assets

Two classes of assets, inventories and land, necessitate slightly modifications from the above methodology when computing $METR$s.  In addition, owner occupied housing faces some different tax treatment and thus deserves its own discussion.  This section discusses the modifications to the $METR$ calculations described above for these asset categories.

### Inventories

In calculating the $METR$ for inventory investments, the cost of capital is defined as follows:

```{math}
:label: eqn:coc_inventory
\rho = \phi \rho_{FIFO} + (1-\phi)\rho_{LIFO},
```

where $phi$ are the fraction of inventories that use FIFO accounting and $\rho_{FIFO}$ and $\rho_{LIFO}$ are given as:

```{math}
:label: eqn:inventory_fifo
\rho_{FIFO} = \frac{1}{Y_v} log(\frac{e^{(Y_v} - u_{j}}{(1 - u_{j})} - \pi,
```

and

```{math}
:label: eqn:inventory_lifo
\rho_{LIFO} = \frac{1}{Y_v} log(\frac{e^{(r_{m,j}-\pi)Y_v} - u_{j}}{(1 - u_{j})} - \pi,
```

where $Y_{v}$ is the average number of years that inventories are held.


### Land

To be completed...


### Owner-Occupied Housing

To be completed...

(sec:METTR)=
# Marginal Effective Total Tax Rates

$METTR$s include taxation at all levels, at the business entity and the individual to whom the returns from investment ultimately accrue.  The $METTR$ is computed as:

% Commenting out the next line since I don't think it's true.  It doesn't appear to be true since the required rate of return differs in the METR and METTR calculation.
%% Note that when there is no entity level tax (as is the case with non-C-corporate entities under current law), then the $METTR$ is equal to the $METR$.

```{math}
:label: eqn:mettr
METTR = \frac{\rho_{i,m,j}-s_{m,j}}{\rho_{i,m,j}}
```

In equation {eq}`eqn:mettr`. above, $s_{m,j}$ is the overall after-tax return to savers from an investment in a business entity operating in production industry $m$ and organized as a entity of type $j$.  We compute this return as:

```{math}
:label: eqn:returnurn_after_tax
s_{m,j} = f_{m,j}s_{d,m,j} + (1-f_{m,j})s_{e,m,j},
```

where $f_{m,j}$ is the fraction of the investment that is financed with debt (and corresponds to the same fraction used in the calculation of the cost of capital noted above) and $s_{d,m,j}$ and $s_{e,m,j}$ are the after-tax returns to the saver from debt and equity, respectively.  These in turn are found as:

```{math}

s_{d,m,j} = \alpha_{d,ft,j}\times \left[i(1-\tau_{int}-\pi\right] + \alpha_{e,td,j}\times s_{d,td,j} + \alpha_{d,nt,j}\times (i-\pi)
```

Here, $\alpha_{d,ft,j}$, $\alpha_{d,td,j}$, and $\alpha_{d,nt,j}$ are the fraction of debt of entities of tax treatment $j$ held in fully taxable, tax deferred, and non-taxable accounts.  The variable $s_{d,td,j}$ are the after-tax returns of tax-deferred debt investors in entities of type $j$.  The tax rate on interest income is $\tau_{int}$ and the nominal interest rate and inflation are given by $i$ and $\pi$.


The after-tax return on debt in tax deferred accounts is:

```{math}
:label: eqn:return_debt_tax_deferred
s_{d,td,j} = \frac{1}{Y_{td,j}}ln \left[(1-\tau_{td,j})e^{iY_{td,j}}+\tau_{td,j}\right]-\pi
```

The after-tax return on equity investments is given by:

```{math}
:label: eqn:return_equity
s_{e,j} = \alpha_{e,ft,j}\times s_{e,ft,j} + \alpha_{e,td,j}\times s_{e,td,j} + \alpha_{e,nt,j}\times E_{j}
```

Here, $\alpha_{e,ft,j}$, $\alpha_{e,td,j}$, and $\alpha_{e,nt,j}$ are the fraction of equity held in fully taxable, tax deferred, and non-taxable accounts.  The variables, $s_{e,ft,j}$ and $s_{e,td,j}$ are the after-tax returns of fully taxable and tax-deferred investors, respectively.

The return on equity investments in fully taxable accounts is given by:

```{math}
:label: eqn:return_equity_taxable
s_{e,ft,j} = (1-m_{j})E(1-\tau_{div}) + g_{j},
```

where $m_{j}$ are the fraction of earnings that are retained by entity of type $j$, $\tau_{div}$ is the dividend tax rate on the marginal equity investor, and $g_{j}$ is the real return paid on retained earnings after the capital gains tax on the marginal equity investor.[^new_view_note]

The return on equity in tax-deferred accounts is:

```{math}
:label: eqn:return_equity_tax_deferred
s_{e,td,j} = \frac{1}{Y_{td,j}}ln \left[(1-\tau_{td})e^{(\pi+E_{j})Y_{td,j}}+\tau_{td}\right]-\pi
```

(sec:EATR)=
# Effective Average Tax Rates

Some investment decisions are discrete: build the new plant or not, pursue this R&D effort or another, and so on.  For discrete investment decisions, firms will compare the after tax rates of returns each of the possible choices.  In such cases, the relevant measure of the impact of the tax system on their investment choices will be measured by the effective average tax rate ($EATR$).  {cite}`DG2003` propose a forward  measure of the EATR, which the `Cost-of-Capital-Calculator` also produces estimates.  The $EATR$ is computed as:

```{math}
:label: eqn:eatr
EATR = \left(\frac{p_{i,m,j} - rho_{i,m,j}}{p_{i,m,j}}\right)u_{j} + \left(\frac{\rho_{i,m,j}}{p_{i,m,j}}\right)METR_{i,m,j},
```

where $p_{i,m,j}$ is the rate of profit on the project.  Note that the $EATR$ is equal to the $METR$ for marginal projects - those who's rate of profit is equal to the cost of capital.


## Computing After-Tax Capital Gains

Capital gains are not taxed until those gains are realized through the sale of stock.  The ability to defer the tax liability from gains complicates the calculation of the after-tax gains that accrue to investors. Further complicating this calculation is that, under current law, short and long term gains are taxed at differential rates and the basis for capital gains is "stepped-up" on equity passed along to decedents upon death.  Note, we'll omit the tax entity type subscript here since this calculation only applies to those entity types that can retain earnings, namely C-corporations under current tax law.

```{math}
:label: eqn:capital_gains
g = \omega_{scg}\times g_{scg} + \omega_{lcg}\times g_{lcg} + \omega_{xcg}\times mE,
```

  where $\omega_{scg}$, $\omega_{lcg}$, and $\omega_{xcg}$ are the fractions of capital gains that are held for less than one year, more than one year but not until the owner's death, and those held until death, respectively.  The variables $g_{scg}$ and $g_{lcg}$ are the after-tax, real, annualized returns to short and long term capital gains.

```{math}
:label: eqn:short_term_capital_gains
g_{scg} = \frac{1}{Y_{scg}}\times ln\left[(1-\tau_{scg})e^{(\pi+mE)Y_{scg}}+\tau_{scg}\right]+\pi,
```

 and

```{math}
:label: eqn:long_term_capital_gains
g_{lcg} = \frac{1}{Y_{lcg}}\times ln\left[(1-\tau_{lcg})e^{(\pi+mE)Y_{lcg}}+\tau_{lcg}\right]+\pi
```

(sec:assets)=
# Computing Fixed Assets by Industry and Entity Type

In the computation of $\rho_{m,j}$, we need to have a measure of fixed assets by industry and tax treatment for each asset type, $\widetilde{FA}_{i,m,j}$. To make this calculation, we work with two different sources of data. The first is the BEA's [Detailed Data for Fixed Assets and Consumer Durable Goods](http://www.bea.gov/national/FA2004/Details/Index.html). These data allow us to identify the stock of fixed assets by industry for each asset type.  Call this variable $FA_{i,m}$.  The second source of data we draw upon are the IRS Statistics of Income (SOI) data from business entity tax returns.  From these data, we use information on depreciable assets and accumulated depreciation, aggregated by industry and tax entity type to compute a measure of the total stock of fixed assets by industry and tax treatment, $FA^{\tau}_{m,j}$.  The superscript $\tau$ is used to denote that these asset values come from tax data.  Measuring assets from tax returns is not ideal for two reasons.  First, there are reporting issues.  These line items do not affect tax liability and so are often not reported with as much accuracy as items related to income.  Relatedly, balance sheet reporting is often limited to businesses above a certain size.  The second reason is that, for the previously cited and other reasons, measures of asset from tax returns may not line up with BEA totals.  We thus use the asset totals computed from tax returns only to help apportion the BEA asset totals across tax treatment.  Namely, we compute the variable $\widetilde{FA}_{i,m,j}$ as follows:

```{math}
:label: eqn:asset_bridge
\widetilde{FA}_{i,m,j} = FA_{i,m}\times \frac{FA^{\tau}_{m,j}}{\sum_{j=1}^{J} FA^{\tau}_{m,j}}
```

 This calculation makes the implicit assumption that the mix of asset types (i.e., the percent of total assets that each asset $i$ comprises) is the same across different tax entities within an industry.

We define the set of tax entity types to be the following five entity types:

1. C-corporations
2. S-corporations
3. Corporate partners
4. Non-corporate partners
5. Sole proprietorships

Investments by C-corporations and corporate partners face the corporate income tax treatment and thus will be defined a "corporate".  Investments by other entity types face the individual income tax and will thus be defined as "non-corporate".

<!-- %There are several issues one faces when making the computation in Equation {eq}`eqn:asset_bridge`.  The first issue is the inclusion of tax-exempt entities in the BEA totals.  The second set of issues has to do with varying specificity of industry classifications between the BEA and SOI data and within the SOI data. We discuss each in turn below.
%
### Adjusting the BEA Data for Nonprofits
%The BEA data on fixed asset stocks by asset type and industry include the assets of nonprofit organizations. Since these organizations are not subject to tax, we do not need to calculate the $METR$ on their investments.  We thus want to exclude the asset attributable to nonprofits from our asset data.  We adjust the BEA data to account for the assets owned by nonprofits through the following steps:
%

1. We drop religious buildings from the BEA data.
2. Depreciable assets, minus accumulated tax depreciation by industry, were tabulated from SOI data and compared with the corresponding BEA values to find the ratio of the two: $Ratio_{m}=\frac{\sum_{j=1}^{J}FA^{\tau}_{m,j}}{\sum_{i=1}^{I}FA_{i,m}}$.  A high ratio would indicate a large presence of nonprofits in that industry because nonprofits don't file tax returns.\footnote{Nonprofits may be partners in partnerships.  We detail how we account for nonprofit partners below.}
3. We identify industries with a ratio of XX or higher to have a significant nonprofit presence.  For these industries, the ratio of SOI assets to BEA assets was normalized to the average for industries without a significant nonprofit component (excluding banking and real estate). To estimate the value of assets held by nonprofit organizations, one minus the normalized ratio was applied to the BEA value of all types of assets.
} -->


## Handling Varying Industry Specificity Between BEA and SOI Data

The BEA data in the detailed fixed asset tables are the only source of data on asset types by industry.  The level of industry detail in the BEA data differs from that in the SOI data.  To account for this, and to identify cost of capital as the finest levels of industry detail, we make the assumption that the mix of fixed assets remains the same across the children of any parent industry.  The total amount of BEA assets by asset type can then be allocated across tax treatment and SOI minor industry using Equation {eq}`eqn:asset_bridge`.


<!-- ### SOI Data with Less Industry Specificity than BEA Data
%
%If the SOI data have less specific industry groupings than the BEA data (for a specific BEA industry code $m$), then we assume that the split of assets across the "children" (i.e. more minor industry) of the ``parent (i.e., the more major industry) is the same for each pass-through entity type as it is for C corporations, where the SOI data provide more industry detail.  In particular,
%
%```{math}
%\widetilde{FA}_{i,m,j} = FA_{i,m}\times \frac{FA^{\tau}_{m3,j}\times \frac{FA^{\tau}_{m,C-corp}}{\sum_{m\in m3}FA^{\tau}_{m,C-corp}}}{\sum_{j=1}^{J} FA^{\tau}_{m3,j}\times \frac{FA^{\tau}_{m,C-corp}}{\sum_{m\in m3}FA^{\tau}_{m,C-corp}}}, \text{ where } m\in m3
%```
%
%Here, $m3$ represents the less specific industry code from the SOI data. -->

## SOI Data by Entity Type

We use IRS Statistics of Income (SOI) data on corporations, partnerships, and sole proprietorships.  These data come with varying levels of specificity.  Data on corporations are available at what the SOI call "minor industry" level.  This encompass 196 industry classifications.[^ind_class_note]  Data on partnerships and sole proprietorships are generally available at the "major" industry level.  These approximate the 3-digit NAICS codes and encompass 81 industry classifications.  Data on S-corporations are available at the "sector" level, with 21 sector classifications.  We note our methodologies below to attribute these data to the minor industry level for each entity type.  Once data for each entity type is allocated across minor industry, we utilize cross-walks to related the SOI industry codes to BEA and NAICS codes, allowing one to group industries at varying levels of detail across different classification systems.

(sec:CandS)=
### C and S Corporation Data

Tax data on subchapter C corporations come from the data files for the [SOI Tax Stats - Corporation Source Book](http://www.irs.gov/uac/SOI-Tax-Stats-Corporation-Source-Book:-Data-File) for 2011.  The link to those files is [here](http://www.irs.gov/uac/SOI-Tax-Stats-Corporation-Source-Book:-Data-File).  Specifically, we use the `2011sb1.csv` and `2011sb3.csv` files to find the aggregate amounts by industry for the following variables from Form 1120 and associated schedules: depreciable assets and accumulated depreciation.  Note that the `2011sb1.csv` file contains data from all Form 1120 returns (which includes both C and S corporations).  Thus, in calculating aggregates for subchapter C corporations only, we net out the totals by industry and line item for S corporations using the `2011sb3.csv` data.

Note that the level of industry detail in `2011sb1.csv` and `2011sb3.csv` differ, with the former reporting variables as fine as the 6-digit NAICS level and the latter reporting variables at the 2-digit level.  In order to infer S corporation data at a finer level of industry detail, we make the assumption that the each variable is distributed across minor industries within a major industry in the same way for all corporations as it they are for S corporations.  Letting $x_{m1}$ be a variable of interest reported for all corporations in detailed industry $m1$ (e.g., these may correspond to a 6-digit NAICS code) from `2011sb1.csv` and $x_{m2}$ be the same variable reported for all corporations at the less detailed industry level (e.g., 2-digit NAICS).  We thus assume that the variable $x$ (which could be depreciable assets or accumulated depreciation) for S corporations can be allocated across detailed industry categories $m1$ as:

```{math}
:label: eqn:attrib_minor
x_{m1,s}=\frac{x_{m1}}{x_{m2}}\times x_{m2,s},
```

 where $m1\in m2$.  Variables allocated in this way are then used when differencing out data from `2011sb1.csv` and `2011sb3.csv` to find the amounts for C corporations.

Using these data, we calculate the stock of fixed assets for C corporations in industry $m$ as reported on tax returns, ${FA}^{\tau}_{m,c}$, as the difference between the aggregate amounts of depreciable assets and accumulated depreciation for that industry.  We then calculate the stock of fixed assets for S-corporations in industry $m$ as reported on tax returns, ${FA}^{\tau}_{m,s}$, as the difference between the aggregate amounts of depreciable assets and accumulated depreciation for that industry for S-corporations.

### Partnership Data

For partnerships, we draw upon the [SOI Tax Stats - Partnership Statistics by Sector or Industry](http://www.irs.gov/uac/SOI-Tax-Stats-Partnership-Statistics-by-Sector-or-Industry).  There are three files we use to get measures of partnership assets in 2012.  From the `12pa01.xls` file, we pull aggregate depreciation deductions by industry.  From `12pa03.xls`, we collect aggregate values for depreciable assets and accumulated depreciation.  Finally, we use `12pa05.xls` to help us allocate the total partnership capital stock between corporate, individual, and tax exempt partners (we discuss this further below).

Using these data, we calculate the stock of fixed assets for partnerships in industry $m$ as reported on tax returns, ${FA}^{\tau}_{m,p}$, as the difference between the aggregate amounts of depreciable assets and accumulated depreciation for that industry.

**Allocating Partnership Capital Across Types of Partners**: Partners in partnerships may be corporations, individuals, partnerships, tax-exempts, or other organizations.  Because these partners face different tax treatment, we need to allocate shares of partnership assets to each of these entity types.  We do this by using ratios of depreciable assets to net income/loss by industry.  We then use these ratios to distribute the share of total assets across partner type using the net income/loss going to partners of a given type in each industry.  The assumption is that the ratio of assets to income/loss is the same across types of partners within a given industry.  This certainly misses some of the variation in the ownership structure of partnership assets and in the distribution of partnership income, but is a method that allows us to attribute partnership assets across partner types.

File `12pa03.xls` provides data on depreciable assets by industry.  Denote these by $FA^{\tau}_{m,p}$. Using `12pa05.xls`, we gather the aggregate amounts of net income or losses distributed to partners by partner type $t$ and industry $m2$, $\text{Net Income(Loss)}_{m2,t}$. Net income and losses attributed to partners by type from the `12pa05.xls` data do not total to the same values of net income and losses reported in `12pa03.xls` because not all partnerships report their allocations.  Therefore, we make an intermediate calculation to determine the share of all attributable gains/losses accrue to which types of partners.  Note that the data from `12pa05.xls` differ in the level of industry detail from the data in `12pa01.xls` and `12pa03.xls`.  For notational clarity, let $m1$ be the more detailed classifications and $m2$ be the less detailed classifications.  Using these two pieces of information together, we find the total amount of fixed assets by industry and partner type as:

```{math}
:label: eqn:fixed_assets
\text{FA}^{\tau}_{m1,p,t}=  \underbrace{\frac{abs(\text{Net Income})_{m2,t}}{\sum_{t}abs(\text{Net Income}_{m2,t}}}_{\text{From `12pa05.xls`}} \times \underbrace{\text{FA}^{\tau}_{m1,p}}_{\text{From `12pa03.xls`}},
```

 where $m1\in m2$ and $t$ denotes partner type (individual, corporate, partnership, tax-exempt, other).  An implicit assumption here is that that share of net gains or losses attributed to each partner type is the same across each sub-industry within a major industry (i.e., the attribution across all $m_{1}\in m_{2}$ is identical).

When allocating capital across tax treatment, we will attribute the capital owned by corporate partners to the corporate sector, we will exclude assets held by tax-exempts, and the remainder will be attributed to the non-corporate sector.  One can also break out assets by entity type, rather than the more coarse, corporate/non-corporate groupings.

Finally, since partnership data do not identify depreciable assets for each minor industry, we use data from S-corporation assets at the minor industry level to attribute assets from the major industry reported in the partnership data to the corresponding minor industries that are its children.  The attribution takes the form described in Equation {eq}`eqn:attrib_minor`.  This imputation is only done for minor industries for which the partnership data do not report depreciable asset totals.


### Sole Proprietorships

We divide sole proprietorships into two groups: non-farm sole proprietors, who file a Schedule C of Form 1040, and farm sole proprietorships, who file Schedule F of Form 1040.

**Non-farm Sole Proprietorships**:  Our data for non-farm sole proprietorships come from the [SOI Tax Stats - Non-farm Sole Proprietorship Statistics](http://www.irs.gov/uac/SOI-Tax-Stats-Nonfarm-Sole-Proprietorship-Statistics) for 2011.  Specifically, we use the file `11sp01br.xls`.  These data do not record the value of depreciable assets for sole proprietorships, but they do contain depreciation deductions for sole proprietors.  Thus we impute the value of depreciable assets and land using the assumption that the ratio of depreciable assets to depreciation deductions is the same within a particular industry for sole proprietorships and partnerships.  Specifically, we find the stock of fixed assets for sole proprietors to be:

```{math}
:label: eqn:fixed_assets_sp
{FA}^{\tau}_{sp}=\frac{\text{Depreciable Assets}_{m,p}}{\text{Depreciation Deductions}_{m,p}}\times \text{Depreciation Deductions}_{m,sp},
```

 where $m$ denotes industry and the subscripts $p$ and $sp$ represent partnership and sole proprietorship, respectively.


**Farm Sole Proprietorships**:  The SOI do not provide detailed data on farm sole proprietors.  Thus for these businesses, we use [Table 67 of the *2012 Census of Agriculture*](http://www.agcensus.usda.gov/Publications/2012/Full_Report/Volume_1,_Chapter_1_US/st99_1_067_067.pdf) (*COA*).  The *COA* reports the values of land and structures (together) and the value of machinery and equipment.  These values are reported separately by type of organization (e.g, sole proprietorship, partnership).  To find the value of depreciable assets that is comparable to those for non-farm sole proprietors as reported in tax data, we must adjust these data so that we have a separate accounting of land and structures.  We use tax data to help us to impute this decomposition.

Let $R_{sp}$ be the value of land and structures held by sole proprietor farms in the *COA* and let $Q_{sp}$ be the value of machinery and equipment held by sole proprietor farms in the *COA*.  Let $R_{p}$ and $Q_{p}$ be the analogous values for farm partnerships in the *COA*.  By an accounting identity, it must be the case that $R_{i}+Q_{i}={FA}_{i}+{LAND}_{i}$ for entity of type $i\in{sp,p}$.  We thus find the ratio of land to capital held by partnerships in the agriculture industry; $\frac{\text{LAND}^{\tau}_{ag,p}}{{\text{LAND}^{\tau}_{ag,p}}+{FA}^{\tau}_{ag,p}}$, where the subscript $ag$ denotes the industry used is agriculture and the subscript $p$ denotes partnership returns. Next, this ratio is multiplied by the value for land and structures, $R_{p}$, and machinery and equipment. $Q_{p}$ for partnerships in the *COA*.  The result is an imputation for the value of land held by farm partnerships:

```{math}
:label: eqn:farm_land_value
\text{LAND}_{p}= \frac{\text{LAND}^{\tau}_{ag,p}}{\text{LAND}^{\tau}_{ag,p}+{FA}^{\tau}_{ag,p}}\times (R_{p}+Q_{p})
```

To then get an imputation for the value of land held by farm sole proprietorships, we assume that the distribution in the value of land per acre is the same for farm sole proprietorships as it is for farm partnerships.  That is, $\frac{\text{LAND}_{p}}{A_{p}}=\frac{\text{LAND}_{sp}}{A_{sp}}$, where $A_{p}$ and $A_{sp}$ denote the acreage held by farm partnerships and farm sole proprietorships, as reported in the *COA*.  We use this assumption to solve for ${LAND}_{sp}$, given our imputed value for ${LAND}_{p}$ and data on $A_{p}$ and ${A}_{sp}$.

We solve for the imputed value of fixed assets held by farm sole proprietorships as:

```{math}
:label: eqn:imputed_farm_assets
{FA}_{sp}=R_{sp}+Q_{sp}-\text{LAND}_{sp}
```

We then add the values of ${FA}_{sp}$ to the value for fixed assets that we found for non-farm sole proprietorships in the agriculture industry, ${FA}^{\tau}_{ag,sp}$.

Lastly, since sole proprietorship data do not allow us to directly identify depreciable assets for each minor industry, we use data from partnership assets at the minor industry level to attribute assets from the major industry as inferred from the sole proprietorship data to the corresponding minor industries that are its children.  The attribution takes the form described in Equation {eq}`eqn:attrib_minor`.  This imputation is only done for minor industries for which the sole proprietorship data do allow us to identify depreciable assets.

<!-- %### Residential Fixed Assets
%
%To be completed...
%
% Describe data for private residential structures.  Talk about split for owner-occupied and across industry.
%-->

(sec:land)=
# Land


To be completed...

Get Land from Fin Accounts, Inventories from BEA.  Attribute over industry/tax treatment using SOI data - much like do for fixed assets.

(sec:inventories)=
# Inventories

To be completed...

 Get Land from Fin Accounts, Inventories from BEA.  Attribute over industry/tax treatment using SOI data - much like do for fixed assets.


# Parameterization

<!-- %In order to calculate $METR$s, we need to assign values to each of the parameters described in Table {numref}`tab:param_list`.  This section describes the determination of the value of each of these parameters. -->



## Nominal Discount Rates

The nominal discount rate, $r_{m,j}$, used by the business represents the cost of funds to the business.  These funds may come from equity, either through retained earnings or new equity issues, or from debt.  The cost of equity is given by $E_{j}$ (and varies by tax treatment), the cost of debt is given by the nominal interest rate $i$ (and is the same for all businesses).  The variable $E_{j}$ represents the expected real rate of return that investors can expect if they invest in any business of entity type $j$.  In general, interest payment deductions may be deductible.  In the case of deductibility, the cost of debt is  $i(1-u_{j})$, where $u_{j}$ is the statutory tax rate on business income at the first level.  We assume that the cost of funds for the marginal investment is a weighted average of the cost of funds from these two sources, debt and equity.  In particular:

```{math}
:label: eqn:cof
r_{m,j}-\pi = f_{m,j}\left[i(1-u_{j})-\pi\right] + (1-f_{m,j})E_{j},
```

 where $f_{m,j}$ represents the fraction of the marginal investment financed with debt by firms in industry $m$ and of tax entity type $j$.  Changes to interest deductibility are reflected by changes in the cost of funds and thus the discount rate.  Likewise, systems like an allowance for corporate equity will affect the cost of funds and the discount rate.

(sec:step3)=
### Measuring Debt by Industry and Tax Treatment

We measure total debt from the [Financial Accounts of the United States](http://www.federalreserve.gov/apps/fof/FOFTables.aspx).  In particular, we use the following tables to capture debt, which we measure separately for corporate financial and nonfinancial businesss, noncorporate business, and household mortgage debt:

* B.100: Value of owner-occupied houses;
* L.103: Liabilities of nonfinancial corporations, by type of instrument;
* L.104: Liabilities of nonfinancial noncorporate business, by type of instrument;
* L.208: Total liabilities (financial corporations);
* L.223: Corporate equity outstanding, by sector (nonfinancial, financial);
* L.218: Home mortgages (households); and
* L.229: Proprietors equity in noncorporate business

To allocate debt across tax treatment, we use SOI Tax Stats Data.  The Financial Account Data combine both S corporations and C corporations in the "corporation" definition.  We thus use SOI data to identify the portion of debt and equity attributable to S corporations. Debt is assigned in proportion to interest deductions. Equity is assigned in proportion to the sum of capital stock, additional paid-in capital, and retained earnings minus treasury stock. The resulting S corporation amounts were subtracted from corporate totals (leaving the amount for C corporations) and added to noncorporate businesses.  We do the same to allocate the noncorporate across sole proprietorships and partnerships.  We further allocate the amount of debt and equity attributable to corporate partnerships using a similar method.

Specifically, we make the following calculations:

Let $debt_{corp}$ be the total amount of nonfinancial corporate debt reported in the Financial Accounts of the Untied States Table L.103, variable FL104122005.  We then allocate this total across S-corporations and C-corporations and industry $m$ as follows:

```{math}
:label: eqn:debt_ccorp
debt_{m,c} = debt_{corp}\frac{INTRST\_PD_{m,c}}{\sum_{S\in{c,s}}\sum_{m=1}^{M}INTRST\_PD_{m,S}}
```

Note that we exclude finance from the industries above since we have their debt and equity separately.

```{math}
:label: eqn:debt_scorp
debt_{m,s} = debt_{corp}\frac{INTRST\_PD_{m,s}}{\sum_{S\in{s,c}}\sum_{m=1}^{M}INTRST\_PD_{m,S}}
```

Similarly, for equity, let

```{math}
:label: eqn:capital
  X = CAP\_STCK + PD\_CAP\_SRPLS + RTND\_ERNGS\_APPR + \\
  COMP\_RTND\_ERNGS\_UNAPPR - CST\_TRSRY\_STCK
```

and let $equity_{corp}$ be total nonfinancial corporate equity from the Financial Accounts of the United States Table L.223, series LM103164103.  For C-corps, we have:

```{math}
:label: eqn:equity_ccorp
equity_{m,c} = equity_{corp}\frac{X_{m,c}}{\sum_{S\in{c,s}}\sum_{m=1}^{M}X_{m,S}}
```

And for S-corps:

```{math}
:label: eqn:equity_scorp
equity_{m,s} = equity_{corp}\frac{X_{m,s}}{\sum_{S\in{c,s}}\sum_{m=1}^{M}X_{m,S}}
```

For financial businesses, we use Table L.208, series FL794122005 for corporate debt and Table L.224 series LM793164105 for equity.  Here we can split the financial business amount across subindustries in finance (to the extent the SOI data contain such detail) and between S corp and C corp.  The methodology is the same as above, replacing the industry list with the list of finance subindustries and using the total equity and debt for financial businesses reported in the Financial Accounts.

For the corporate financial services industry, we use Table L.208 series FL794122005 for debt and Table L.223 series LM793164105 for equity.

Noncorporate, nonfinancial debt totals come from Table L.104, series FL114123005.  For non-corporate debt, we can divide between partnerships and sole props by industry using

```{math}
:label: eqn:debt_pt_minor
debt_{m,j} = debt_{noncorp}\frac{INTRST\_PD_{m,j}}{\sum_{m=1}^{M}INTRST\_PD_{m,j}}, \text{ where } j\in{p,sp},
```

<!-- %\textcolor{red}{Note that we do have partnerships and sole proprietorships in the tax data that are financial firms.  I don't know where this debt is in the Financial Accounts.  Because of this (and for now), let's exclude the finance industry from the above calculation (thus the sum is over $m\neq finance$).} -->

Noncorporate equity total comes from Table L.229, series FL152090205.  We can see partners' capital accounts for partnerships, but for sole props we don't have a good measure of the equity of proprietors.  We thus make the assumption that the equity of sole proprietors is distributed across industries in the same way that the equity of partnerships is.

```{math}
:label: eqn:equity_pt_minor
equity_{m,p+sp} = equity_{noncorp}\frac{PCA_{m,p}}{sum_{m=1}^{M}PCA_{m,p}},
```

Where $PCA_{p,m}$ are the "partnership capital accounts" for partnerships in industry $m$.  $equity_{m,p+sp}$ denotes the total amount of equity for partnerships and sole proprietorships in industry $m$.  We then find total non-corporate equity for industry $m$ as $equity_{NC,m} = equity_{p+sp,m} + equity_{s,m}$.

We then calculate the fraction of investment financed with debt by industry $m$ and entity type $j$ as: $f_{m,j} = \frac{debt_{m,j}}{equity_{m,j}+debt_{m,j}}$.  Due to the data limitations stemming from data on sole proprietors, we calculate the ratio for partnerships and sole proprietorships as being: $f_{m,p} = f_{m,sp} = \frac{debt_{m,p}+debt_{m,sp}}{equity_{m,p+sp}}$  The exception here are financial, noncorporate businesses (see issue above with debt for these businesses).  Because of this limitation, we let $f_{finance,j}=f_{finance,s}, \forall j\in\{p,sp\}$ (i.e., we take the financial policy of S-corp financial businesses and apply it to all non-corporate financial businesses).


## NPV of Depreciation Deductions

The net present value of depreciation deductions is solved for using the discount rate derived above.  Specifically, we have:

```{math}
:label: eqn:npv_depr_discount
z_{i} = \int_{0}^{Y}z_{i}(y)e^{-r_{m,j}y}dy,
```

 where $Y$ is the number of years the asset is depreciated over, $y$ is time in years, $z_{i}(y)$ is the dollar value of deprecation deductions in year $y$ per dollar invested in asset of type $i$, and $e$ is the mathematical constant.  The function $z_{i}(y)$ reflects tax policy regarding deprecation schedules.

Under straight-line depreciation, the remaining depreciable value of \$1 invested at any time $y$ is given by:

```{math}
:label: eqn:rdv_discount
V(y) =  1-\frac{y}{Y},
```

The net present value of straight-line depreciation can thus be found as:

```{math}
:label: eqn:npv_depr_sl
z_{sl}=\int_{Y}^{0}\frac{1-e^{-ry}}{Y}dy,
```

 which, when integrated and with bonus depreciation rate equal to $bonus$, yields:

```{math}
:label: eqn:npv_depr_bonus
z_{sl}=bonus + (1 - bonus)\frac{e^{-rY}}{Yr},
```

 where $Y$ is the recovery period of the asset.  With a declining balance method of deprecation, the remaining depreciable value of \$1 invested at any time $y$ is given by:

```{math}
:label: eqn:rdv_db
V(y) =  e^{-\beta y},
```

 where $\beta$ is the rate of decline in value.  Under the declining balance method of depreciation, this rate determined by the rate of acceleration of the straight-line deprecation method for an asset with a recovery period of $Y$ years.  Letting $b$ denote the degree of acceleration of straight-line depreciation, we have $\beta=\frac{b}{Y}$.  For example, for a 200\% declining balance method of an asset with a recovery period of 5 years, $\beta =\frac{2}{5}=40\%$.

To determine when it is advantageous for a filer to switch from the declining balance method to the straight-line method, we must find the point at which the slope of the declining balance method falls below the slope of the straight-line method.  It is at this point that the depreciation deductions from the straight line method exceed those of the declining balance method.  The slope of the remaining depreciable value under the declining balance method is given by:

<!-- %\ \\
%\begin{center}
%Do we want a figure like CBO shows where the two curves (for DB and SL) intersect?
%\end{center}
%\ \\ -->

```{math}
:label: eqn:slope_db
\sigma_{db} = \frac{dV}{dy}=-\beta e^{-\beta y}
```

 The slope of the straight line function depends upon the depreciable basis remaining at the switch.  Therefore, the slope of the depreciable basis for the straight line method is given by:

```{math}
:label: eqn:slope_sl
\sigma_{sl} =  \frac{dV}{dy}=\frac{e^{-\beta Y^{*}}}{Y^{*}-Y},
```

 where $Y^{*}$ is the optimal time to switch. We can thus solve for $Y^{*}$ as the point in time at which the slope of the two functions are equal.  The $Y^{*}$ that solves this is given by:

```{math}
:label: eqn:opt_switch_time
Y^{*}=Y\left(1-\frac{1}{b}\right),
```

We can now find the present value of depreciation deductions under a declining balance with switch to straight line depreciation method.  To do this, we find the integrals over the two methods for their respective portions of the recovery life.  We find the present value of deprecation deductions, $z_{dbsl}$, to be:

```{math}
:label: eqn:npv_depr_dbsl
z_{dbsl}=\int_{0}^{Y^{*}}\beta e^{-(\beta+r)y}dy+\int_{Y^{*}}^{Y}\frac{e^{-\beta Y^{*}}}{Y^{*}-Y}e^{-ry}dy,
```

 which, when integrated and with bonus depreciation, yields:

```{math}
:label: eqn:npv_dbsl_bonus
z_{dbsl}=bonus + (1 - bonus)\frac{\beta}{\beta+r}\left[1-e^{-(\beta+r)Y^{*}}\right]+\frac{e^{-\beta Y^{*}}}{(Y-Y^{*})r}\left[e^{-rY^{*}}-e^{-rY}\right]
```

<!-- %\subsubsection{Current Law Tax Depreciation Rules}
%
%To be completed...
%
% Talk about source of data for current law rules.  Limitation that don't vary across industry (but this could be added- just to time consuming now to get exactly right).
%
%\subsection{Economic Depreciation Rates}
%
%To be completed...
%
%\subsection{Rates of Return}
%
%To be completed...
%
% From historical stock returns...


% From BEA estimates... -->

(sec:params)=
# User Inputs

Users may enter tax policies and evaluate those policy changes' effects on the cost of capital and effective tax rates.  In addition, users may specific changes in the underlying macroeconomic assumptions.  Table {numref}`tab:user_params` summarizes these parameters that the user might adjust to evaluate a tax reform option of interest.  We discuss these parameters and how they are computed or entered into the model below.


```{table} User Defined Parameters
:name: tab:user_params

| Parameter                    | Description                            | Source         | Vary by asset | Vary by ind | Vary by tax treat   |
|:-----------------------------|:---------------------------------------|:---------------|:--------------|:------------|:--------------------|
| $\pi$                          | Inflation rate                         | CBO/user input | No            | No          | No                  |
| $i$                          | Nominal interest rate                  | CBO/user input | No            | No          | No                  |
| $E_c$           | Required real return on corporate equity                   | CBO/user input | No            | No          | N/A - only for corp |
| $u_j$          | Statutory business entity-level income tax             | User input     | No            | No          | Yes                 |
| $w_{i,m,j}$  | Property tax rate                      | User input     | Maybe         | Maybe       | Maybe               |
| $z_{i}(y)$       | Tax depreciation allowance             | User input     | Yes           | No          | No                  |
| Notation?                    | Haircut to Interest Deduction          | User Input     | No            | No          | Maybe               |
| Notation?                    | Allowance for Corporate Equity         | User Input     | No            | No          | Yes                 |
| $\tau_{div, j}$ | Dividend tax rate on marginal investor | User Input     | No            | No          | Yes                 |
| $\tau_{int, j}$ | Interest tax rate on marginal investor | User Input     | No            | No          | Yes                 |
| $\tau_{scg}$      | Short term capital gains rate on marginal investor                   | User Input     | No            | No          | N/A - only for corp |
| $\tau_{lcg}$      | Long term capital gains rate on marginal investor                     | User Input     | No            | No          | N/A - only for corp |
| $\tau_{d, j}$    | Tax on deferred capital income for marginal investor                 | User Input     | No            | No          | Yes                 |
```

## Economic Parameters

<!-- %To be completed... -->

One may alter the macroeconomic assumptions regarding rates of interest and inflation.[^cbo_note]

% Note interest rate from BBB corp bond and inflation rate.  Note may allow for series in future, but currently just one value

## Tax Policy Parameters

*Business Taxation*: Users to adjust the statutory marginal tax rates at the entity level, tax depreciation schedules, allowances for deductibility of interest or equity, and property tax rates.

*Individual Income Taxation*: `Cost of Capital Calculator` has the ability to allow for changes in individual income tax rates on pass-through business income, interest, dividends, and capital gains. In addition, policies affecting the deductibility of property taxes or mortgage interest affect the after-tax costs of owner-occupied housing.  To find the effect of such policy changes on the marginal investor, `Cost of Capital Calculator `interacts with OSPC's `Tax-Calculator`. Once the reform policies are specified, the `Tax-Calculator` computes the marginal tax rates on non-corporate business income, dividend income, interest income, capital gains income, and tax-deferred retirement account income.  The rates we apply to the "marginal investor" in the model are then computed as:

* $\tau_{pt}$ = weighted average marginal tax rate on ordinary, non-corporate business income (weighted by amount of non-corporate business income)
* $\tau_{div}$ = weighted average marginal tax rate on dividend income (weighted by amount of dividend income received)
* $\tau_{int}$ = weighted average of marginal tax rate on interest income (weighted by amount of interest income received)
* $\tau_{scg}$ = weighted average of marginal tax rate on short-term capital gains (weighted by amount of short-term capital gains received)
* $\tau_{lcg}$ = weighted average of marginal tax rate on long-term capital gains (weighted by amount of long-term capital gains received)
* $\tau_{xcg}$ = weighted average of marginal tax rate on capital gains held until death (weighted by amount of total capital gains received)
* $\tau_{td}$ = weighted average of marginal tax rate on pension distributions (weighted by the amount of pension distributions)
* $\tau_{h}$ = weighted average marginal tax rate on mortgage interest and property taxes (weighted by amounts of these deductions)


<!-- %\subsection{Baseline Parameter Values}
%
%To be completed...

% Table with list of parameters and their baseline values (or ranges if vary across ind/tax treatment)

%% Table generated by Excel2LaTeX from sheet 'SectorDefinitions'
%\begin{table}[htbp]
%  \centering
%  \caption{Legal Form of Organization vs. Tax Treatment}
%    \begin{tabular}{lll}
%    \hline
%    \hline
%    Entity & Legal Form of Organization & Tax Treatment \\
%   \hline
%    C Corporation & Corporate & Corporate \\
%    S Corporation & Corporate & Non-corporate \\
%    Partnership & Non-corporate & n.a. \\
%    \ \ \ Share of partnership income & n.a   & Corporate \\
%    \ \ \ attributable to corporate partners & &  \\
%    \ \ \ Share of partnership income& n.a.  & Non-corporate \\
%    \ \ \ attributable to individual partners &  &  \\
%    Sole Proprietorship & Non-corporate & Non-corporate \\
%    \hline
%    \hline
%    \end{tabular}%
%  :label: tab:org_form%
%\end{table}%


%% Might be good if can tie these sections to the code (e.g. NPV of deprec handled in calc_z, econ depr read in in calc_z.get_econ_depr(), etc).
%% Or perhaps this is a separate guide - follows the same sections here and points out where in the code the calculations are done.
 -->

[^new_view_note]: If one subscribes to the "new view", that dividend taxes do not affect investment incentives, then the first term in this equation would be zero.  We use the subscript $j$ by the parameters $m$ and $g$, but note that these parameters only apply to business entities who can retain earnings (typically, these are those with an entity level tax).

[^ind_class_note]: Pages 2-6 of the [Corporation Source Book](https://www.irs.gov/pub/irs-soi/13cosbsec1.pdf) outline these industry classifications.

[^cbo_note]: The default values are the taken from the CBO baseline forecast.
