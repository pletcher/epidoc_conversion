from betacode import conv
from lxml import etree
from lxml.builder import ElementMaker

from .character_entities import ENTITIES

E = ElementMaker(namespace="http://www.tei-c.org/ns/1.0",
                nsmap={None: "http://www.tei-c.org/ns/1.0"})
APP = E.app
DATE = E.date
LEM = E.lem

LANGUAGES = {
    'de': 'deu',
    'en': 'eng',
    'fr': 'fra',
    'gr': 'grc',
    'greek': 'grc',
    'la': 'lat',
}

TEI_NS = "{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"

def fix_date(s):
    try:
        return s.zfill(5 if int(s) < 0 else 4)
    except ValueError:
        return s

def fix_lang(s):
    return LANGUAGES.get(s, s)

def preconvert(filename):
    with open(filename, 'r') as f:
        raw = f.read()

    for entity, s in ENTITIES.items():
        raw = raw.replace(entity, s)

    with open(filename, 'w') as f:
        f.write(raw)


class Converter:
    def __init__(self, filename):
        parser = etree.XMLParser(remove_blank_text=True)
        self.filename = filename
        self.tree = etree.parse(filename, parser=parser)

    def convert(self):
        self.convert_lemma_to_applemma()
        self.convert_betacode_to_unicode()
        self.convert_argument_tags()
        self.convert_bylines()
        self.convert_dates()
        self.convert_langs()
        self.convert_speeches()
        self.convert_summary_children_to_siblings()
        self.convert_overviews()
        self.convert_summaries()
        self.convert_sections()
        self.remove_targOrder_attr()
        self.write_etree()

    def convert_argument_tags(self):
        for argument in self.tree.iterfind(f".//{TEI_NS}argument"):
            argument.tag = 'div'
            argument.attrib['type'] = 'textpart'
            argument.attrib['subtype'] = 'chapter'
            argument.attrib['n'] = 'Argument'

    def convert_bylines(self):
        for byline in self.tree.iterfind(f".//{TEI_NS}byline"):
            byline.tag = "docAuthor"
    
    def convert_lemma_to_applemma(self):
        for lemma in self.tree.iterfind(f".//{TEI_NS}lemma"):
            orig_lang = lemma.attrib.get(f'{XML_NS}lang', lemma.attrib.get('lang'))
            lang = fix_lang(orig_lang)

            replacement = APP(
                LEM(lemma.text or '', {f'{XML_NS}lang': lang}),
            )
            replacement.tail = lemma.tail or ''
            lemma.getparent().replace(lemma, replacement)

    def convert_betacode_to_unicode(self):
        for node in self.tree.iterfind(f".//*[@{XML_NS}lang='greek']"):
            if node.text is not None:
                node.text = conv.beta_to_uni(node.text)

    def convert_dates(self):
        for date in self.tree.iterfind(f".//{TEI_NS}date"):
            when = date.attrib.get('value', date.attrib.get('when'))

            if when is None:
                continue
            
            if date.attrib.get('value') is not None:
                del date.attrib['value']
            
            date.attrib['when'] = fix_date(when)

        for date_range in self.tree.iterfind(f".//{TEI_NS}dateRange"):
            when_from = date_range.attrib.get('from')
            when_to = date_range.attrib.get('to')
            date_range.tag = 'date'

            date_range.attrib['from'] = fix_date(when_from)
            date_range.attrib['to'] = fix_date(when_to)

    def convert_langs(self):
        for lang_el in self.tree.findall(".//*[@lang]"):
            lang = lang_el.attrib.get('lang')

            del lang_el.attrib['lang']

            lang_el.attrib[f'{XML_NS}lang'] = fix_lang(lang)

    def convert_speeches(self):
        for speech in self.tree.iterfind(f".//{TEI_NS}div[@type='speech']"):
            speech.attrib['type'] = 'commentary'
            speech.attrib['subtype'] = 'speech'
    
    # NOTE: (charles) These functions are basically identical except for a
    # minor change in the xpath, but we're going to prefer explicitness
    # over DRY-ness for the moment.
    def convert_sections(self):
        for section in self.tree.iterfind(f".//{TEI_NS}div[@type='section']"):
            section.attrib['type'] = 'textpart'
            section.attrib['subtype'] = 'section'

    def convert_summaries(self):
        for summary in self.tree.iterfind(f".//{TEI_NS}div[@type='summary']"):
            summary.attrib['type'] = 'textpart'
            summary.attrib['subtype'] = 'section'

    def convert_overviews(self):
        for overview in self.tree.iterfind(f".//{TEI_NS}div[@type='overv']"):
            overview.attrib['type'] = 'textpart'
            overview.attrib['subtype'] = 'chapter'

    def convert_summary_children_to_siblings(self):
        for overview in self.tree.iterfind(f".//{TEI_NS}div[@type='overv']"):
            for summary in overview.iterfind(f"./{TEI_NS}div[@type='summary']"):
                prev = None
                for section in summary.iterfind(f"./{TEI_NS}div/[@type='section']"):
                    if prev is None:
                        summary.addnext(section)
                        prev = section
                    else:
                        prev.addnext(section)
                        prev = section
    
    def remove_targOrder_attr(self):
        for el in self.tree.iterfind(".//*[@targOrder]"):
            del el.attrib['targOrder']
    
    def write_etree(self):
        with open(self.filename, 'wb') as f:
            etree.indent(self.tree, space="\t")
            f.write(etree.tostring(self.tree, encoding="utf-8", xml_declaration=True))
