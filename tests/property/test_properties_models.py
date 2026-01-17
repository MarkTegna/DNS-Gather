"""Property-based tests for data models"""

import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timedelta

from dns_gather.models import ZoneInfo, DNSRecord, ApplicationState


# Strategies for generating test data
zone_types = st.sampled_from(['Primary', 'Secondary', 'Stub', 'Unknown'])
transfer_statuses = st.sampled_from(['Success', 'Denied', 'Failed', 'Pending'])
record_types = st.sampled_from(['A', 'AAAA', 'CNAME', 'MX', 'NS', 'SOA', 'TXT', 'PTR', 'SRV'])


@st.composite
def zone_info_strategy(draw):
    """Generate random ZoneInfo instances"""
    return ZoneInfo(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-'))),
        zone_type=draw(zone_types),
        serial=draw(st.integers(min_value=1, max_value=2147483647)),
        transfer_status=draw(transfer_statuses),
        record_count=draw(st.integers(min_value=0, max_value=10000)),
        error_message=draw(st.text(max_size=200))
    )


@st.composite
def dns_record_strategy(draw):
    """Generate random DNSRecord instances"""
    return DNSRecord(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='.-@'))),
        record_type=draw(record_types),
        ttl=draw(st.integers(min_value=0, max_value=86400)),
        data=draw(st.text(min_size=1, max_size=200))
    )


@st.composite
def application_state_strategy(draw):
    """Generate random ApplicationState instances"""
    start = datetime.now()
    duration = draw(st.integers(min_value=1, max_value=3600))
    end = start + timedelta(seconds=duration)
    
    return ApplicationState(
        zones_discovered=draw(st.integers(min_value=0, max_value=100)),
        zones_transferred=draw(st.integers(min_value=0, max_value=100)),
        zones_failed=draw(st.integers(min_value=0, max_value=100)),
        total_records=draw(st.integers(min_value=0, max_value=10000)),
        errors=draw(st.lists(st.text(max_size=100), max_size=10)),
        start_time=start,
        end_time=end
    )


# Feature: dns-zone-exporter, Property: Data model round-trip
@given(zone_info_strategy())
def test_zone_info_to_dict_preserves_data(zone_info):
    """
    For any valid ZoneInfo instance, converting to dict should preserve all key fields
    """
    result = zone_info.to_dict()
    
    # Verify all expected keys are present
    assert 'Zone Name' in result
    assert 'Zone Type' in result
    assert 'Record Count' in result
    assert 'Transfer Status' in result
    assert 'Error Message' in result
    
    # Verify values match
    assert result['Zone Name'] == zone_info.name
    assert result['Zone Type'] == zone_info.zone_type
    assert result['Record Count'] == zone_info.record_count
    assert result['Transfer Status'] == zone_info.transfer_status
    assert result['Error Message'] == zone_info.error_message


# Feature: dns-zone-exporter, Property: Data model round-trip
@given(dns_record_strategy())
def test_dns_record_to_dict_preserves_data(dns_record):
    """
    For any valid DNSRecord instance, converting to dict should preserve all key fields
    """
    result = dns_record.to_dict()
    
    # Verify all expected keys are present
    assert 'Record Name' in result
    assert 'Record Type' in result
    assert 'TTL' in result
    assert 'Data' in result
    
    # Verify values match
    assert result['Record Name'] == dns_record.name
    assert result['Record Type'] == dns_record.record_type
    assert result['TTL'] == dns_record.ttl
    assert result['Data'] == dns_record.data


# Feature: dns-zone-exporter, Property: Data model round-trip
@given(application_state_strategy())
def test_application_state_get_summary_preserves_data(app_state):
    """
    For any valid ApplicationState instance, get_summary should preserve all statistics
    """
    result = app_state.get_summary()
    
    # Verify all expected keys are present
    assert 'zones_discovered' in result
    assert 'zones_transferred' in result
    assert 'zones_failed' in result
    assert 'total_records' in result
    assert 'duration_seconds' in result
    assert 'error_count' in result
    
    # Verify values match
    assert result['zones_discovered'] == app_state.zones_discovered
    assert result['zones_transferred'] == app_state.zones_transferred
    assert result['zones_failed'] == app_state.zones_failed
    assert result['total_records'] == app_state.total_records
    assert result['error_count'] == len(app_state.errors)
    
    # Verify duration is calculated correctly
    expected_duration = (app_state.end_time - app_state.start_time).total_seconds()
    assert abs(result['duration_seconds'] - expected_duration) < 0.001
