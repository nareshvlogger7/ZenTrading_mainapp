import pandas as pd
import numpy as np
import yfinance as yf
import quantstats as qs
from sklearn.linear_model import LinearRegression, LogisticRegression
import warnings
warnings.filterwarnings('ignore')

def linear_regression(train, test):
    # Creating the columns of independent variables
    train['H-C'] = train['High'] - train['Close']
    train['C-L'] = train['Close'] - train['Low']
    train['H-Ht-1'] = train['High'] - train['High'].shift(1)
    train['L-Lt-1'] = train['Low'] - train['Low'].shift(1)

    x = train[['H-C', 'C-L', 'H-Ht-1', 'L-Lt-1']].iloc[:-1].dropna()
    y = train[['Close']].shift(-1).iloc[1:-1]

    model = LinearRegression()
    model.fit(x, y)

    test['H-C'] = test['High'] - test['Close']
    test['C-L'] = test['Close'] - test['Low']
    test['H-Ht-1'] = test['High'] - test['High'].shift(1)
    test['L-Lt-1'] = test['Low'] - test['Low'].shift(1)
    test.dropna(inplace=True)

    test['Predicted'] = test['Close'] + \
                        test['H-C'] * model.coef_[0][0] + \
                        test['C-L'] * model.coef_[0][1] + \
                        test['H-Ht-1'] * model.coef_[0][2] + \
                        test['L-Lt-1'] * model.coef_[0][3]

    test['Entry'] = np.where(test['Predicted'] > test['Predicted'].shift(1), test['Close'], 0)
    test['Exit'] = np.where((test['Entry'] != 0) & (test['Open'].shift(-1) < test['Close']), 
                             test['Open'].shift(-1), 0)

    test['Exit'] = np.where((test['Entry'] != 0) & (test['Open'].shift(-1) > test['Close']), 
                             test['Close'].shift(-1), test['Exit'])

    test['P&L_LR'] = test['Exit'] - test['Entry']
    test['Equity curve LR'] = test['P&L_LR'].cumsum() + int(test['Close'][0])

    return test

def logistic_regression(train, test):
    train['C-L > H-C'] = np.where((train['Close'] - train['Low']) > (train['High'] - train['Close']), 1, 0)
    train['H > Ht-1'] = np.where(train['High'] > train['High'].shift(1), 1, 0)

    x_train = train[['C-L > H-C', 'H > Ht-1']]
    y_train = train['Close'].shift(-1)

    model = LogisticRegression()
    model.fit(x_train, y_train)

    test['C-L > H-C'] = np.where((test['Close'] - test['Low']) > (test['High'] - test['Close']), 1, 0)
    test['H > Ht-1'] = np.where(test['High'] > test['High'].shift(1), 1, 0)

    x_test = test[['C-L > H-C', 'H > Ht-1']]
    test['Predicted'] = model.predict(x_test)

    return test

def should_buy_lr(current_price, previous_high, previous_low, current_volume, average_volume):
    # Example condition for buying using Linear Regression strategy
    if current_price > previous_high and current_volume > average_volume:
        return True
    return False

def should_sell_lr(current_price, previous_high, previous_low, current_volume, average_volume):
    # Example condition for selling using Linear Regression strategy
    if current_price < previous_low and current_volume > average_volume:
        return True
    return False

def should_buy_lg(current_price, previous_high, previous_low, current_volume, average_volume):
    # Example condition for buying using Logistic Regression strategy
    if current_price > previous_high and current_volume > average_volume:
        return True
    return False

def should_sell_lg(current_price, previous_high, previous_low, current_volume, average_volume):
    # Example condition for selling using Logistic Regression strategy
    if current_price < previous_low and current_volume > average_volume:
        return True
    return False
