from src.parser.tag_parser import TagParser, Tag, Field


BLOCK4_TEXT = """
:20:SENDER-REF-001
:23B:CRED
:32A:240101KRW50000000,
:50K:/123456789
WOORI BANK SEOUL
:57A:HNBKKRSE
:59:/987654321
KOREA BANK COUNTERPARTY
:70:OFFSHORE KRW PAYMENT TEST
:71A:SHA
"""


class TestTagParser:
    parser = TagParser()

    def test_extract_tags_returns_list(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        assert isinstance(tags, list)

    def test_extract_tags_count(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        assert len(tags) == 8

    def test_extract_tags_first_tag_name(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        assert tags[0].name == ":20:"

    def test_extract_tags_first_tag_value(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        assert tags[0].value == "SENDER-REF-001"

    def test_extract_tags_line_number(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        assert tags[0].line == 2
        assert tags[1].line == 3

    def test_extract_tags_specific_values(self):
        tags = self.parser.extract_tags(BLOCK4_TEXT)
        tag_map = {t.name: t.value for t in tags}
        assert tag_map[":23B:"] == "CRED"
        assert tag_map[":32A:"] == "240101KRW50000000,"
        assert tag_map[":71A:"] == "SHA"

    def test_extract_tags_empty_text(self):
        tags = self.parser.extract_tags("")
        assert tags == []

    def test_extract_tags_no_tags(self):
        tags = self.parser.extract_tags("NO TAGS HERE\nJUST TEXT\n")
        assert tags == []

    def test_parse_field_returns_field(self):
        tag = Tag(name=":20:", value="TEST-REF", line=1)
        field = self.parser.parse_field(tag)
        assert isinstance(field, Field)

    def test_parse_field_preserves_name(self):
        tag = Tag(name=":20:", value="TEST-REF", line=1)
        field = self.parser.parse_field(tag)
        assert field.name == ":20:"

    def test_parse_field_preserves_value(self):
        tag = Tag(name=":20:", value="TEST-REF", line=1)
        field = self.parser.parse_field(tag)
        assert field.value == "TEST-REF"

    def test_parse_field_qualifier_from_tag_with_slash(self):
        tag = Tag(name=":52A/D:", value="WOOBUS33", line=1)
        field = self.parser.parse_field(tag)
        assert field.qualifier == "D"

    def test_parse_field_no_qualifier(self):
        tag = Tag(name=":20:", value="TEST", line=1)
        field = self.parser.parse_field(tag)
        assert field.qualifier is None

    def test_parse_field_raw_value(self):
        tag = Tag(name=":20:", value="TEST-REF", line=1)
        field = self.parser.parse_field(tag)
        assert field.raw_value == "TEST-REF"
