import pytest

from src.p6_converter.converter import Converter, NAMESPACES


@pytest.fixture
def converter():
    return Converter("tests/viaf000.viaf000.test_file.xml")

class TestConverter:
    def test_add_lang_and_urn_to_first_div(self, converter):
        converter.add_lang_and_urn_to_first_div()

        first_div = converter.tree.find(".//tei:text/tei:body/tei:div", namespaces=NAMESPACES)

        print(first_div.attrib)
        assert first_div.get("n") is not None
