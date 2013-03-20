import dexy.plugin

class ExampleClass(object):
    """
    An example of a base pluginable class.
    """
    __metaclass__ = dexy.plugin.PluginMeta
    _settings = {}

class One(ExampleClass):
    """
    An example class named One.
    """
    aliases = ['one']

class Two(One):
    """
    An example class named Two.
    """
    aliases = ['two']

def test_plugin_meta():
    assert 'one' in ExampleClass.plugins
    assert 'two' in ExampleClass.plugins

    assert not 'three' in ExampleClass.plugins
    ExampleClass.register_plugin('three', One, {"FOO":"bar"})

    assert ExampleClass.plugins['one'][0] == One
    assert ExampleClass.plugins['two'][0] == Two

    assert ExampleClass.plugins['three'][0] == One

    assert sorted(ExampleClass.plugins.keys()) == ['one', 'three', 'two']
