# London Bikes: Forecasting Daily Demand

Group project for the MSc in Analytics and Management at London Business School (Group 5).

**Brief:** help Transport for London planners understand what drives daily bike-hire demand and anticipate busy days.

## What we did
- Explored the London bikes dataset (4,383 daily observations from 2014, with weather and calendar variables)
- Built and compared four OLS regression models, judged on adjusted R² and residual standard error
- Checked multicollinearity with the Variance Inflation Factor (VIF) and removed redundant predictors
- Ran residual diagnostics on the final model

## Result
Final model (weather + month, season and day-of-week effects): **adjusted R² 0.646**, residual standard error ≈ 5,467 hires/day.

## Tools
Python · pandas · statsmodels · seaborn · matplotlib

## My contribution
[Describe the part you personally worked on]

## Files
- `london_bikes_forecasting.html`: full notebook with code, outputs and written interpretation
