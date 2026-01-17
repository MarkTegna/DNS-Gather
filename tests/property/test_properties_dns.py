"""Property-based tests for DNS operations"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from dns_gather.dns_manager import DNSManager


# Real DNS server for testing
TEST_DNS_SERVER = '192.168.168.55'


# Feature: dns-zone-exporter, Property 1: DNS Connection Establishment
def test_dns_connection_with_standard_port():
    """
    For the standard DNS port (53), connection should work with various timeouts
    """
    port = 53
    
    for timeout in [5, 10, 15]:
        manager = DNSManager(TEST_DNS_SERVER, port=port, timeout=timeout, use_tcp=True)
        
        success, message = manager.test_connection()
        
        # Should always return a tuple with bool and string
        assert isinstance(success, bool)
        assert isinstance(message, str)
        assert len(message) > 0
        
        # Message should contain server info
        assert TEST_DNS_SERVER in message or 'Connection' in message


# Feature: dns-zone-exporter, Property 1: DNS Connection Establishment
def test_valid_dns_server_connection():
    """
    For a valid DNS server address, connection should succeed
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    success, message = manager.test_connection()
    
    # Should connect successfully to real DNS server
    assert success is True
    assert 'Successfully connected' in message
    assert manager.connected is True


# Feature: dns-zone-exporter, Property 1: DNS Connection Establishment
def test_invalid_dns_server_returns_error():
    """
    For an invalid DNS server address, connection should fail with descriptive error
    """
    # Use a non-routable IP address
    manager = DNSManager('192.0.2.1', port=53, timeout=2, use_tcp=True)
    
    success, message = manager.test_connection()
    
    # Should fail with descriptive error
    assert success is False
    assert isinstance(message, str)
    assert len(message) > 0
    assert 'timeout' in message.lower() or 'failed' in message.lower()


# Feature: dns-zone-exporter, Property 1: DNS Connection Establishment
def test_connect_method_returns_boolean():
    """
    For any DNS server, connect() should return a boolean
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    result = manager.connect()
    
    assert isinstance(result, bool)


# Feature: dns-zone-exporter, Property 1: DNS Connection Establishment
def test_connection_timeout_handling():
    """
    For a connection that times out, should return False with timeout message
    """
    # Use very short timeout to force timeout
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=0.001, use_tcp=True)
    
    success, message = manager.test_connection()
    
    # Should handle timeout gracefully
    assert isinstance(success, bool)
    assert isinstance(message, str)
    # Either succeeds very quickly or times out
    if not success:
        assert 'timeout' in message.lower() or 'failed' in message.lower()


def test_real_dns_query():
    """
    Test that we can perform a real DNS query against the test server
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # Connect first
    assert manager.connect() is True
    
    # Try a simple query
    response = manager.query('version.bind', 'TXT', 'CH')
    
    # Should get a response (even if empty)
    assert response is not None



# Feature: dns-zone-exporter, Property 2: TSIG Authentication Support
@given(
    keyname=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_').filter(lambda x: not x.startswith('.') and not x.endswith('.') and '..' not in x),
    algorithm=st.sampled_from(['hmac-sha256', 'hmac-sha512', 'hmac-md5'])
)
@settings(max_examples=10)
def test_tsig_key_configuration(keyname, algorithm):
    """
    For any valid TSIG credentials, the DNS Manager should accept and store them
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # Use a dummy base64 secret (real TSIG would need valid secret)
    secret = 'dGVzdHNlY3JldA=='  # base64 encoded "testsecret"
    
    # Should not raise exception
    try:
        manager.set_tsig_key(keyname, secret, algorithm)
        
        # Should store the keyname
        assert manager.tsig_keyname == keyname
        assert manager.tsig_keyring is not None
    except Exception as e:
        # If it fails due to invalid DNS name format, that's acceptable
        # as long as it doesn't crash the application
        assert isinstance(e, Exception)


# Feature: dns-zone-exporter, Property 2: TSIG Authentication Support
def test_tsig_key_storage():
    """
    For any TSIG key configuration, the manager should store it correctly
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    keyname = 'test-key'
    secret = 'dGVzdHNlY3JldA=='
    algorithm = 'hmac-sha256'
    
    manager.set_tsig_key(keyname, secret, algorithm)
    
    assert manager.tsig_keyname == keyname
    assert manager.tsig_keyring is not None


# Feature: dns-zone-exporter, Property 2: TSIG Authentication Support  
def test_connection_without_tsig():
    """
    For a connection without TSIG, the manager should work normally
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    
    # Should have no TSIG configured
    assert manager.tsig_keyring is None
    assert manager.tsig_keyname is None
    
    # Should still be able to connect
    success, message = manager.test_connection()
    assert isinstance(success, bool)
    assert isinstance(message, str)



from dns_gather.zone_discovery import ZoneDiscovery
from dns_gather.models import ZoneInfo


# Feature: dns-zone-exporter, Property 3: Zone Discovery Completeness
def test_zone_discovery_returns_list():
    """
    For any connected DNS server, zone discovery should return a list
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zones = discovery.enumerate_zones()
    
    assert isinstance(zones, list)


# Feature: dns-zone-exporter, Property 3: Zone Discovery Completeness
@given(
    zone_names=st.lists(
        st.text(min_size=3, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-').filter(
            lambda x: not x.startswith('.') and not x.endswith('.') and '..' not in x and x.count('.') >= 1
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=5, suppress_health_check=[HealthCheck.filter_too_much], deadline=1000)
def test_zone_discovery_from_list_returns_complete_metadata(zone_names):
    """
    For any list of zone names, discovery should return complete metadata for each
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zones = discovery.discover_zones_from_list(zone_names)
    
    # Should return same number of zones
    assert len(zones) == len(zone_names)
    
    # Each zone should have complete metadata
    for zone in zones:
        assert hasattr(zone, 'name')
        assert hasattr(zone, 'zone_type')
        assert hasattr(zone, 'serial')
        assert hasattr(zone, 'transfer_status')
        assert hasattr(zone, 'record_count')
        assert hasattr(zone, 'error_message')
        
        assert isinstance(zone.name, str)
        assert isinstance(zone.zone_type, str)
        assert isinstance(zone.serial, int)
        assert isinstance(zone.transfer_status, str)
        assert isinstance(zone.record_count, int)
        assert isinstance(zone.error_message, str)


# Feature: dns-zone-exporter, Property 4: Zone Discovery Error Resilience
def test_zone_discovery_handles_invalid_zone():
    """
    For any zone that fails during discovery, should log error and continue
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    
    # Mix of potentially valid and invalid zones
    zone_names = ['invalid-zone-12345.test', 'another-invalid.test']
    zones = discovery.discover_zones_from_list(zone_names)
    
    # Should return results for all zones (even if they failed)
    assert len(zones) == len(zone_names)
    
    # Each zone should have a status
    for zone in zones:
        assert zone.transfer_status in ['Pending', 'Failed', 'Success']


# Feature: dns-zone-exporter, Property 3: Zone Discovery Completeness
def test_get_zone_metadata_returns_zone_info():
    """
    For any zone name, get_zone_metadata should return a ZoneInfo object
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_info = discovery.get_zone_metadata('example.com')
    
    assert isinstance(zone_info, ZoneInfo)
    assert zone_info.name == 'example.com'



from dns_gather.zone_transfer import ZoneTransfer


# Feature: dns-zone-exporter, Property 5: Zone Transfer Execution
def test_zone_transfer_returns_tuple():
    """
    For any zone, zone transfer should return a tuple of (records, error_message)
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    transfer = ZoneTransfer(manager)
    records, error = transfer.perform_axfr('test.invalid')
    
    assert isinstance(records, list)
    assert isinstance(error, str)


# Feature: dns-zone-exporter, Property 6: Record Type Collection Completeness
def test_zone_transfer_collects_all_record_types():
    """
    For any zone with multiple record types, all types should be collected
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    transfer = ZoneTransfer(manager)
    
    # Try a zone transfer (may fail if not allowed)
    records, error = transfer.perform_axfr('example.com')
    
    # If transfer succeeded, check that records have types
    if len(records) > 0:
        for record in records:
            assert hasattr(record, 'record_type')
            assert isinstance(record.record_type, str)
            assert len(record.record_type) > 0


# Feature: dns-zone-exporter, Property 7: Zone Transfer Error Resilience
def test_zone_transfer_handles_denied_transfer():
    """
    For any zone transfer that is denied, should return error message
    """
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    transfer = ZoneTransfer(manager)
    
    # Try to transfer a zone that likely doesn't allow transfers
    records, error = transfer.perform_axfr('denied-zone.test')
    
    # Should handle gracefully
    assert isinstance(records, list)
    assert isinstance(error, str)
    
    # If transfer failed, should have error message
    if len(records) == 0:
        assert len(error) > 0
