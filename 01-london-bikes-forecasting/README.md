# London Bikes: Forecasting Daily Demand
 
Group project (Group 5) for the MSc in Analytics and Management at London Business School.
 
**Brief:** act as the analytics team of Transport for London (TfL) and give planners a simple, defensible model of what drives daily bike-hire demand, so they can redistribute bikes, schedule maintenance and staff docking stations.
 
---
 
## Data
- London bikes dataset: **4,383 daily observations** from January 2014
- Outcome: `bikes_hired` (daily hires)
- Predictors: weather (temperature, precipitation, UV index, snow, wind, cloud cover, visibility, …) and calendar fields (day of week, month, season)
---
 
## My contribution
I worked within a team of 7 students and was responsible for the core analytical work: **Part 1 (exploratory analysis), Part 2 (model building) and Part 3 (multicollinearity testing)**, including the written interpretation of each.
 
### Part 1: Exploratory analysis
- Built a correlation heatmap of the outcome and 10 candidate weather variables.
- Identified the variables most associated with hires (temperature, "feels like", max/min temperature, dew point and humidity, all with |r| > 0.45).
- Flagged likely redundant pairs before modelling (temperature vs "feels like", vs dew point, vs max/min temperature). This set up the formal VIF test in Part 3.
### Part 2: Model building
- Built and compared four OLS regression models (statsmodels), judged on adjusted R² and residual standard error rather than R² alone.
- Engineered two date-based indicator variables to capture structural changes in the market: entry of competing bike-hire operators (from October 2019) and the scheme's price change (from September 2022).
- Combined weather, calendar (month, season, day of week) and these market variables into the final model.
| Model | Specification | Adj. R² | Residual SE (hires/day) |
|-------|---------------|---------|--------------------------|
| A | Temperature only (baseline) | 0.359 | 7,353 |
| B | + humidity, visibility, solar radiation, weather conditions | 0.505 | 6,462 |
| C | Weather + market changes + calendar, no temperature | 0.635 | 5,548 |
| **D (final)** | **Temperature + weather + market changes + calendar** | **0.646** | **5,467** |
 
### Part 3: Multicollinearity (VIF)
- An earlier, larger specification reached adj. R² ≈ 0.70, but VIF testing showed severe multicollinearity: some variables (e.g. snow depth, precipitation cover, weather conditions) had VIFs above 1,000.
- Removed the redundant variables and refitted, deliberately trading a small amount of fit (0.70 → 0.646) for a model with stable, interpretable coefficients.
---
 
## Impact
- **Explained variance rose from 36% to 65%** relative to the temperature-only baseline (adj. R² 0.359 → 0.646).
- **Typical daily prediction error fell by about 26%**, from ~7,350 to ~5,470 hires/day.
- **Turned the model into plain-language findings for planners** (final model, all else equal):
  - each extra °C adds about **500 hires/day**;
  - each extra mm of rain removes about **280 hires/day**;
  - Sundays see about **3,800 fewer hires** than Mondays, while Tuesday–Thursday see about **2,300–2,500 more**;
  - days before the September 2022 price change averaged about **7,000 more hires** than days after it.
- Choosing an interpretable model over the highest-scoring one gave planners coefficients they can trust and act on, rather than unstable estimates driven by redundant variables.
---
 
## Tools
Python · pandas · NumPy · statsmodels · seaborn · matplotlib
 
## Files
- `london_bikes_forecasting.html`: full notebook with code, outputs and written interpretation
 
