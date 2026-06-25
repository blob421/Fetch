import hmac, hashlib, time, json, requests

def get_signed_uri(secret_key, qs):
    timestamp = str(int(time.time() * 1000))

    # append timestamp to the query string BEFORE signing
    full_qs = qs + "&timestamp=" + timestamp

    signature = hmac.new(
        secret_key.encode(),
        full_qs.encode(),
        hashlib.sha256
    ).hexdigest()

    full_qs += f'&signature={signature}'
    return full_qs



def get_headers(body, secret, key):

    timestamp, signature = sign_post(key, secret, body)
    return {
            "ApiKey": key,
            "Request-Time": timestamp,
            "Signature": signature,
            "Content-Type": "application/json"
                }



def sign_post(api_key, secret_key, body_dict):
    timestamp = str(int(time.time() * 1000))

    # JSON string EXACTLY as sent
    json_str = json.dumps(body_dict, separators=(',', ':'))

    target = api_key + timestamp + json_str

    signature = hmac.new(
        secret_key.encode(),
        target.encode(),
        hashlib.sha256
    ).hexdigest()

    return timestamp, signature



def get_price_spot():
    try:
        res = requests.get('https://api.mexc.com/api/v3/ticker/price?symbol=BTCUSDT')
        if res.ok:
            j_son = res.json()
            price = j_son.get('price', None)
        
            return price
        
        else:
           return None
        
    except requests.exceptions.RequestException as e:
                    
        return None
    


def get_price_futures(close=False):
    try:
     
        res = requests.get('https://api.mexc.com/api/v1/contract/ticker?symbol=BTC_USDT')

        j_son = res.json()
        data = j_son.get('data', {})
        bid1 = float(data.get("bid1"))
        ask1 = float(data.get("ask1"))

        price = bid1 if not close else ask1
        success = j_son.get('success', None)
        
    
        if not success :
            return None
         
        else:
            return price 

    except requests.exceptions.RequestException:
        return None



def create_futures_order(side, price, secret_key, api_key):
    try:
        ### 3.22 usdc per contracts , 6 contracts 19.2 usdc
        body = {'symbol': 'BTC_USDT', 'vol': 1,  'price': price , 
                'side': side, 'type': 1, 'openType': 1, 'leverage': 2, 
                'stopLossPrice': price * 0.95 , 'takeProfitPrice' : price * 1.05}
        
        json_str = json.dumps(body, separators=(',', ':'))

        headers = get_headers(body, secret_key, api_key)

        res = requests.post('https://api.mexc.com/api/v1/private/order/create', headers=headers, 
                            data=json_str)
        data = res.json()
    
        
        success = data.get('success', None)

        if success :
         
            order_id = data.get('data', {}).get('orderId', None)
            
            return order_id, data
        else:
           return None, data

    except requests.exceptions.RequestException as e:
        return None, None



def close_futures_order(secret_key, api_key, order_id):
    try: 
        body = {}
        headers = get_headers(body, secret_key, api_key)
        json_str = json.dumps(body, separators=(',', ':'))
        res = requests.post('https://api.mexc.com/api/v1/private/position/close_all', 
                            headers=headers, data=json_str)
        success = res.json().get('success', False)

        if success: 
            return success 
        
        else:
            try:
                body = [order_id]
                headers = get_headers(body , secret_key, api_key)
                json_str = json.dumps(body, separators=(',', ':'))
                res = requests.post('/api/v1/private/order/cancel' ,data=json_str, headers=headers)
                success = res.json().get('success', None)

                if success:
                   return success
                else:
                   return False

            except requests.exceptions.RequestException as e:
                return None

    except requests.exceptions.RequestException as e:
        print(f'\nThere was an error closing all orders : {e}\n')
        return None



def handle_spot_order(secret_key, api_key, close, order_id, price, qty=None):
    try:    
        
        p_side = 'SELL' if close else "BUY"
        
        price = float(price) - 25 if close else float(price) + 25

        qty = round(155 / float(price), 4) if not close else qty

        qs = f'symbol=BTCUSDT&side={p_side}&type=LIMIT&quantity={qty}&price={price}'
        full_qs = get_signed_uri(secret_key, qs)
        
        base_url = 'https://api.mexc.com/api/v3/order?'

        
        res = requests.post(base_url + full_qs, headers={"X-MEXC-APIKEY": api_key})
        data = res.json()

        if res.ok :
            if not close:
                order_id = data.get('orderId', None)
                
                return order_id, qty, data
            else:
                return True
        else:      
            return None , None, None if not close else False
         

    except requests.exceptions.RequestException:
        return None , None, None if not close else None
    
