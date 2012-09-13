import dexy.commands

def test_filters_text():
    text = dexy.commands.filters_text()
    assert "PygmentsFilter (pyg, pygments) Apply Pygments syntax highlighting." in text

def test_filters_text_single_alias():
    text = dexy.commands.filters_text(alias="pyg")
    assert "Aliases: pyg, pygments" in text

def test_filters_text_versions():
    text = dexy.commands.filters_text(versions=True)
    assert "Installed version: Python" in text

def test_filters_text_single_alias_source():
    text = dexy.commands.filters_text(alias="pyg", source=True)
    assert "Aliases: pyg, pygments" in text
    assert "class" in text
    assert "PygmentsFilter" in text
    assert not "class PygmentsFilter" in text

def test_filters_text_single_alias_source_nocolor():
    text = dexy.commands.filters_text(alias="pyg", source=True, nocolor=True)
    assert "Aliases: pyg, pygments" in text
    assert "class PygmentsFilter" in text
