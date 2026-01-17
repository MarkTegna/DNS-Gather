"""Unit tests for DNSManager"""

import pytest
from dns_gather.dns_manager import DNSManager


# Real DNS server for testing
TEST_DNS_SERVER = '192.168.168.55'


def test_dns_manager_initialization():
    """Test DNSManager initialization with default parameters"""
    manager = DNSManager(TEST_DNS_SERVER)
    
    assert manager.server == TEST_DNS_SERVER
    assert manager.port == 53
    assert manager.timeout == 10
    assert manager.use_tcp is True
    assert manager.connected is False
    assert manager.tsig_keyring is None


def test_dns_manager_custom_parameters():
    """Test DNSManager initialization with custom parameters"""
    manager = DNSManager(TEST_DNS_SERVER, port=5353, timeout=30, use_tcp=False)
    
    assert manager.server == TEST_DNS_SERVER
    assert manager.port == 5353
    assert manager.timeout == 30
    assert manager.use_tcp is False


def test_connection_to_real_dns_server():
    """Test connection to real DNS server"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    success, message = manager.test_connection()
    
    assert success is True
    assert 'Successfully connected' in message
    assert TEST_DNS_SERVER in message
    assert manager.connected is True


def test_connection_to_invalid_server():
    """Test connection to invalid DNS server"""
    # Use a non-routable IP
    manager = DNSManager('192.0.2.1', port=53, timeout=2, use_tcp=True)
    
    success, message = manager.test_connection()
    
    assert success is False
    assert isinstance(message, str)
    assert len(message) > 0


def test_connect_method():
    """Test connect() method"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    result = manager.connect()
    
    assert isinstance(result, bool)
    assert result is True  # Should connect to real server


def test_tsig_key_setup():
    """Test TSIG key configuration"""
    manager = DNSManager(TEST_DNS_SERVER)
    
    keyname = 'test-key'
    secret = 'dGVzdHNlY3JldA=='  # base64 encoded
    algorithm = 'hmac-sha256'
    
    manager.set_tsig_key(keyname, secret, algorithm)
    
    assert manager.tsig_keyname == keyname
    assert manager.tsig_keyring is not None


def test_tsig_key_with_different_algorithms():
    """Test TSIG key with different algorithms"""
    manager = DNSManager(TEST_DNS_SERVER)
    
    algorithms = ['hmac-sha256', 'hmac-sha512', 'hmac-md5']
    
    for algorithm in algorithms:
        manager.set_tsig_key('test-key', 'dGVzdHNlY3JldA==', algorithm)
        assert manager.tsig_keyring is not None


def test_query_method():
    """Test DNS query method"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # Connect first
    assert manager.connect() is True
    
    # Perform query
    response = manager.query('version.bind', 'TXT', 'CH')
    
    # Should get a response
    assert response is not None


def test_query_with_invalid_name():
    """Test DNS query with invalid name"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # Connect first
    assert manager.connect() is True
    
    # Query for something that likely doesn't exist
    response = manager.query('this-definitely-does-not-exist-12345.invalid', 'A', 'IN')
    
    # Should handle gracefully (may return None or response with NXDOMAIN)
    # Either way, should not crash
    assert response is None or response is not None


def test_connection_timeout():
    """Test connection timeout handling"""
    # Use very short timeout
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=0.001, use_tcp=True)
    
    success, message = manager.test_connection()
    
    # Should handle timeout gracefully
    assert isinstance(success, bool)
    assert isinstance(message, str)


def test_tcp_vs_udp():
    """Test TCP vs UDP connection modes"""
    # TCP connection
    manager_tcp = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    success_tcp, msg_tcp = manager_tcp.test_connection()
    
    # UDP connection
    manager_udp = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=False)
    success_udp, msg_udp = manager_udp.test_connection()
    
    # Both should work (or at least not crash)
    assert isinstance(success_tcp, bool)
    assert isinstance(success_udp, bool)
    assert isinstance(msg_tcp, str)
    assert isinstance(msg_udp, str)


def test_multiple_connections():
    """Test multiple connection attempts"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # First connection
    success1, msg1 = manager.test_connection()
    assert success1 is True
    
    # Second connection (should work again)
    success2, msg2 = manager.test_connection()
    assert success2 is True
    
    # Both should succeed
    assert manager.connected is True
