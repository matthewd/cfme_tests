# -*- coding: utf-8 -*
from cfme.fixtures import pytest_selenium as sel
from utils.conf import ui_bench_tests
from utils.pagestats import analyze_page_stat
from utils.pagestats import navigate_accordions
from utils.pagestats import pages_to_csv
from utils.pagestats import pages_to_statistics_csv
from utils.pagestats import perf_click
from utils.pagestats import standup_perf_ui
from collections import OrderedDict
import pytest
import re

explorer_filters = [
    re.compile(r'^POST \"\/miq_capacity\/optimize_tree_select\/\?id\=ds\-[0-9\-\_]*\"$'),
    re.compile(r'^POST \"\/miq_capacity\/optimize_tree_select\/\?id\=h\-[0-9\-\_]*\"$')]

bottlenecks_filters = [
    re.compile(r'^POST \"\/miq_capacity\/optimize_tree_select\/\?id\=ds\-[0-9\-\_]*\"$'),
    re.compile(r'^POST \"\/miq_capacity\/optimize_tree_select\/\?id\=h\-[0-9\-\_]*\"$')]


@pytest.mark.perf_ui_optimize
@pytest.mark.usefixtures("cfme_log_level_rails_debug")
def test_perf_ui_optimize_utilization(ssh_client, soft_assert):
    pages, ui_worker_pid, prod_tail = standup_perf_ui(ssh_client, soft_assert)

    pages.extend(analyze_page_stat(perf_click(ui_worker_pid, prod_tail, True, sel.force_navigate,
        'utilization'), soft_assert))

    services_acc = OrderedDict((('Utilization', 'utilization'), ))

    pages.extend(navigate_accordions(services_acc, 'utilization', (ui_bench_tests['page_check']
        ['optimize']['utilization']), ui_worker_pid, prod_tail, soft_assert))

    pages_to_csv(pages, 'perf_ui_optimize_utilization.csv')
    pages_to_statistics_csv(pages, explorer_filters, 'statistics.csv')


@pytest.mark.perf_ui_optimize
@pytest.mark.usefixtures("cfme_log_level_rails_debug")
def test_perf_ui_optimize_bottlenecks(ssh_client, soft_assert):
    pages, ui_worker_pid, prod_tail = standup_perf_ui(ssh_client, soft_assert)

    pages.extend(analyze_page_stat(perf_click(ui_worker_pid, prod_tail, True, sel.force_navigate,
        'bottlenecks'), soft_assert))

    services_acc = OrderedDict((('Bottlenecks', 'bottlenecks'), ))

    pages.extend(navigate_accordions(services_acc, 'bottlenecks', (ui_bench_tests['page_check']
        ['optimize']['bottlenecks']), ui_worker_pid, prod_tail, soft_assert))

    pages_to_csv(pages, 'perf_ui_optimize_bottlenecks.csv')
    pages_to_statistics_csv(pages, bottlenecks_filters, 'statistics.csv')
