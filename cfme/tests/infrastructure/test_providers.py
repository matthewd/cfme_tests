# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=W0621

import pytest
import cfme.web_ui.flash as flash
from cfme.infrastructure import provider
from utils.update import update
import uuid
import utils.error as error


@pytest.fixture(params=['rhevm32', 'vsphere55'])
def provider_data(request, cfme_data):
    """ Returns management system data from cfme_data"""
    return provider.get_from_config(request.param)


@pytest.fixture
def has_no_providers(db_session):
    """ Clears all management systems from an applicance

    This is a destructive fixture. It will clear all managements systems from
    the current appliance.
    """
    import db
    db_session.query(db.ExtManagementSystem).delete()
    db_session.commit()

pytestmark = [pytest.mark.usefixtures("logged_in")]


def test_that_checks_flash_with_empty_discovery_form():
    """ Tests that the flash message is correct when discovery form is empty."""
    provider.discover(None)
    flash.assert_message_match('At least 1 item must be selected for discovery')


def test_that_checks_flash_when_discovery_cancelled():
    """ Tests that the flash message is correct when discovery is cancelled."""
    provider.discover(None, cancel=True)
    flash.assert_message_match('Infrastructure Providers Discovery was cancelled by the user')


@pytest.mark.usefixtures('has_no_providers')
def test_providers_discovery(provider_data):
    provider.discover_from_provider(provider_data)
    flash.assert_message_match('Infrastructure Providers: Discovery successfully initiated')
    # TODO - wait for it to finish (no reliable way to do that currently)


@pytest.mark.usefixtures('has_no_providers')
def test_provider_add(provider_data):
    """ Tests that a provider can be added """
    provider_data.create()
    flash.assert_message_match('Infrastructure Providers "%s" was saved' % provider_data.name)
    provider_data.validate()


@pytest.mark.usefixtures('has_no_providers')
def test_provider_add_with_bad_credentials(provider_data):
    provider_data.credentials = provider.get_credentials_from_config('bad_credentials')
    if isinstance(provider_data, provider.VMwareProvider):
        with error.expected('Cannot complete login due to an incorrect user name or password.'):
            provider_data.create(validate_credentials=True)
    elif isinstance(provider_data, provider.RHEVMProvider):
        with error.expected('401 Unauthorized'):
            provider_data.create(validate_credentials=True)


@pytest.mark.usefixtures('has_no_providers')
def test_provider_edit(provider_data):
    """ Tests that editing a management system shows the proper detail after an edit."""
    provider_data.create()
    old_name = provider_data.name
    with update(provider_data) as provider_data:
        provider_data.name = str(uuid.uuid4())  # random uuid
    flash.assert_message_match('Infrastructure Provider "%s" was saved' % provider_data.name)

    with update(provider_data) as provider_data:
        provider_data.name = old_name  # old name
    flash.assert_message_match('Infrastructure Provider "%s" was saved' % provider_data.name)


def test_that_checks_flash_when_add_cancelled():
    """Tests that the flash message is correct when add is cancelled."""
    prov = provider.VMwareProvider()
    prov.create(cancel=True)
    flash.assert_message_match('Add of new Infrastructure Provider was cancelled by the user')