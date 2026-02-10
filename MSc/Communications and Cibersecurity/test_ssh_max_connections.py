#!/usr/bin/env python3
"""
Test SSH MaxStartups configuration
Tests if SSH server properly rejects connections beyond MaxStartups limit
"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SSH_HOST = 'ssh'  # Docker service name
SSH_PORT = 22
MAX_EXPECTED = 5  # Expected MaxStartups value
TOTAL_ATTEMPTS = 8  # Try 8 connections (3 more than max)
HOLD_TIME = 10  # Hold connections for 10 seconds

def open_ssh_connection(connection_num):
    """
    Open a TCP connection to SSH server and verify SSH banner
    Returns tuple: (connection_num, success, message)
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        
        # Attempt connection
        start_time = time.time()
        s.connect((SSH_HOST, SSH_PORT))
        connect_time = time.time() - start_time
        
        # Wait for SSH banner (proves connection was not immediately dropped)
        try:
            banner = s.recv(256).decode('utf-8', errors='ignore')
            if 'SSH' not in banner:
                s.close()
                return (connection_num, False, "No SSH banner received - rejected by MaxStartups")
        except socket.timeout:
            s.close()
            return (connection_num, False, "Banner timeout - connection dropped by MaxStartups")
        except Exception as e:
            s.close()
            return (connection_num, False, f"Banner read failed: {str(e)}")
        
        # Connection successful - hold it
        print(f"✅ Connection {connection_num}: Connected in {connect_time:.2f}s (banner: {banner[:20].strip()}...)")
        
        # Keep connection alive to occupy a slot
        time.sleep(HOLD_TIME)
        s.close()
        
        return (connection_num, True, f"Success (held for {HOLD_TIME}s)")
        
    except socket.timeout:
        return (connection_num, False, "Timeout - likely rejected by MaxStartups")
    except ConnectionRefusedError:
        return (connection_num, False, "Connection refused - MaxStartups limit reached")
    except ConnectionResetError:
        return (connection_num, False, "Connection reset by peer - rejected by MaxStartups")
    except Exception as e:
        return (connection_num, False, f"Error: {str(e)}")

def main():
    print("=" * 70)
    print("SSH MaxStartups Test")
    print("=" * 70)
    print(f"Target: {SSH_HOST}:{SSH_PORT}")
    print(f"Expected limit: {MAX_EXPECTED} simultaneous connections")
    print(f"Testing with: {TOTAL_ATTEMPTS} concurrent connection attempts")
    print("=" * 70)
    print()
    
    # Track results
    results = []
    successful = 0
    failed = 0
    
    # Open connections concurrently
    print(f"[{time.strftime('%H:%M:%S')}] Starting {TOTAL_ATTEMPTS} concurrent connections...")
    print()
    
    with ThreadPoolExecutor(max_workers=TOTAL_ATTEMPTS) as executor:
        # Submit all connection attempts
        futures = {
            executor.submit(open_ssh_connection, i): i 
            for i in range(1, TOTAL_ATTEMPTS + 1)
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            conn_num, success, message = future.result()
            results.append((conn_num, success, message))
            
            if success:
                successful += 1
            else:
                failed += 1
                print(f"❌ Connection {conn_num}: {message}")
    
    # Sort results by connection number
    results.sort(key=lambda x: x[0])
    
    # Print summary
    print()
    print("=" * 70)
    print("Test Results")
    print("=" * 70)
    print(f"Total attempts: {TOTAL_ATTEMPTS}")
    print(f"Successful:     {successful}")
    print(f"Failed:         {failed}")
    print()
    
    # Detailed results
    print("Detailed Results:")
    for conn_num, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  Connection {conn_num}: {status} - {message}")
    
    print()
    print("=" * 70)
    
    # Validation
    if successful <= MAX_EXPECTED and failed >= 1:
        print("✅ TEST PASSED: MaxStartups limit is working correctly!")
        print(f"   Expected: ≤{MAX_EXPECTED} connections, Got: {successful} successful")
        print(f"   At least 1 connection was rejected as expected")
    elif successful == TOTAL_ATTEMPTS:
        print("⚠️  TEST FAILED: All connections accepted!")
        print(f"   Expected: max {MAX_EXPECTED} connections")
        print(f"   Got: {successful} connections (no rejections)")
        print()
        print("   Possible issues:")
        print("   - MaxStartups setting not applied")
        print("   - SSH server restarted after config change?")
    else:
        print("⚠️  TEST INCONCLUSIVE")
        print(f"   Expected: {MAX_EXPECTED} successful, {TOTAL_ATTEMPTS - MAX_EXPECTED} rejected")
        print(f"   Got: {successful} successful, {failed} rejected")
    
    print("=" * 70)
    print()
    
    # Return exit code
    return 0 if (successful <= MAX_EXPECTED and failed >= 1) else 1

if __name__ == "__main__":
    exit(main())
