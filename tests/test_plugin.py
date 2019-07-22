import dexy.plugin

class WidgetBase(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    """
    Example of plugin.
    """
    _settings = {
            'foo' : ("Default value for foo", "bar"),
            'abc' : ("Default value for abc", 123)
            }

class Widget(WidgetBase):
    """
    Widget class.
    """
    aliases = ['widget']

class SubWidget(Widget):
    """
    Subwidget class.
    """
    aliases = ['sub']
    _settings = {
            'foo' : 'baz'
            }

class Fruit(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    '''fruit class'''
    aliases = ['fruit']
    _settings = {}

class Starch(dexy.plugin.Plugin, metaclass=dexy.plugin.PluginMeta):
    '''starch class'''
    aliases = ['starch']
    _settings = {}
    _other_class_settings = {
            'fruit' : {
                    "color" : ("The color of the fruit", "red")
                }
            }

def test_plugin_meta():
    new_class = dexy.plugin.PluginMeta(
            "Foo",
            (dexy.plugin.Plugin,),
            {
                'aliases' : [],
                "__doc__" : 'help',
                '__metaclass__' : dexy.plugin.PluginMeta
                }
            )

    assert new_class.__name__ == 'Foo'
    assert new_class.__doc__ == 'help'
    assert new_class.aliases == []
    assert new_class.plugins == {}

def test_create_instance():
    widget = Widget.create_instance('widget')
    assert widget.setting('foo') == 'bar'

    sub = Widget.create_instance('sub')
    assert sub.setting('foo') == 'baz'
    assert sub.setting('abc') == 123
    assert sub.setting_values()['foo'] == 'baz'
    assert sub.setting_values()['abc'] == 123

def test_other_class_settings():
    fruit = Fruit()
    fruit.initialize_settings()
    assert fruit.setting('color') == 'red'
