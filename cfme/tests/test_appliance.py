# -*- coding: utf-8 -*-
"""Tests around the appliance"""

import pytest
import re

from utils import version

pytestmark = pytest.mark.smoke


@pytest.mark.ignore_stream("upstream")
@pytest.mark.parametrize(('package'), [
    'cfme',
    'cfme-appliance',
    'cfme-lib',
    'nfs-utils',
    'nfs-utils-lib',
    'mingw32-cfme-host',
    'ipmitool',
    'prince',
    'netapp-manageability-sdk',
    'rhn-client-tools',
    'rhn-check',
    'rhnlib',
])
def test_rpms_present(ssh_client, package):
    """Verifies nfs-util rpms are in place needed for pxe & nfs operations"""
    exit, stdout = ssh_client.run_command('rpm -q %s' % package)
    assert 'is not installed' not in stdout
    assert exit == 0


# this is going to fail on 5.1
def test_selinux_enabled(ssh_client):
    """Verifies selinux is enabled"""
    stdout = ssh_client.run_command('getenforce')[1]
    assert 'Enforcing' in stdout


def test_iptables_running(ssh_client):
    """Verifies iptables service is running on the appliance"""
    stdout = ssh_client.run_command('service iptables status')[1]
    assert 'is not running' not in stdout


def test_httpd_running(ssh_client):
    """Verifies httpd service is running on the appliance"""
    stdout = ssh_client.run_command('service httpd status')[1]
    assert 'is running' in stdout


def test_evm_running(ssh_client):
    """Verifies overall evm service is running on the appliance"""
    stdout = ssh_client.run_command('service evmserverd status | grep EVM')[1]
    assert 'started' in stdout


@pytest.mark.parametrize(('service'), [
    'evmserverd',
    'evminit',
    'sshd',
    'iptables',
    'postgresql92-postgresql',
])
def test_chkconfig_on(ssh_client, service):
    """Verifies if key services are configured to start on boot up"""
    stdout = ssh_client.run_command('chkconfig | grep ' + service)[1]
    assert '5:on' in stdout


@pytest.mark.ignore_stream("upstream")
@pytest.mark.parametrize(('rule'), [
    'ACCEPT     tcp  --  anywhere             anywhere            state NEW tcp dpt:ssh',
    'ACCEPT     tcp  --  anywhere             anywhere            state NEW tcp dpt:http',
    'ACCEPT     tcp  --  anywhere             anywhere            state NEW tcp dpt:https'
])
def test_iptables_rules(ssh_client, rule):
    """Verifies key iptable rules are in place"""
    stdout = ssh_client.run_command('iptables -L')[1]
    assert rule in stdout


# this is based on expected changes tracked in github/ManageIQ/cfme_build repo
def test_memory_total(ssh_client):
    """Verifies that the total memory on the box is >= 6GB"""
    stdout = ssh_client.run_command(
        'free -g | grep Mem: | awk \'{ print $2 }\'')[1]
    assert stdout >= 6


# this is based on expected changes tracked in github/ManageIQ/cfme_build repo
def test_cpu_total(ssh_client):
    """Verifies that the total number of cpus is >= 4"""
    stdout = ssh_client.run_command(
        'lscpu | grep ^CPU\(s\): | awk \'{ print $2 }\'')[1]
    assert stdout >= 4


@pytest.mark.ignore_stream("upstream")
def test_certificates_present(ssh_client, soft_assert):
    """Test whether the required product certificates are present.

    This test is parametrized with the given file and its MD5 hash.
    If the given MD5 hash is ``None``, it won't be checked.

    From wiki:
    `Ships with /etc/pki/product/<id>.pem where RHEL is "69" and CF is "167"`
    """
    filenames_md5s = version.pick({
        version.LOWEST: [
            ("/etc/pki/product/69.pem", None),
            ("/etc/pki/product/167.pem", None)
        ],
        '5.3': [
            ("/etc/pki/product/69.pem", None),
            ("/etc/pki/product/167.pem", None),
            ("/etc/pki/product/201.pem", None)
        ]
    })
    for filename, given_md5 in filenames_md5s:
        file_exists = ssh_client.run_command("test -f '%s'" % filename)[0] == 0
        soft_assert(file_exists, "File %s does not exist!" % filename)
        if given_md5:
            md5_of_file = ssh_client.run_command("md5sum '%s'" % filename)[1].strip()
            # Format `abcdef0123456789<whitespace>filename
            md5_of_file = re.split(r"\s+", md5_of_file, 1)[0]
            soft_assert(given_md5 == md5_of_file, "md5 of file %s differs" % filename)


@pytest.mark.ignore_stream("upstream")
def test_db_connection(db):
    """Test that the pgsql db is listening externally

    This looks for a row in the miq_databases table, which should always exist
    on an appliance with a working database and UI
    """
    databases = db.session.query(db['miq_databases']).all()
    assert len(databases) > 0


@pytest.mark.bugzilla(1121202)
def test_asset_precompiled(ssh_client):
    version = ssh_client.get_version()
    if not version.startswith('5.2'):
        file_exists = ssh_client.run_command("test -d /var/www/miq/vmdb/public/assets")[0] == 0
        assert file_exists, "Assets not precompiled"
