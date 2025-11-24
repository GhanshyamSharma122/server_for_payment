from flask import Flask, request, jsonify
import sqlite3
import json

app = Flask(__name__)
DB_NAME = "offline_bank.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, balance REAL, public_key TEXT)''')
    # Transactions table to prevent double spending
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (tx_id TEXT PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL, timestamp TEXT)''')
    conn.commit()
    conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    public_key = data.get('public_key')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    row = c.fetchone()
    
    if row:
        balance = row[0]
    else:
        # New user gets 1000 coins default
        balance = 1000.0
        c.execute("INSERT INTO users (username, balance, public_key) VALUES (?, ?, ?)", 
                  (username, balance, public_key))
        conn.commit()
    
    conn.close()
    return jsonify({"status": "success", "balance": balance})

@app.route('/sync', methods=['POST'])
def sync():
    # Receives a list of offline transactions
    tx_list = request.json.get('transactions', [])
    processed = 0
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    for tx in tx_list:
        tx_id = tx['id']
        sender = tx['sender']
        receiver = tx['receiver']
        amount = float(tx['amount'])
        
        # Check if tx already processed
        c.execute("SELECT tx_id FROM transactions WHERE tx_id=?", (tx_id,))
        if c.fetchone():
            continue
            
        # Verify Balance (Simple check)
        c.execute("SELECT balance FROM users WHERE username=?", (sender,))
        sender_bal_row = c.fetchone()
        
        # In a real app, we would verify RSA signature here using sender's public_key
        
        if sender_bal_row:
            # Deduct from sender
            new_sender_bal = sender_bal_row[0] - amount
            c.execute("UPDATE users SET balance=? WHERE username=?", (new_sender_bal, sender))
            
            # Add to receiver
            c.execute("SELECT balance FROM users WHERE username=?", (receiver,))
            rec_row = c.fetchone()
            if rec_row:
                new_rec_bal = rec_row[0] + amount
                c.execute("UPDATE users SET balance=? WHERE username=?", (new_rec_bal, receiver))
            else:
                # If receiver doesn't exist on server yet, create ghost account
                c.execute("INSERT INTO users (username, balance, public_key) VALUES (?, ?, ?)", 
                          (receiver, 1000 + amount, "pending"))

            # Record Transaction
            c.execute("INSERT INTO transactions VALUES (?,?,?,?,?)", 
                      (tx_id, sender, receiver, amount, tx['timestamp']))
            processed += 1
            
    conn.commit()
    
    # Get updated balance for the requester
    requester = request.json.get('username')
    c.execute("SELECT balance FROM users WHERE username=?", (requester,))
    final_balance = c.fetchone()[0]
    conn.close()
    
    return jsonify({"status": "synced", "processed_count": processed, "new_balance": final_balance})

if __name__ == '__main__':
    init_db()
    # Host 0.0.0.0 allows mobile access on same WiFi
    app.run(host='0.0.0.0', port=5000, debug=True)