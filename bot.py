#!/usr/bin/env python3
"""
Deriv Digit Match Trading Bot
Trades when last digit is 1 and predicts next digit will be 1
"""

import json
import time
import websocket
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DerivDigitBot:
    def __init__(self, api_token, email="your_email@deriv.com"):
        self.api_token = api_token
        self.email = email
        self.ws = None
        self.account_id = None
        self.balance = 0
        self.trade_amount = 10  # Default trade amount
        self.last_digits = {}
        self.trade_count = 0
        
    def connect(self):
        """Connect to Deriv WebSocket"""
        logger.info("Connecting to Deriv...")
        try:
            self.ws = websocket.WebSocketApp(
                "wss://ws.deriv.com/websockets/v3",
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            self.ws.on_open = self.on_open
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"Connection error: {e}")
            
    def on_open(self, ws):
        """Called when WebSocket connection opens"""
        logger.info("Connected to Deriv!")
        
        # Authorize
        auth_msg = {
            "authorize": self.api_token
        }
        ws.send(json.dumps(auth_msg))
        
    def on_message(self, ws, message):
        """Process messages from Deriv"""
        try:
            data = json.loads(message)
            
            # Handle authorization
            if "authorize" in data:
                if data["authorize"].get("status") == "ok":
                    self.account_id = data["authorize"]["account_id"]
                    self.balance = data["authorize"]["balance"]
                    logger.info(f"Authorized! Account: {self.account_id}, Balance: {self.balance}")
                    self.subscribe_to_indices()
                else:
                    logger.error("Authorization failed!")
                    
            # Handle price updates
            elif "tick" in data:
                self.handle_tick(data["tick"])
                
            # Handle trade responses
            elif "buy" in data:
                self.handle_trade_response(data["buy"])
                
        except Exception as e:
            logger.error(f"Message processing error: {e}")
            
    def subscribe_to_indices(self):
        """Subscribe to synthetic indices"""
        # Subscribe to Volatility Index 10, 25, 50, 75, 100
        symbols = ["1s10V", "1s25V", "1s50V", "1s75V", "1s100V"]
        
        for symbol in symbols:
            tick_msg = {
                "ticks": symbol,
                "subscribe": 1
            }
            self.ws.send(json.dumps(tick_msg))
            logger.info(f"Subscribed to {symbol}")
            
    def handle_tick(self, tick_data):
        """Handle price tick - check if last digit is 1"""
        symbol = tick_data.get("symbol")
        quote = tick_data.get("quote")
        
        if not symbol or quote is None:
            return
            
        # Extract last digit from quote
        last_digit = int(str(int(quote * 10)) % 10)
        
        logger.info(f"{symbol}: {quote} - Last digit: {last_digit}")
        
        # Check if last digit is 1
        if last_digit == 1:
            logger.warning(f"🎯 SIGNAL DETECTED: {symbol} has last digit 1!")
            self.place_trade(symbol)
            
    def place_trade(self, symbol):
        """Place a trade predicting digit will be 1"""
        try:
            trade_msg = {
                "buy": 1,
                "subscribe": 1,
                "price": self.trade_amount,
                "parameters": {
                    "amount": self.trade_amount,
                    "barrier": "1",
                    "basis": "stake",
                    "contract_type": "DIGITDIFF",
                    "currency": "USD",
                    "duration": 5,
                    "duration_unit": "t",
                    "symbol": symbol
                }
            }
            
            logger.info(f"📊 Placing trade on {symbol}...")
            self.ws.send(json.dumps(trade_msg))
            self.trade_count += 1
            
        except Exception as e:
            logger.error(f"Trade placement error: {e}")
            
    def handle_trade_response(self, trade_data):
        """Handle trade execution response"""
        if trade_data.get("status") == "ok":
            payout = trade_data.get("payout")
            transaction_id = trade_data.get("transaction_id")
            logger.info(f"✅ Trade placed! ID: {transaction_id}, Potential payout: {payout}")
        else:
            logger.error(f"❌ Trade failed: {trade_data}")
            
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        """Handle connection close"""
        logger.info("Connection closed. Reconnecting in 10 seconds...")
        time.sleep(10)
        self.connect()
        
    def run(self):
        """Start the bot"""
        logger.info("🤖 Deriv Digit Match Bot Started!")
        logger.info(f"Trade Amount: {self.trade_amount} USD")
        logger.info("Scanning all synthetic indices for digit 1 signals...")
        
        self.connect()

if __name__ == "__main__":
    # Get API token from environment or config
    API_TOKEN = input("Enter your Deriv API token: ")
    
    bot = DerivDigitBot(API_TOKEN)
    bot.run()
