import argparse

from lxml import etree
from lxml.builder import ElementMaker

parser = argparse.ArgumentParser(
                    prog='Epidoc Conversion',
                    description='Script to help with cleaning up Epidoc XML files',
                    epilog='')

parser.add_argument('filename')

E = ElementMaker(namespace="http://www.tei-c.org/ns/1.0",
                nsmap={None: "http://www.tei-c.org/ns/1.0"})
APP = E.app
DATE = E.date
LEM = E.lem

ENTITIES = {
    '&Acirc;': 'Â',
    '&Amacr;': 'Ā',
    # I don't know if Unicode can actually represent this -- it should have the turnstile on top of the A
    '&Arpress;': 'ⱵA',
    '&Ebreve;': 'Ĕ',
    # this is an approximation
    '&Eunc;': 'ϵ',
    '&Ndot;': 'Ṅ',
    '&Obreve;': 'Ŏ',
    '&Omacr;': 'Ō',
    '&abreve;': 'ă',
    '&acirc;': 'â',
    '&acutebreve;': '́̆',
    '&adot;': 'ȧ',
    '&amacr;': 'ā',
    '&anceps;': '×',
    '&ast;': '*',
    '&brevemacr;': '᷋',
    '&cacute;': 'ć',
    '&ccaron;': 'č',
    '&ccedil;': 'ç',
    '&cnull;': 'c̥',
    '&dash;': '–',
    '&eacute;': 'é',
    '&ebreve;': 'ĕ',
    '&ecirc;': 'ê',
    '&edot;': 'ė',
    # just an approximation
    '&eglide;': 'ε̬',
    '&egrave;': 'è',
    '&emacr;': 'ē',
    '&emacracute;': 'ḗ',
    '&enull;': 'ε̥',
    '&euml;': 'ë',
    '&gacute;': 'ǵ',
    '&gdot;': 'ġ',
    '&grave;': '`',
    '&ibreve;': 'ĭ',
    '&icirc;': 'î',
    # this is the closest unicode can get to ι with a glide below
    '&iglide;': 'ɩ̧',
    '&imacr;': 'ī',
    '&kacute;': 'ḱ',
    # I'm guessing they meant '&koppa;'
    '&koopa;': 'ϙ',
    '&koppa;': 'ϟ',
    '&lins;': '<img src="//upload.wikimedia.org/wikipedia/commons/thumb/2/27/Greek_Lambda_Athenian.svg/13px-Greek_Lambda_Athenian.svg.png" decoding="async" width="13" height="16" class="mw-file-element" srcset="//upload.wikimedia.org/wikipedia/commons/thumb/2/27/Greek_Lambda_Athenian.svg/19px-Greek_Lambda_Athenian.svg.png 1.5x, //upload.wikimedia.org/wikipedia/commons/thumb/2/27/Greek_Lambda_Athenian.svg/26px-Greek_Lambda_Athenian.svg.png 2x" data-file-width="43" data-file-height="53"/>',
    '&hellip;': '…',
    '&ldquo;': '“',
    '&lnull;': 'λ̥',
    '&lpress;': '⊣',
    '&rdquo;': '”',
    '&macracute;': '́̄',
    '&macrbreve;': '᷋',
    '&macrdot;': '∸',
    '&mdash;': '—',
    '&mnull;': 'μ̥',
    '&ndash;': '–',
    '&ndot;': 'ṅ',
    '&nbsp;': ' ',
    '&nnull;': 'ν̥',
    '&num;': 'ʹ',
    '&obreve;': 'ŏ',
    '&ocirc;': 'ô',
    '&odblac;': 'ö',
    '&omacr;': 'ō',
    '&ouml;': 'ö',
    '&lpar;': '(',
    '&rpar;': ')',
    '&rpress;': 'Ⱶ',
    '&lsqb;': '[',
    '&rsqb;': ']',
    '&lsquo;': '‘',
    '&rsquo;': '’',
    '&rmacr;': 'ṝ',
    '&rnull;': 'ρ̥',
    '&root;': '√',
    '&sampi;': 'ϡ',
    '&tnull;': 't̥',
    '&tnum;': '͵',
    '&rcirc;': 'ř',
    # not quote right, but about as close as we can get
    '&rlcrop;': '⎣',
    '&rough;': '῾',
    '&rtilde;': 'r̃',
    '&sacute;': 'ś',
    '&sbreve;': 'š',
    '&schwa;': 'ə',
    '&scirc;': 'ŝ',
    '&scron;': 'š',
    '&smooth;': '᾽',
    # not quote right, but about as close as we can get
    '&ubreve;': 'ŭ',
    '&ucirc;': 'û',
    # this is the closest unicode can currently get to υ with a glide
    '&uglide;': 'ṵ',
    '&umacr;': 'ū',
    '&uuml;': 'ü',
    '&ulcrop;': '⎤',
    '&urcrop;': '⎡',
    '&ymacr;': 'ȳ',
    '&zcaron;': 'ž',
}

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
        converter.convert_lemma_to_applemma()
        converter.convert_argument_tags()
        converter.convert_bylines()
        converter.convert_dates()
        converter.convert_langs()
        converter.convert_speeches()
        converter.convert_summary_children_to_siblings()
        converter.convert_overviews()
        converter.convert_summaries()
        converter.convert_sections()
        converter.remove_targOrder_attr()
        converter.write_etree()

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

if __name__ == '__main__':
    args = parser.parse_args()
    preconvert(args.filename)
    converter = Converter(args.filename)
    converter.convert()

    
