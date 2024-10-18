from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
from datetime import date, timedelta
from smartapi.smartConnect import SmartConnect  # Corrected import
from golden_strategies import should_buy_lr, should_sell_lr, should_buy_lg, should_sell_lg
import os

app = Flask(__name__)

# Initialize and get symbol token information
def initializeSymbolTokenMap():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    token_df = pd.DataFrame.from_dict(requests.get(url).json())
    token_df['expiry'] = pd.to_datetime(token_df['expiry'])
    token_df = token_df.astype({'strike': 'float'})
    return token_df

def getTokenInfo(exch_seg, instrumenttype, symbol, strike_price, pe_ce):
    token_df = initializeSymbolTokenMap()
    strike_price = strike_price * 100
    if exch_seg == 'NFO' and (instrumenttype == 'OPTSTK' or instrumenttype == 'OPTIDX'):
        return token_df[(token_df['exch_seg'] == 'NFO') & (token_df['instrumenttype'] == instrumenttype) &
                        (token_df['name'] == symbol) & (token_df['strike'] == strike_price) &
                        (token_df['symbol'] == pe_ce)]
    return token_df[token_df['exch_seg'] == 'NFO']

def getCandleData(obj, symbolInfo):
    try:
        historicParam = {
            "exchange": symbolInfo['exch_seg'],
            "symboltoken": symbolInfo['token'],
            "interval": "FIVE_MINUTE",
            "fromdate": f'{date.today() - timedelta(90)} 09:15',
            "todate": f'{date.today() - timedelta(1)} 15:30'
        }
        res_json = obj.getCandleData(historicParam)
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        cd = pd.DataFrame(res_json['data'], columns=columns)
        cd['timestamp'] = pd.to_datetime(cd['timestamp'], format='%Y-%m-%d %H:%M:%S')
        cd['symbol'] = symbolInfo['symbol']
        cd['expiry'] = symbolInfo['expiry']
        print(f"Done for {symbolInfo['symbol']}")
        return cd
    except Exception as e:
        print(f"Historic API failed for {symbolInfo['symbol']}: {e}")
        return pd.DataFrame()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    api_key = data.get('api_key')
    username = data.get('username')
    password = data.get('password')

    try:
        # Initialize SmartConnect and create session
        obj = SmartConnect(api_key=api_key)
        session_data = obj.generateSession(username, password)
        refresh_token = session_data['data']['refreshToken']

        # Fetch the feed token and user profile
        feedToken = obj.getfeedToken()
        userProfile = obj.getProfile(refresh_token)

        return jsonify({
            "message": "Login successful",
            "refresh_token": refresh_token,
            "feed_token": feedToken,
            "user_profile": userProfile
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Login failed",
            "error": str(e)
        }), 500

@app.route('/get_symbol_data', methods=['POST'])
def get_symbol_data():
    data = request.json
    symbol = data.get('symbol')
    strike_price = data.get('strike_price')
    pe_ce = data.get('pe_ce')

    try:
        tokenInfo = getTokenInfo('NFO', 'OPTIDX', symbol, strike_price, pe_ce).iloc[0]
        return jsonify(tokenInfo.to_dict()), 200

    except Exception as e:
        return jsonify({
            "message": "Error fetching symbol data",
            "error": str(e)
        }), 500

@app.route('/get_candle_data', methods=['POST'])
def get_candle_data():
    data = request.json
    api_key = data.get('api_key')
    refresh_token = data.get('refresh_token')
    symbol_info = data.get('symbol_info')

    try:
        obj = SmartConnect(api_key=api_key)
        obj.generateSessionWithRefreshToken(refresh_token)
        
        candle_data = getCandleData(obj, symbol_info)
        return candle_data.to_json(orient='records'), 200

    except Exception as e:
        return jsonify({
            "message": "Error fetching candle data",
            "error": str(e)
        }), 500

@app.route('/take_order', methods=['POST'])
def take_order():
    data = request.json
    current_price = data.get('current_price')
    previous_high = data.get('previous_high')
    previous_low = data.get('previous_low')
    current_volume = data.get('current_volume')
    average_volume = data.get('average_volume')

    try:
        # Check conditions for Golden Strategies
        if should_buy_lr(current_price, previous_high, previous_low, current_volume, average_volume):
            place_order('BUY', current_price)  # Integrate with your trading API
            return jsonify({"message": "Buy order placed using LR strategy"}), 200

        if should_sell_lr(current_price, previous_high, previous_low, current_volume, average_volume):
            place_order('SELL', current_price)  # Integrate with your trading API
            return jsonify({"message": "Sell order placed using LR strategy"}), 200

        if should_buy_lg(current_price, previous_high, previous_low, current_volume, average_volume):
            place_order('BUY', current_price)  # Integrate with your trading API
            return jsonify({"message": "Buy order placed using LG strategy"}), 200

        if should_sell_lg(current_price, previous_high, previous_low, current_volume, average_volume):
            place_order('SELL', current_price)  # Integrate with your trading API
            return jsonify({"message": "Sell order placed using LG strategy"}), 200

        return jsonify({"message": "No trade executed"}), 200

    except Exception as e:
        return jsonify({
            "message": "Error in taking order",
            "error": str(e)
        }), 500

def place_order(order_type, price):
    # Placeholder for actual trading API integration
    print(f"Placing {order_type} order at {price}")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # For deployment environments
    app.run(debug=True, host='0.0.0.0', port=port)
