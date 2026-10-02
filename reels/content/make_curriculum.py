import json, re
MODULES = [
 (1, "Շուկայի և crypto-ի հիմունքներ"), (2, "Անվտանգություն, scam-եր և բորսա"), (3, "Ռիսկի հիմունքներ"),
 (4, "Թրեյդինգի մեխանիկա"), (5, "Գրաֆիկի ընթերցում"), (6, "Market Structure և Liquidity"),
 (7, "Order Blocks և FVG"), (8, "Ռիսկ և հոգեբանություն"), (9, "Ռազմավարություն"),
 (10, "Backtesting և վիճակագրություն"), (11, "Դերիվատիվներ, մակրո, on-chain")]
TITLES = {
2: ["Wallet-ի տեսակները", "Private Key և Seed Phrase", "Անվտանգության հիմունքներ", "2FA", "Ինչպես ստուգել կայքը",
    "Scam. կեղծ support", "Scam. բուրգեր", "Scam. կեղծ giveaway", "Scam. ծանոթությունից ներդրում", "Scam. pump and dump",
    "Scam. կեղծ airdrop", "Scam. «VIP ազդանշաններ»", "Բորսայի կառուցվածքը", "Ինչպես ընտրել բորսա", "Trading Pair",
    "USDT և quote currency", "Ի՞նչ է պոզիցիան", "Bid, Ask և Spread", "Market Order", "Limit Order", "Stop Order",
    "Միջնորդավճարներ", "Հարկեր և կարգավորում", "Ամփոփում + տնային առաջադրանք"],
3: ["Ինչու է ռիսկը առաջինը", "Ճշմարտությունը սկսնակների մասին", "Risk per Trade", "0.5% և 1% կանոնը",
    "Stop Loss-ի գաղափարը", "Position Size-ի բանաձևը", "Position sizing. հաշվարկ", "Risk/Reward Ratio", "1R-ի գաղափարը",
    "Win Rate և R/R կապը", "Կորուստների շարքի մաթեմատիկան", "Drawdown", "Վերականգնման մաթեմատիկան", "Դեմո և paper trading",
    "Trading Journal", "FOMO, Fear, Greed", "Revenge Trading և Overtrading", "Ամփոփում + տնային առաջադրանք"],
4: ["Trading Volume", "Order Book", "Market Depth", "Slippage", "Maker և Taker", "Պոզիցիայի բացում և փակում",
    "Take Profit և Partial TP", "Stop Market vs Stop Limit", "Entry Price", "P&L-ի հաշվարկ", "ROE և ROI", "Spot և Futures",
    "Long և Short", "Leverage", "Margin", "Isolated և Cross Margin", "Liquidation", "Liquidation Price",
    "Leverage-ի իրական ռիսկը", "Funding Rate", "Open Interest", "Long/Short Ratio", "Liquidations Data",
    "TradingView-ի ինտերֆեյսը", "Chart-ի կարգավորում", "Alert-ներ", "Օրդերների համեմատություն",
    "Իսկ իրականում. slippage", "Simulated trade", "Ամփոփում + տնային առաջադրանք"],
5: ["Մոմի կառուցվածքը (OHLC)", "Bullish և Bearish մոմ", "Timeframe-ների իմաստը", "Կարճ և երկար timeframe-ներ",
    "Higher Timeframe Analysis", "Trend-ի սահմանումը", "Uptrend. HH և HL", "Downtrend. LH և LL", "Range", "Swing High և Low",
    "Support", "Resistance", "Major S/R և Round Numbers", "Trendline", "Breakout", "Fakeout", "Retest", "Consolidation",
    "Ծավալի վերլուծություն", "Moving Average", "RSI", "MACD", "VWAP", "Bollinger Bands", "Double Top և Bottom",
    "Head and Shoulders", "Triangles և Flags", "Իսկ իրականում. chart-ի աղմուկը", "Ինդիկատորների սահմանները",
    "Ամբողջական Chart Analysis + տնային"],
6: ["Market Structure", "Internal և External Structure", "Major և Minor Swing", "Structural High/Low", "BOS", "CHOCH",
    "MSS", "Displacement", "Impulse և Correction", "Liquidity (խորացված)", "Buy-Side և Sell-Side Liquidity",
    "Equal Highs և Lows", "Previous Day High/Low", "Previous Week High/Low", "Session High/Low",
    "Internal և External Liquidity", "Liquidity Sweep", "Sweep + Reclaim", "Stop Hunt", "Inducement",
    "Liquidity Hierarchy", "Structure + Liquidity", "Իսկ իրականում. structure", "Ամբողջական վերլուծություն + տնային"],
7: ["Order Block", "Bullish և Bearish OB", "Valid OB-ի չափանիշները", "Structural OB", "Fresh, Mitigated, Invalid OB",
    "OB Selection", "Fair Value Gap", "Bullish և Bearish FVG", "FVG Formation", "FVG Fill", "Displacement + FVG",
    "OB + FVG", "Liquidity Sweep + OB", "MSS + OB", "Premium և Discount", "Equilibrium", "Dealing Range", "Repricing",
    "Mitigation", "Rejection vs Continuation", "Strong vs Weak Zone", "Multi-Timeframe OB", "Entry Model",
    "Իսկ իրականում. SMC", "SMC-ի սահմանները", "SMC Walkthrough + տնային"],
8: ["Structural Stop Loss", "Volatility-based Stop", "ATR և Stop Loss", "Take Profit-ի կառուցվածք",
    "Liquidity-based Take Profit", "Minimum R/R", "1:2 և 1:3 R/R", "Break-even Win Rate", "Expectancy",
    "Losing Streak (խորացված)", "Maximum Drawdown", "Risk of Ruin", "Daily Loss Limit", "Weekly Loss Limit",
    "Կորելացված պոզիցիաներ", "Overtrading (խորացված)", "Revenge Trading (խորացված)", "Greed", "Fear", "Discipline",
    "Trading Journal (խորացված)", "Post-Trade Review", "Հոգնածություն և որոշումներ", "Trading Rulebook",
    "Իսկ իրականում. drawdown", "Ամփոփում + տնային առաջադրանք"],
9: ["Trading Strategy", "Setup vs Strategy", "Strategy-ի 5 բաղադրիչները", "Market Condition Filter", "HTF Bias",
    "Long և Short Bias", "Entry Conditions", "Exit Conditions", "Stop Conditions", "No-Trade Conditions", "Session Filter",
    "Volatility Filter", "Volume Filter", "Liquidity Filter", "Funding և OI Filter", "Confluence", "A և B Setup",
    "Setup Scoring", "Trade Checklist", "Entry Trigger", "Confirmation vs Anticipation", "Aggressive և Conservative Entry",
    "Scale In", "Partial Exit", "Long Strategy", "Short Strategy", "Իսկ իրականում. վատ շուկա", "Ամփոփում + տնային առաջադրանք"],
10: ["Backtesting", "Ինչու Backtest անել", "Historical Data", "Data Quality", "Sample Size", "Manual Backtesting",
     "Կանոնների գրանցում", "Entry-ի ստանդարտացում", "Exit-ի ստանդարտացում", "Fees-ի ներառում", "Slippage-ի ներառում",
     "Win Rate (վիճակագրություն)", "Average Win և Loss", "Expectancy-ի հաշվարկ", "Profit Factor", "Equity Curve",
     "Drawdown Curve", "Sharpe Ratio", "Sortino Ratio", "R-Multiple", "MAE և MFE", "Out-of-Sample", "Forward Testing",
     "Overfitting", "Data Snooping", "Optimization և Robustness", "Իսկ իրականում. backtest vs իրական", "Backtest Project + տնային"],
11: ["Futures (խորացված)", "Perpetual Contracts", "Funding Rate (խորացված)", "Open Interest (խորացված)", "Price + OI",
     "Price + Funding", "Long և Short Liquidations", "Liquidation Clusters", "Basis", "Contango և Backwardation",
     "BTC Dominance", "Altcoin Market Structure", "Stablecoin Liquidity", "Total Market Cap", "On-Chain Data",
     "Exchange Inflows և Outflows", "Whale Activity", "Realized vs Unrealized", "Federal Reserve", "Interest Rates",
     "Inflation / CPI", "Employment Data", "DXY", "Treasury Yields", "Risk-On / Risk-Off", "Macro + Crypto",
     "News-ի ազդեցությունը", "Market Context Analysis + ավարտ"],
}
CALC = re.compile(r"հաշվարկ|բանաձև|Expectancy|Sharpe|Sortino|Ratio|R-Multiple|Profit Factor|Risk of Ruin|մաթեմատիկա|Win Rate|P&L|ROE|Position Size|Break-even")
EXPL = re.compile(r"Ամփոփում|Ամբողջական|Walkthrough|Project|Strategy$|Իսկ իրականում|Simulated|Analysis")

from m1 import M1
from m2 import M2
from m5 import M5
SCRIPTED = {2: M2, 5: M5}
lessons = []
for n, spec in enumerate(M1, 1):
    lessons.append(dict(spec, id=f"M1-{n:02d}", module=1, n=n, status="script"))
for m, titles in TITLES.items():
    for n, t in enumerate(titles, 1):
        if n in SCRIPTED.get(m, {}):
            spec = SCRIPTED[m][n]
            lessons.append(dict(spec, id=f"M{m}-{n:02d}", module=m, n=n, status="script")); continue
        typ = "calc" if CALC.search(t) else "explain" if EXPL.search(t) else "concept"
        lessons.append({"id": f"M{m}-{n:02d}", "module": m, "n": n, "title": t, "type": typ, "status": "planned",
                        "negative": t.startswith("Scam"), "introduces": [f"M{m}-{n:02d}"], "uses": []})
json.dump({"modules": [{"n": n, "title": t} for n, t in MODULES], "lessons": lessons},
          open("curriculum.json", "w"), ensure_ascii=False, indent=1)
print(len(lessons), "lessons;", sum(1 for l in lessons if l["status"] == "script"), "scripted")
