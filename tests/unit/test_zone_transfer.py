"""Unit tests for zone transfer operations"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import dns.zone
import dns.rdataset
import dns.rdatatype
import dns.name
import dns.exception

from dns_gather.zone_transfer import ZoneTransfer
from dns_gather.dns_manager import DNSManager
from dns_gather.models import DNSRecord


@pytest.fixture
def mock_dns_manager():
    """Create a mock DNS manager"""
    manager = Mock(spec=DNSManager)
    manager.server = '192.168.168.55'
    manager.port = 53
    manager.timeout = 10
    manager.tsig_keyring = None
    manager.tsig_keyname = None
    return manager


@pytest.fixture
def zone_transfer(mock_dns_manager):
    """Create a ZoneTransfer instance with mock DNS manager"""
    return ZoneTransfer(mock_dns_manager)


def test_zone_transfer_initialization(mock_dns_manager):
    """Test that ZoneTransfer initializes correctly"""
    transfer = ZoneTransfer(mock_dns_manager)
    
    assert transfer.dns_manager == mock_dns_manager


def test_perform_axfr_returns_tuple(zone_transfer):
    """Test that perform_axfr returns a tuple of (records, error)"""
    with patch('dns.query.xfr') as mock_xfr:
        # Mock a failed transfer
        mock_xfr.side_effect = dns.exception.FormError("Transfer denied")
        
        result = zone_transfer.perform_axfr('test.com')
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], str)


def test_perform_axfr_handles_form_error(zone_transfer):
    """Test that perform_axfr handles FormError (transfer denied)"""
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = dns.exception.FormError("Transfer denied")
        
        records, error = zone_transfer.perform_axfr('test.com')
        
        assert len(records) == 0
        assert 'denied' in error.lower() or 'malformed' in error.lower()


def test_perform_axfr_handles_timeout(zone_transfer):
    """Test that perform_axfr handles timeout"""
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = dns.exception.Timeout()
        
        records, error = zone_transfer.perform_axfr('test.com')
        
        assert len(records) == 0
        assert 'timeout' in error.lower()


def test_perform_axfr_handles_transfer_error(zone_transfer):
    """Test that perform_axfr handles TransferError"""
    with patch('dns.query.xfr') as mock_xfr:
        # TransferError requires an rcode (integer), not a string
        mock_xfr.side_effect = dns.query.TransferError(5)  # REFUSED rcode
        
        records, error = zone_transfer.perform_axfr('test.com')
        
        assert len(records) == 0
        assert 'transfer error' in error.lower()


def test_perform_axfr_handles_generic_exception(zone_transfer):
    """Test that perform_axfr handles generic exceptions"""
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = Exception("Unknown error")
        
        records, error = zone_transfer.perform_axfr('test.com')
        
        assert len(records) == 0
        assert 'failed' in error.lower()


def test_perform_axfr_successful_transfer(zone_transfer):
    """Test successful zone transfer"""
    # Create a mock zone
    mock_zone = Mock(spec=dns.zone.Zone)
    
    # Create mock node with A record
    mock_node = Mock()
    mock_rdataset = Mock()
    mock_rdataset.rdtype = dns.rdatatype.A
    mock_rdataset.ttl = 300
    
    # Create mock rdata
    mock_rdata = Mock()
    mock_rdata.__str__ = Mock(return_value='192.168.1.1')
    
    mock_rdataset.__iter__ = Mock(return_value=iter([mock_rdata]))
    mock_node.rdatasets = [mock_rdataset]
    
    # Set up zone nodes
    mock_zone.nodes = {
        dns.name.from_text('www'): mock_node
    }
    
    with patch('dns.query.xfr') as mock_xfr, \
         patch('dns.zone.from_xfr', return_value=mock_zone):
        
        records, error = zone_transfer.perform_axfr('test.com')
        
        assert len(records) > 0
        assert error == ''
        assert isinstance(records[0], DNSRecord)


def test_parse_zone_data_with_multiple_records(zone_transfer):
    """Test parsing zone data with multiple record types"""
    # Create a mock zone
    mock_zone = Mock(spec=dns.zone.Zone)
    
    # Create mock nodes with different record types
    nodes = {}
    
    # A record
    a_node = Mock()
    a_rdataset = Mock()
    a_rdataset.rdtype = dns.rdatatype.A
    a_rdataset.ttl = 300
    a_rdata = Mock()
    a_rdata.__str__ = Mock(return_value='192.168.1.1')
    a_rdataset.__iter__ = Mock(return_value=iter([a_rdata]))
    a_node.rdatasets = [a_rdataset]
    nodes[dns.name.from_text('www')] = a_node
    
    # MX record
    mx_node = Mock()
    mx_rdataset = Mock()
    mx_rdataset.rdtype = dns.rdatatype.MX
    mx_rdataset.ttl = 600
    mx_rdata = Mock()
    mx_rdata.__str__ = Mock(return_value='10 mail.test.com.')
    mx_rdataset.__iter__ = Mock(return_value=iter([mx_rdata]))
    mx_node.rdatasets = [mx_rdataset]
    nodes[dns.name.from_text('@')] = mx_node
    
    mock_zone.nodes = nodes
    
    records = zone_transfer.parse_zone_data(mock_zone, 'test.com')
    
    assert len(records) == 2
    assert any(r.record_type == 'A' for r in records)
    assert any(r.record_type == 'MX' for r in records)


def test_parse_zone_data_with_multiple_rdata(zone_transfer):
    """Test parsing zone data with multiple rdata in one rdataset"""
    # Create a mock zone
    mock_zone = Mock(spec=dns.zone.Zone)
    
    # Create mock node with multiple A records
    node = Mock()
    rdataset = Mock()
    rdataset.rdtype = dns.rdatatype.A
    rdataset.ttl = 300
    
    # Multiple rdata
    rdata1 = Mock()
    rdata1.__str__ = Mock(return_value='192.168.1.1')
    rdata2 = Mock()
    rdata2.__str__ = Mock(return_value='192.168.1.2')
    
    rdataset.__iter__ = Mock(return_value=iter([rdata1, rdata2]))
    node.rdatasets = [rdataset]
    
    mock_zone.nodes = {
        dns.name.from_text('www'): node
    }
    
    records = zone_transfer.parse_zone_data(mock_zone, 'test.com')
    
    assert len(records) == 2
    assert all(r.record_type == 'A' for r in records)
    assert records[0].data == '192.168.1.1'
    assert records[1].data == '192.168.1.2'


def test_parse_zone_data_preserves_ttl(zone_transfer):
    """Test that parse_zone_data preserves TTL values"""
    # Create a mock zone
    mock_zone = Mock(spec=dns.zone.Zone)
    
    node = Mock()
    rdataset = Mock()
    rdataset.rdtype = dns.rdatatype.A
    rdataset.ttl = 12345
    
    rdata = Mock()
    rdata.__str__ = Mock(return_value='192.168.1.1')
    
    rdataset.__iter__ = Mock(return_value=iter([rdata]))
    node.rdatasets = [rdataset]
    
    mock_zone.nodes = {
        dns.name.from_text('test'): node
    }
    
    records = zone_transfer.parse_zone_data(mock_zone, 'test.com')
    
    assert len(records) == 1
    assert records[0].ttl == 12345


def test_parse_zone_data_preserves_name(zone_transfer):
    """Test that parse_zone_data preserves record names"""
    # Create a mock zone
    mock_zone = Mock(spec=dns.zone.Zone)
    
    node = Mock()
    rdataset = Mock()
    rdataset.rdtype = dns.rdatatype.A
    rdataset.ttl = 300
    
    rdata = Mock()
    rdata.__str__ = Mock(return_value='192.168.1.1')
    
    rdataset.__iter__ = Mock(return_value=iter([rdata]))
    node.rdatasets = [rdataset]
    
    mock_zone.nodes = {
        dns.name.from_text('subdomain.test'): node
    }
    
    records = zone_transfer.parse_zone_data(mock_zone, 'test.com')
    
    assert len(records) == 1
    assert 'subdomain.test' in records[0].name


def test_parse_zone_data_empty_zone(zone_transfer):
    """Test parsing an empty zone"""
    # Create a mock zone with no nodes
    mock_zone = Mock(spec=dns.zone.Zone)
    mock_zone.nodes = {}
    
    records = zone_transfer.parse_zone_data(mock_zone, 'test.com')
    
    assert len(records) == 0
    assert isinstance(records, list)


def test_perform_axfr_uses_tsig_if_configured(zone_transfer):
    """Test that perform_axfr uses TSIG credentials if configured"""
    # Configure TSIG on the manager
    zone_transfer.dns_manager.tsig_keyring = {'test-key': 'secret'}
    zone_transfer.dns_manager.tsig_keyname = 'test-key'
    
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = dns.exception.FormError("Transfer denied")
        
        zone_transfer.perform_axfr('test.com')
        
        # Verify xfr was called with TSIG parameters
        mock_xfr.assert_called_once()
        call_kwargs = mock_xfr.call_args[1]
        assert call_kwargs['keyring'] == {'test-key': 'secret'}
        assert call_kwargs['keyname'] == 'test-key'


def test_perform_axfr_uses_correct_timeout(zone_transfer):
    """Test that perform_axfr uses the configured timeout"""
    zone_transfer.dns_manager.timeout = 25
    
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = dns.exception.FormError("Transfer denied")
        
        zone_transfer.perform_axfr('test.com')
        
        # Verify xfr was called with correct timeout
        mock_xfr.assert_called_once()
        call_kwargs = mock_xfr.call_args[1]
        assert call_kwargs['timeout'] == 25


def test_perform_axfr_uses_correct_port(zone_transfer):
    """Test that perform_axfr uses the configured port"""
    zone_transfer.dns_manager.port = 5353
    
    with patch('dns.query.xfr') as mock_xfr:
        mock_xfr.side_effect = dns.exception.FormError("Transfer denied")
        
        zone_transfer.perform_axfr('test.com')
        
        # Verify xfr was called with correct port
        mock_xfr.assert_called_once()
        call_kwargs = mock_xfr.call_args[1]
        assert call_kwargs['port'] == 5353


def test_validate_hostname_match_cname_mismatch():
    """Test that CNAME hostname mismatches are detected"""
    mock_dns_manager = Mock(spec=DNSManager)
    mock_logger = Mock()
    transfer = ZoneTransfer(mock_dns_manager, logger=mock_logger)
    
    # Test CNAME with mismatched hostname
    transfer._validate_hostname_match('web', 'web.test.com', 'CNAME', 'app.test.com.', 'test.com')
    
    assert len(transfer.validation_warnings) == 1
    assert 'CNAME mismatch' in transfer.validation_warnings[0]
    assert 'web' in transfer.validation_warnings[0]
    assert 'app' in transfer.validation_warnings[0]


def test_validate_hostname_match_cname_correct():
    """Test that matching CNAME hostnames don't generate warnings"""
    mock_dns_manager = Mock(spec=DNSManager)
    mock_logger = Mock()
    transfer = ZoneTransfer(mock_dns_manager, logger=mock_logger)
    
    # Test CNAME with matching hostname
    transfer._validate_hostname_match('web', 'web.test.com', 'CNAME', 'web.prod.com.', 'test.com')
    
    assert len(transfer.validation_warnings) == 0


def test_validate_hostname_match_ignores_non_relevant_types():
    """Test that validation only applies to A, AAAA, and CNAME records"""
    mock_dns_manager = Mock(spec=DNSManager)
    mock_logger = Mock()
    transfer = ZoneTransfer(mock_dns_manager, logger=mock_logger)
    
    # Test MX record (should be ignored)
    transfer._validate_hostname_match('mail', 'mail.test.com', 'MX', '10 mail.test.com.', 'test.com')
    
    assert len(transfer.validation_warnings) == 0


def test_validation_warnings_logged_on_transfer():
    """Test that validation warnings are logged during zone transfer"""
    mock_dns_manager = Mock(spec=DNSManager)
    mock_dns_manager.server = '192.168.168.55'
    mock_dns_manager.port = 53
    mock_dns_manager.timeout = 10
    mock_dns_manager.tsig_keyring = None
    mock_dns_manager.tsig_keyname = None
    
    mock_logger = Mock()
    transfer = ZoneTransfer(mock_dns_manager, logger=mock_logger)
    
    # Create a mock zone with CNAME mismatch
    mock_zone = Mock(spec=dns.zone.Zone)
    node = Mock()
    rdataset = Mock()
    rdataset.rdtype = dns.rdatatype.CNAME
    rdataset.ttl = 300
    
    rdata = Mock()
    rdata.__str__ = Mock(return_value='app.test.com.')
    
    rdataset.__iter__ = Mock(return_value=iter([rdata]))
    node.rdatasets = [rdataset]
    
    mock_zone.nodes = {
        dns.name.from_text('web'): node
    }
    
    with patch('dns.query.xfr') as mock_xfr, \
         patch('dns.zone.from_xfr', return_value=mock_zone):
        
        records, error = transfer.perform_axfr('test.com')
        
        # Verify warning was logged
        assert mock_logger.warning.called
        warning_call = mock_logger.warning.call_args[0][0]
        assert 'CNAME mismatch' in warning_call
