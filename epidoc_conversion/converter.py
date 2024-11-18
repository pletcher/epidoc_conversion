from betacode import conv
from copy import deepcopy
from lxml import etree
from lxml.builder import ElementMaker

import logging

logging.basicConfig(level=logging.INFO)

from .character_entities import ENTITIES

E = ElementMaker(
    namespace="http://www.tei-c.org/ns/1.0", nsmap={None: "http://www.tei-c.org/ns/1.0"}
)
APP = E.app
DATE = E.date
DIV = E.div
LEM = E.lem

LANGUAGES = {
    "de": "deu",
    "en": "eng",
    "fr": "fra",
    "gr": "grc",
    "greek": "grc",
    "it": "ita",
    "la": "lat",
}

LOGGER = logging.getLogger(__name__)

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
    with open(filename, "r") as f:
        raw = f.read()

    for entity, s in ENTITIES.items():
        raw = raw.replace(entity, s)

    with open(filename, "w") as f:
        f.write(raw)


class Converter:
    def __init__(self, filename):
        parser = etree.XMLParser(remove_blank_text=True)
        self.filename = filename
        self.tree = etree.parse(filename, parser=parser)

    def convert(self):
        self.convert_lemma_to_applemma()
        self.convert_argument_tags()
        self.convert_bylines()
        self.convert_dates()
        self.convert_langs()
        # betacode to unicode needs to come after
        # language attributes have been fixed
        self.convert_betacode_to_unicode()
        self.convert_milestones_to_textparts()
        self.convert_speeches()
        self.convert_summary_children_to_siblings()
        self.convert_overviews()
        self.convert_summaries()
        self.convert_sections()
        self.remove_targOrder_attr()
        self.write_etree()

    def convert_argument_tags(self):
        for argument in self.tree.iterfind(f".//{TEI_NS}argument"):
            argument.tag = "div"
            argument.attrib["type"] = "textpart"
            argument.attrib["subtype"] = "chapter"
            argument.attrib["n"] = "Argument"

    def convert_bylines(self):
        for byline in self.tree.iterfind(f".//{TEI_NS}byline"):
            byline.tag = "docAuthor"

    def convert_lemma_to_applemma(self):
        for lemma in self.tree.iterfind(f".//{TEI_NS}lemma"):
            orig_lang = lemma.attrib.get(f"{XML_NS}lang", lemma.attrib.get("lang"))
            lang = fix_lang(orig_lang)

            replacement = APP(
                LEM(lemma.text or "", {f"{XML_NS}lang": lang}),
            )
            replacement.tail = lemma.tail or ""
            lemma.getparent().replace(lemma, replacement)

    # FIXME: This still misses cases where there is an element
    # within the Greek-language el, e.g.,
    # <foreign xml:lang="grc">νόμων <gap reason="illegible"/> o(/soi ai)sxu/nhn fe/rousi</foreign>
    def convert_betacode_to_unicode(self):
        logging.info(f"convert_betacode_to_unicode() called")

        for el in self.tree.iterfind(f".//*[@{XML_NS}lang='grc']"):
            logging.info(f"Converting betacode to unicode in {el}")

            if el.text is not None:
                el.text = conv.beta_to_uni(el.text)

            for descendant in el.iterdescendants():
                logging.info(f"Iterating descendants of {el}")
                if descendant.text is not None:
                    descendant.text = conv.beta_to_uni(descendant.text)

        for gap in self.tree.iterfind(f".//{TEI_NS}gap"):
            logging.info(f"Found a <gap> element -- checking parent for language")

            gap_parent = gap.getparent()

            if gap_parent.get(f"{XML_NS}lang") == "grc" and gap.tail is not None:
                logging.info(
                    f"<gap> element's parent declares 'grc' @lang and <gap> has tail text -- converting {gap.tail} to Unicode"
                )

                gap.tail = conv.beta_to_uni(gap.tail)

        logging.info(f"convert_betacode_to_unicode() finished")

    def convert_dates(self):
        for date in self.tree.iterfind(f".//{TEI_NS}date"):
            when = date.attrib.get("value", date.attrib.get("when"))

            if when is None:
                continue

            if date.attrib.get("value") is not None:
                del date.attrib["value"]

            date.attrib["when"] = fix_date(when)

        for date_range in self.tree.iterfind(f".//{TEI_NS}dateRange"):
            when_from = date_range.attrib.get("from")
            when_to = date_range.attrib.get("to")
            date_range.tag = "date"

            date_range.attrib["from"] = fix_date(when_from)
            date_range.attrib["to"] = fix_date(when_to)

    def convert_langs(self):
        LOGGER.info("convert_langs() called")

        for lang_el in self.tree.findall(".//*[@lang]"):
            lang = lang_el.attrib.get("lang")

            del lang_el.attrib["lang"]

            lang_el.attrib[f"{XML_NS}lang"] = fix_lang(lang)

        for lang_el in self.tree.iterfind(f".//*[@{XML_NS}lang]"):
            lang = lang_el.get(f"{XML_NS}lang")
            lang_el.attrib[f"{XML_NS}lang"] = fix_lang(lang)

        for lang_el in self.tree.iterfind(f".//{TEI_NS}langUsage/{TEI_NS}language"):
            lang = lang_el.get("ident")
            lang_el.attrib["ident"] = fix_lang(lang)

    def convert_milestones_to_textparts(self):
        for milestone in self.tree.iterfind(f".//{TEI_NS}milestone"):
            current_unit = milestone.get("unit")

            if current_unit is None:
                break

            siblings = []

            for sibling in milestone.itersiblings():
                if (
                    sibling.tag == f"{TEI_NS}milestone"
                    and sibling.get("unit") == current_unit
                ):
                    break
                siblings.append(sibling)

            div = DIV(
                type="textpart",
                subtype=current_unit,
                n=milestone.get("n", ""),
                ed=milestone.get("ed", ""),
                *siblings,
            )
            parent = milestone.getparent()
            parent.replace(milestone, div)

    def convert_speeches(self):
        for speech in self.tree.iterfind(f".//{TEI_NS}div[@type='speech']"):
            speech.attrib["type"] = "commentary"
            speech.attrib["subtype"] = "speech"

    # NOTE: (charles) These functions are basically identical except for a
    # minor change in the xpath, but we're going to prefer explicitness
    # over DRY-ness for the moment.
    def convert_sections(self):
        for section in self.tree.iterfind(f".//{TEI_NS}div[@type='section']"):
            section.attrib["type"] = "textpart"
            section.attrib["subtype"] = "section"

    def convert_summaries(self):
        for summary in self.tree.iterfind(f".//{TEI_NS}div[@type='summary']"):
            summary.attrib["type"] = "textpart"
            summary.attrib["subtype"] = "section"

    def convert_overviews(self):
        for overview in self.tree.iterfind(f".//{TEI_NS}div[@type='overv']"):
            overview.attrib["type"] = "textpart"
            overview.attrib["subtype"] = "chapter"

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
            del el.attrib["targOrder"]

    def write_etree(self):
        with open(self.filename, "wb") as f:
            etree.indent(self.tree, space="\t")
            f.write(etree.tostring(self.tree, encoding="utf-8", xml_declaration=True))
