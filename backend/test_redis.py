import redis

# Connect to Redis
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# Test connection
try:
    r.ping()
    print("[SUCCESS] Redis connection successful!")
    
    # Test set/get
    r.set('test_key', 'Hello Redis!')
    value = r.get('test_key')
    print(f"[SUCCESS] Test value: {value}")
    
    # Test delete
    r.delete('test_key')
    print("[SUCCESS] Redis is working correctly!")
    
except Exception as e:
    print(f"[ERROR] Redis connection failed: {str(e)}")