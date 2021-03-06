# -*- coding: utf-8 -*-
"""meta(\*\*metadata): Marker for metadata addition.

To add metadata to a test simply pass the kwargs as plugins wish.

You can write your own plugins. They generally live in ``metaplugins/`` directory but you can
define them pretty much everywhere py.test loads modules. Plugin has a name and a set
of callbacks that are called when certain combination of keys is present in the metadata.

To define plugin, do like this:

.. code-block:: python

   @plugin("plugin_name")
   def someaction(plugin_name):
       print plugin_name  # Will contain value of `plugin_name` key of metadict

This is the simplest usage, where it is supposed that the plugin checks only one key with the
same name s the plugin's name. I won't use this one in the latter examples, I will use the
more verbose one.

.. code-block:: python

   @plugin("plugin_name", keys=["plugin_name", "another_key"])
   def someaction(plugin_name, another_key):
       print plugin_name  # Will contain value of `plugin_name` key of metadict
       print another_key  # Similarly this one

This one reacts when the two keys are present. You can make even more complex setups:

.. code-block:: python

   @plugin("plugin_name", keys=["plugin_name"])
   @plugin("plugin_name", ["plugin_name", "another_key"])  # You don't have to write keys=
   def someaction(plugin_name, another_key=None):
       print plugin_name  # Will contain value of `plugin_name` key of metadict
       print another_key  # Similarly this one if specified, otherwise None

This created a nonrequired parameter for the action.

You can specify as many actions as you wish per plugin. The only thing that limits you is the
correct action choice. First, all the actions are filtered by present keys in metadata. Then
after this selection, only the action with the most matched keywords is called. Bear this
in your mind. If this is not enough in the future, it can be extended if you wish.

"""
from collections import namedtuple
from types import FunctionType

import pytest

from utils import kwargify
from utils.log import logger


class metadict(dict):
    """A dictionary that can access items as object variables, returns None if not found"""
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            return None


def pytest_configure(config):
    config.addinivalue_line("markers", __doc__.splitlines()[0])


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    # Put the meta mark on objects as soon as pytest begins to collect them
    if isinstance(obj, FunctionType) and not hasattr(obj, 'meta'):
        pytest.mark.meta(obj)


@pytest.mark.tryfirst
def pytest_collection_modifyitems(session, config, items):
    for item in items:
        item._metadata = metadict(item.function.meta.kwargs)
        meta = item.get_marker("meta")
        if meta is None:
            continue
        metas = reversed([x.kwargs for x in meta])  # Extract the kwargs, reverse the order
        for meta in metas:
            item._metadata.update(meta)


@pytest.fixture(scope="function")
def meta(request):
    return request.node._metadata


Plugin = namedtuple('Plugin', ['name', 'metas', 'function', 'kwargs'])


class PluginContainer(object):
    SETUP = "setup"
    TEARDOWN = "teardown"
    BEFORE_RUN = "before_run"
    AFTER_RUN = "after_run"
    DEFAULT = SETUP

    def __init__(self):
        self._plugins = []

    def __call__(self, name, keys=None, **kwargs):
        if keys is None:
            keys = [name]

        def f(g):
            self._plugins.append(Plugin(name, keys, kwargify(g), kwargs))
            return g  # So the markers can be chained
        return f

if "plugin" not in globals():
    plugin = PluginContainer()


def run_plugins(item, when):
    possible_plugins = []
    for plug in plugin._plugins:
        if all([meta in item._metadata.keys() for meta in plug.metas])\
                and plug.kwargs.get("run", plugin.DEFAULT) == when:
            possible_plugins.append(plug)
    by_names = {}
    for plug in possible_plugins:
        if plug.name not in by_names:
            by_names[plug.name] = []
        by_names[plug.name].append(plug)
    for plugin_name, plugin_objects in by_names.iteritems():
        plugin_objects.sort(key=lambda p: len(p.metas), reverse=True)
        plug = plugin_objects[0]
        env = {"item": item}
        for meta in plug.metas:
            env[meta] = item._metadata[meta]
        logger.info(
            "Calling metaplugin {}({}) with meta signature {} {}".format(
                plugin_name, plug.function.__name__, str(plug.metas), str(plug.kwargs)))
        plug.function(**env)
        logger.info(
            "Metaplugin {}({}) with meta signature {} {} has finished".format(
                plugin_name, plug.function.__name__, str(plug.metas), str(plug.kwargs)))


def pytest_runtest_setup(item):
    run_plugins(item, plugin.SETUP)


def pytest_runtest_teardown(item):
    run_plugins(item, plugin.TEARDOWN)


def pytest_runtest_call(__multicall__, item):
    run_plugins(item, plugin.BEFORE_RUN)
    try:
        __multicall__.execute()
    finally:
        run_plugins(item, plugin.AFTER_RUN)
