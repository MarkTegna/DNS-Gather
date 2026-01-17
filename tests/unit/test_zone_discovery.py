"""Unit tests for ZoneDiscovery"""

import pytest
from dns_gather.dns_manager import DNSManager
from dns_gather.zone_discovery import ZoneDiscovery
from dns_gather.models import ZoneInfo


TEST_DNS_SERVER = '192.168.168.55'


def test_zone_discovery_initialization():
    """Test ZoneDiscovery initialization"""
    manager = DNSManager(TEST_DNS_SERVER)
    discovery = ZoneDiscovery(manager)
    
    assert discovery.dns_manager == manager


def test_enumerate_zones_returns_list():
    """Test that enumerate_zones returns a list"""
    manager = DNSManager(TEST_DNS_SERVER)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zones = discovery.enumerate_zones()
    
    assert isinstance(zones, list)


def test_get_zone_metadata():
    """Test getting zone metadata"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_info = discovery.get_zone_metadata('example.com')
    
    assert isinstance(zone_info, ZoneInfo)
    assert zone_info.name == 'example.com'
    assert isinstance(zone_info.zone_type, str)
    assert isinstance(zone_info.serial, int)
    assert isinstance(zone_info.transfer_status, str)


def test_discover_zones_from_empty_list():
    """Test discovering zones from empty list"""
    manager = DNSManager(TEST_DNS_SERVER)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zones = discovery.discover_zones_from_list([])
    
    assert isinstance(zones, list)
    assert len(zones) == 0


def test_discover_zones_from_list():
    """Test discovering zones from a list"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_names = ['example.com', 'test.local']
    zones = discovery.discover_zones_from_list(zone_names)
    
    assert isinstance(zones, list)
    assert len(zones) == len(zone_names)
    
    for i, zone in enumerate(zones):
        assert isinstance(zone, ZoneInfo)
        assert zone.name == zone_names[i]


def test_discover_zones_handles_invalid_zone():
    """Test that discovery handles invalid zones gracefully"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_names = ['this-does-not-exist-12345.invalid']
    zones = discovery.discover_zones_from_list(zone_names)
    
    assert len(zones) == 1
    assert isinstance(zones[0], ZoneInfo)
    # Should have some status even if it failed
    assert zones[0].transfer_status in ['Pending', 'Failed']


def test_discover_zones_continues_after_error():
    """Test that discovery continues after encountering an error"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_names = ['invalid1.test', 'invalid2.test', 'invalid3.test']
    zones = discovery.discover_zones_from_list(zone_names)
    
    # Should return all zones even if they all failed
    assert len(zones) == len(zone_names)
    
    for zone in zones:
        assert isinstance(zone, ZoneInfo)


def test_zone_metadata_includes_all_fields():
    """Test that zone metadata includes all required fields"""
    manager = DNSManager(TEST_DNS_SERVER, port=53, timeout=10, use_tcp=True)
    manager.connect()
    
    discovery = ZoneDiscovery(manager)
    zone_info = discovery.get_zone_metadata('test.com')
    
    # Check all required fields exist
    assert hasattr(zone_info, 'name')
    assert hasattr(zone_info, 'zone_type')
    assert hasattr(zone_info, 'serial')
    assert hasattr(zone_info, 'transfer_status')
    assert hasattr(zone_info, 'record_count')
    assert hasattr(zone_info, 'error_message')
