import requests
import json
import time
from datetime import datetime

# Live server URL
BASE_URL = "https://server-for-payment.onrender.com"

class TestLiveServer:
    """Integration tests for the live deployed server"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
    
    def test_login_new_user(self):
        """Test login with a new user"""
        print("\n[TEST] Login new user...")
        username = f"test_user_{int(time.time())}"
        payload = {
            'username': username,
            'public_key': f'{username}_key_123'
        }
        
        try:
            response = self.session.post(f'{self.base_url}/login', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['status'] == 'success', "Status should be 'success'"
            assert data['balance'] == 1000.0, "New user should have 1000 coins"
            print("✓ PASSED: New user login successful")
            return username
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
            return None
    
    def test_login_existing_user(self, username):
        """Test login with existing user"""
        print(f"\n[TEST] Login existing user ({username})...")
        payload = {
            'username': username,
            'public_key': f'{username}_key_123'
        }
        
        try:
            response = self.session.post(f'{self.base_url}/login', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['status'] == 'success', "Status should be 'success'"
            print("✓ PASSED: Existing user login successful")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_sync_single_transaction(self):
        """Test syncing a single transaction"""
        print("\n[TEST] Sync single transaction...")
        
        # Create two users
        sender = f"sender_{int(time.time())}"
        receiver = f"receiver_{int(time.time())}"
        
        self.session.post(f'{self.base_url}/login', 
            json={'username': sender, 'public_key': f'{sender}_key'})
        self.session.post(f'{self.base_url}/login', 
            json={'username': receiver, 'public_key': f'{receiver}_key'})
        
        # Sync transaction
        payload = {
            'username': sender,
            'transactions': [
                {
                    'id': f'tx_{int(time.time())}',
                    'sender': sender,
                    'receiver': receiver,
                    'amount': '100',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        try:
            response = self.session.post(f'{self.base_url}/sync', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['status'] == 'synced', "Status should be 'synced'"
            assert data['processed_count'] == 1, "Should process 1 transaction"
            assert data['new_balance'] == 900.0, f"Sender balance should be 900, got {data['new_balance']}"
            print("✓ PASSED: Single transaction sync successful")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_sync_multiple_transactions(self):
        """Test syncing multiple transactions"""
        print("\n[TEST] Sync multiple transactions...")
        
        # Create three users
        timestamp = int(time.time())
        sender = f"sender_multi_{timestamp}"
        receiver1 = f"receiver1_multi_{timestamp}"
        receiver2 = f"receiver2_multi_{timestamp}"
        
        self.session.post(f'{self.base_url}/login', 
            json={'username': sender, 'public_key': f'{sender}_key'})
        self.session.post(f'{self.base_url}/login', 
            json={'username': receiver1, 'public_key': f'{receiver1}_key'})
        self.session.post(f'{self.base_url}/login', 
            json={'username': receiver2, 'public_key': f'{receiver2}_key'})
        
        # Sync multiple transactions
        payload = {
            'username': sender,
            'transactions': [
                {
                    'id': f'tx_multi_001_{timestamp}',
                    'sender': sender,
                    'receiver': receiver1,
                    'amount': '50',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'id': f'tx_multi_002_{timestamp}',
                    'sender': sender,
                    'receiver': receiver2,
                    'amount': '75',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        try:
            response = self.session.post(f'{self.base_url}/sync', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['processed_count'] == 2, "Should process 2 transactions"
            assert data['new_balance'] == 875.0, f"Sender balance should be 875, got {data['new_balance']}"
            print("✓ PASSED: Multiple transaction sync successful")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_sync_duplicate_prevention(self):
        """Test that duplicate transactions are not processed twice"""
        print("\n[TEST] Duplicate transaction prevention...")
        
        # Create two users
        timestamp = int(time.time())
        sender = f"sender_dup_{timestamp}"
        receiver = f"receiver_dup_{timestamp}"
        tx_id = f"tx_dup_{timestamp}"
        
        self.session.post(f'{self.base_url}/login', 
            json={'username': sender, 'public_key': f'{sender}_key'})
        self.session.post(f'{self.base_url}/login', 
            json={'username': receiver, 'public_key': f'{receiver}_key'})
        
        # First sync
        payload = {
            'username': sender,
            'transactions': [
                {
                    'id': tx_id,
                    'sender': sender,
                    'receiver': receiver,
                    'amount': '100',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        response1 = self.session.post(f'{self.base_url}/sync', json=payload)
        data1 = response1.json()
        print(f"First sync response: {json.dumps(data1, indent=2)}")
        
        # Second sync with same transaction
        try:
            response2 = self.session.post(f'{self.base_url}/sync', json=payload)
            print(f"Status Code: {response2.status_code}")
            data2 = response2.json()
            print(f"Second sync response: {json.dumps(data2, indent=2)}")
            
            assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
            assert data2['processed_count'] == 0, "Duplicate should not be processed"
            print("✓ PASSED: Duplicate transaction prevention working")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_sync_to_unknown_receiver(self):
        """Test sending to unknown receiver (should create ghost account)"""
        print("\n[TEST] Transaction to unknown receiver...")
        
        timestamp = int(time.time())
        sender = f"sender_ghost_{timestamp}"
        receiver = f"receiver_ghost_{timestamp}"
        
        self.session.post(f'{self.base_url}/login', 
            json={'username': sender, 'public_key': f'{sender}_key'})
        
        # Send to unknown receiver (don't create their account first)
        payload = {
            'username': sender,
            'transactions': [
                {
                    'id': f'tx_ghost_{timestamp}',
                    'sender': sender,
                    'receiver': receiver,
                    'amount': '200',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }
        
        try:
            response = self.session.post(f'{self.base_url}/sync', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['processed_count'] == 1, "Transaction should be processed"
            assert data['new_balance'] == 800.0, f"Sender balance should be 800, got {data['new_balance']}"
            print("✓ PASSED: Transaction to unknown receiver processed (ghost account created)")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_empty_transaction_list(self):
        """Test syncing with empty transaction list"""
        print("\n[TEST] Empty transaction list...")
        
        username = f"test_empty_{int(time.time())}"
        self.session.post(f'{self.base_url}/login', 
            json={'username': username, 'public_key': f'{username}_key'})
        
        payload = {
            'username': username,
            'transactions': []
        }
        
        try:
            response = self.session.post(f'{self.base_url}/sync', json=payload)
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert data['processed_count'] == 0, "Should process 0 transactions"
            assert data['new_balance'] == 1000.0, "Balance should be 1000"
            print("✓ PASSED: Empty transaction list handled correctly")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        print("\n[TEST] Server connectivity...")
        try:
            response = self.session.get(self.base_url)
            print(f"Status Code: {response.status_code}")
            print(f"Server is accessible: {response.status_code in [200, 404, 405]}")
            print("✓ PASSED: Server is reachable")
        except requests.exceptions.ConnectionError:
            print("✗ FAILED: Cannot connect to server")
        except Exception as e:
            print(f"✗ FAILED: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("LIVE SERVER INTEGRATION TESTS")
        print(f"Server: {self.base_url}")
        print("=" * 60)
        
        self.test_server_connectivity()
        
        # Test login
        username = self.test_login_new_user()
        if username:
            self.test_login_existing_user(username)
        
        # Test sync operations
        self.test_sync_single_transaction()
        self.test_sync_multiple_transactions()
        self.test_sync_duplicate_prevention()
        self.test_sync_to_unknown_receiver()
        self.test_empty_transaction_list()
        
        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)


if __name__ == '__main__':
    tester = TestLiveServer()
    tester.run_all_tests()
