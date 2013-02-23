import dexy.plugin

def test_plugin_meta():
    new_class = dexy.plugin.PluginMeta(
            "Foo",
            (dexy.plugin.Plugin,),
            {
                'ALIASES' : [],
                "__doc__" : 'help',
                '__metaclass__' : dexy.plugin.PluginMeta
                }
            )

    assert new_class.__name__ == 'Foo'
    assert new_class.__doc__ == 'help'
    assert new_class.ALIASES == []
    assert new_class.plugins == {}
