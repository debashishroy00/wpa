# Portfolio Rebalancing Strategy

**KB-ID: RB-001**
**Category: Portfolio Management**
**Last Updated: 2024-12-16**

## Overview
Rebalancing maintains target asset allocation by selling overweight assets and buying underweight assets. Systematic rebalancing enhances returns and controls risk.

## Rebalancing Methods

### 1. Calendar Rebalancing
**Frequency Options:**
- **Quarterly**: Good balance of maintenance and tax efficiency
- **Semi-annual**: Lower transaction costs, adequate for most
- **Annual**: Minimal costs, may allow larger drifts

**Best Practice**: Semi-annual rebalancing on fixed dates (Jan 1, July 1)

### 2. Threshold Rebalancing
**Absolute Threshold**: Rebalance when allocation differs by fixed percentage
- 5% threshold: Rebalance if target 60% stocks becomes 55% or 65%
- 10% threshold: More tax-efficient, less frequent trading

**Relative Threshold**: Rebalance when allocation differs by percentage of target
- 20% relative: 60% target becomes 48% (20% below) or 72% (20% above)
- More responsive for smaller allocations

### 3. Hybrid Approach (Recommended)
```
Rebalancing Triggers:
├── Time: Check quarterly, rebalance semi-annually
├── Threshold: 5% absolute drift for major asset classes
└── Bandwidth: 20% relative drift for smaller allocations
```

## Account-Specific Strategies

### Tax-Advantaged Accounts (401k, IRA)
**Rebalancing Freedom**
- No tax consequences for rebalancing
- Can rebalance frequently without penalty
- Use for large allocation adjustments

**Implementation:**
1. Rebalance 401k/IRA accounts first
2. Adjust new contributions to help rebalancing
3. Consider asset location optimization

### Taxable Accounts
**Tax-Aware Rebalancing**
- Harvest tax losses when rebalancing
- Avoid wash sale rules (30-day rule)
- Consider holding periods for capital gains rates

**Tax-Loss Harvesting Integration:**
```
Rebalancing + TLH Process:
1. Identify overweight positions with losses → Sell
2. Identify underweight positions → Buy
3. Use proceeds from loss sales to fund purchases
4. Avoid substantially identical securities
```

## Allocation Drift Tolerances

### Major Asset Classes (>20% allocation)
- **Equity/Bond Balance**: 5% absolute threshold
  - Target 60/40 → Rebalance at 55/45 or 65/35
- **Domestic/International**: 5% absolute threshold

### Mid-Size Allocations (5-20%)
- **REITs, Sectors**: 3% absolute or 25% relative
- **Small-cap, Value**: 3% absolute threshold

### Small Allocations (<5%)
- **Commodities, Alternatives**: 2% absolute or 50% relative
- **Individual stocks**: 1% absolute threshold

## Implementation Mechanics

### New Contribution Rebalancing
**Most Tax-Efficient Method:**
1. Calculate current allocation percentages
2. Direct new contributions to underweight assets
3. Continue until back to target allocation

**Advantages:**
- No selling required (no taxes/fees)
- Dollar-cost averaging benefit
- Minimal transaction costs

### Exchange/Sale Rebalancing
**When Contributions Insufficient:**
1. Calculate required trades to reach targets
2. Prioritize tax-advantaged accounts for large trades
3. In taxable accounts, harvest losses first
4. Use ETFs to minimize bid-ask spreads

### Minimum Trade Sizes
- **401k plans**: Often $100+ minimums
- **Brokerages**: Consider $1,000+ to minimize relative costs
- **Fractional shares**: Enable precise rebalancing

## Market Condition Adjustments

### Bear Markets (>20% decline)
**Opportunity Enhancement:**
- Consider more frequent rebalancing
- Large equity purchases at discount prices
- May trigger significant tax-loss harvesting

**Risk Management:**
- Maintain emergency fund separately
- Don't abandon strategy due to emotions
- Consider slight equity overweight if young

### Bull Markets
**Disciplined Selling:**
- Resist urge to let winners run indefinitely
- Take profits systematically
- Build up bond/cash allocation for opportunities

**Tax Considerations:**
- May trigger significant capital gains
- Consider holding periods (1 year for long-term rates)
- Harvest offsetting losses if available

### High Volatility Periods
- More frequent monitoring (monthly vs quarterly)
- Consider smaller threshold bands
- Prepare for emotional decision-making challenges

## Cost-Benefit Analysis

### Transaction Costs
**Typical Costs:**
- Commission-free ETF trades: $0
- Mutual fund early redemption: $49 (if <90 days)
- Bid-ask spreads: 0.01-0.1% for liquid ETFs
- Market impact: Minimal for <$10M trades

### Tax Costs (Taxable Accounts)
**Capital Gains:**
- Short-term: Ordinary income rates (up to 37%)
- Long-term: 0%, 15%, or 20% depending on income
- State taxes: Varies by state (0-13.3%)

### Rebalancing Benefit
**Academic Research:**
- Adds 0.1-0.4% annual return for typical portfolios
- Risk reduction benefit often exceeds return benefit
- Benefits highest during volatile periods

## Behavioral Considerations

### Automation Benefits
**Systematic Approach:**
- Removes emotion from selling high/buying low
- Creates disciplined profit-taking
- Reduces behavioral biases

**Implementation:**
- Set calendar reminders
- Use target-date funds for hands-off approach
- Automate contribution redirections

### Common Mistakes
❌ **Chasing Performance**: Abandoning rebalancing to chase hot sectors
❌ **Tax Paralysis**: Never rebalancing taxable accounts due to tax fears
❌ **Over-Rebalancing**: Daily/weekly adjustments that increase costs
❌ **Perfectionism**: Requiring exact target percentages

## Special Situations

### Large Windfalls (Inheritance, Bonus)
1. Assess current allocation including new money
2. Invest windfall to restore target allocation
3. Consider dollar-cost averaging for very large amounts
4. May be opportunity to rebalance entire portfolio

### Pre-Retirement (10 years out)
- Gradually reduce equity allocation (glide path)
- Build bond ladders or CD ladders
- Consider holding 1-2 years expenses in cash

### Retirement Phase
- Focus on tax-efficient withdrawal sequencing
- Rebalance less frequently to preserve capital
- Consider bucket strategies for different time horizons

## Technology and Tools

### Portfolio Tracking
- **Recommended**: Personal Capital, Morningstar X-Ray
- **Features**: Allocation analysis, drift monitoring
- **Alerts**: Email notifications when thresholds exceeded

### Rebalancing Calculators
- Vanguard Personal Advisor Services
- Fidelity Portfolio Review
- Portfolio Visualizer rebalancing tools

### Tax-Loss Harvesting Software
- Betterment Tax-Loss Harvesting
- Wealthfront Direct Indexing
- Interactive Brokers tax optimizer

---
**Sources**: Vanguard Research, Dimensional Fund Research, Journal of Financial Planning
**Compliance**: Educational content only, not personalized investment advice