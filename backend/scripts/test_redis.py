import redis
import sys

def test_redis_connection():
    try:
        r = redis.Redis(host='redis', port=6379, db=0)
        r.ping()
        print("Successfully connected to Redis!")
        return True
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1) 