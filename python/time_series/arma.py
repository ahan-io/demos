import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import pmdarima as pm
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error


df = pd.read_csv('website_data.csv')
df.info()
df.plot()
# plt.show()


# Prepare our data.
df = np.log(df)
df.plot()
msk = df.index < len(df) - 30 # msk 是一个包含 true/false 的矩阵
df_train = df[msk].copy()
df_test = df[~msk].copy()

# step1: Check for stationarity of time series using ADF Test


adf_test = adfuller(df_train)
print(f"p-value:{adf_test[1]}")

# step2: Transform to stationarity: differencing
df_train_diff = df_train.diff().dropna()
df_train_diff.plot()
plt.show()

adf_test = adfuller(df_train_diff)
print(f"p-value:{adf_test[1]}") # p-value 值小于0.05时，认为序列是平稳的，否则不平稳

# step3: Determine ARIMA models parameters p,q

# step4: Fit the ARIMA model
model = ARIMA(df_train, order=(2, 1, 0))
model_fit = model.fit()
print(model_fit.summary())

# another auto way to choose ARIMA model parameters.
auto_arima = pm.auto_arima(df_train, stepwise=False, seasonal=False)

# step5: Make time series predictions
residuals = model_fit.resid[1:]
fig, ax = plt.subplots(1,2)
residuals.plot(title="Residuals", ax=ax[0])
residuals.plot(title="Density", kind='kde', ax=ax[1])
plt.show()

forecast_test = model_fit.forecast(len(df_test))
df['forecast_manual'] = [None] * len(df_train) + list(forecast_test)

forecast_test_auto = auto_arima.predict(n_periods=len(df_test))
df['forecast_auto'] = [None]*len(df_train) + list(forecast_test_auto)

df.plot()
plt.show()



# Step6: Evaluate model predictions
mae = mean_absolute_error(df_test, forecast_test)
mape = mean_absolute_percentage_error(df_test, forecast_test)
rmse = np.sqrt(mean_squared_error(df_test, forecast_test))

print(f'mae - manual: {mae}')
print(f'mape - manual: {mape}')
print(f'rmse - manual: {rmse}')


mae = mean_absolute_error(df_test, forecast_test_auto)
mape = mean_absolute_percentage_error(df_test, forecast_test_auto)
rmse = np.sqrt(mean_squared_error(df_test, forecast_test_auto))

print(f'mae - auto: {mae}')
print(f'mape - auto: {mape}')
print(f'rmse - auto: {rmse}')