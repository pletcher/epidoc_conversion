from betacode import conv
from copy import deepcopy
from lxml.builder import ElementMaker

import logging
import lxml.etree as etree

from .character_entities import ENTITIES

logging.basicConfig(level=logging.INFO)

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

NAMESPACES = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace",
}

TEI_NS = "{http://www.tei-c.org/ns/1.0}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"

SKIPPABLE_MILESTONE_UNITS = (
    "pg_l",
    None,
)

URN_SUBSTITUTIONS = {
    "Soph. OC": "urn:cts:greekLit:tlg0011.tlg007",
    "Soph. OT": "urn:cts:greekLit:tlg0011.tlg004",
}


def convert_citation(s: str) -> str:
    """
    Convert a natural language citation, such
    as `"Soph. OC 437"` to a CTS URN like
    `"urn:cts:greekLit:tlg0011.tlg007:437"`.
    """

    # Iterate through the URN_SUBSTITUTIONS
    # provided above, checking for a match
    # on the keys. As soon as a match is found,
    # replace it in the citation, stripping the
    # result in case of extra spaces. The remaining
    # part of the string should be the citation
    # component of a URN, which we can append to
    # the URN prefix provided as the value from the
    # matching key in URN_SUBSTITUTIONS.
    for nat, urn in URN_SUBSTITUTIONS.items():
        if nat in s:
            n = s.replace(nat, "").strip()

            # Some citations might reference an
            # entire work, so we'll need to return
            # the whole URN.
            if len(n) > 0:
                return f"{urn}:{n}"
            else:
                return urn

    return s


def derive_lang(tree):
    doc_languages = tree.xpath(".//tei:langUsage/tei:language", namespaces=NAMESPACES)

    if len(doc_languages) > 0:
        return fix_lang(doc_languages[0].get("ident"))


def derive_urn(filename, tree):
    work = filename.split("/")[-1].replace(".xml", "")
    doc_languages = tree.xpath(".//tei:langUsage/tei:language", namespaces=NAMESPACES)

    for language in doc_languages:
        lang = fix_lang(language.get("ident"))

        LOGGER.debug(lang)

        if lang == "lat":
            return f"urn:cts:latinLit:{work}"
        if lang == "grc":
            return f"urn:cts:greekLit:{work}"

    return None


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
        self.assign_refable_units()
        self.add_lang_and_urn_to_body_and_first_div()
        self.convert_lemma_to_applemma()
        self.convert_note_gloss_to_app()
        self.remove_div_pg_l()
        self.convert_argument_tags()
        self.convert_bylines()
        self.convert_dates()
        self.convert_langs()
        # betacode to unicode needs to come after
        # language attributes have been fixed
        self.convert_betacode_to_unicode()
        self.convert_milestones_to_textparts()
        self.pro_lege_manilia()
        self.convert_speeches()
        self.convert_summary_children_to_siblings()
        self.convert_overviews()
        self.convert_summaries()
        self.convert_sections()
        # self.number_textparts()
        self.remove_targOrder_attr()
        # self.uproot_smyth_parts()
        self.add_ref_to_bibls()
        self.write_etree()

    def add_lang_and_urn_to_body_and_first_div(self):
        LOGGER.info("add_lang_and_urn_to_body_and_first_div() called")

        body = self.tree.find(".//tei:body", namespaces=NAMESPACES)

        if body is None:
            LOGGER.warn("No <body> tag found")
            return

        lang = body.attrib.get(f"{XML_NS}lang")

        if lang is None:
            lang = derive_lang(self.tree)

        LOGGER.debug(lang)

        urn = body.attrib.get("n")

        if urn is None:
            urn = derive_urn(self.filename, self.tree)

        LOGGER.debug(urn)

        if lang is not None and urn is not None:
            first_div = self.tree.find(".//tei:body/tei:div", namespaces=NAMESPACES)
            body.attrib["n"] = urn
            body.attrib[f"{XML_NS}lang"] = fix_lang(lang)
            first_div.attrib["n"] = urn
            first_div.attrib[f"{XML_NS}lang"] = fix_lang(lang)

            self.lang = lang
            self.urn = urn
        else:
            LOGGER.debug(body.attrib)

    def add_ref_to_bibls(self):
        for bibl in self.tree.iterfind(".//tei:bibl", namespaces=NAMESPACES):
            n = bibl.get("n")

            if n is None:
                LOGGER.warning(f"@n attribute not found at {etree.tostring(bibl)}")
                continue

            ref_urn = convert_citation(n)

            bibl.set("ref", ref_urn)

    def assign_refable_units(self):
        """
        Read the `refsDecl`s and create a list of units that can be referenced.
        This is important for converting milestones to textparts later.
        """

        refsDecls = self.tree.find(".//tei:refsDecl[@n='CTS']", namespaces=NAMESPACES)

        refable_units = []

        for cRefPattern in refsDecls.iterfind(
            ".//tei:cRefPattern", namespaces=NAMESPACES
        ):
            refable_units.append(cRefPattern.get("n"))

        LOGGER.debug(refable_units)

        self.refable_units = refable_units

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
        """
        FIXME: (charles) We should instead use <term> and <gloss> tags:
        https://epidoc.stoa.org/gl/latest/ref-term.html
        """

        for lemma in self.tree.iterfind(f".//{TEI_NS}lemma"):
            orig_lang = lemma.attrib.get(f"{XML_NS}lang", lemma.attrib.get("lang"))
            lang = fix_lang(orig_lang)

            replacement = APP(
                LEM(lemma.text or "", {f"{XML_NS}lang": lang}),
            )
            replacement.tail = lemma.tail or ""  # pyright: ignore
            lemma.getparent().replace(lemma, replacement)

    def convert_note_gloss_to_app(self):
        for note_gloss in self.tree.iterfind(f".//{TEI_NS}note[@type='gloss']"):
            replacement = APP()

            for child in note_gloss:
                replacement.append(child)  # pyright: ignore

            replacement.tail = note_gloss.tail or ""  # pyright: ignore
            note_gloss.getparent().replace(note_gloss, replacement)

    def convert_betacode_to_unicode(self):
        """
        Convert [@lang='grc'] tags from Betacode to Unicode.
        Note that we only convert inner `tail` text — i.e.,
        `el.tail` is not converted because it should not still
        be Greek.
        """
        logging.info("convert_betacode_to_unicode() called")

        for el in self.tree.iterfind(f".//*[@{XML_NS}lang='grc']"):
            logging.info(f"Converting betacode to unicode in {el}")

            if el.text is not None:
                el.text = conv.beta_to_uni(el.text)

            for descendant in el.iterdescendants():
                logging.info(f"Iterating descendants of {el}")
                if descendant.text is not None:
                    if descendant.attrib.get(f"{XML_NS}lang") == "eng":
                        descendant.text = conv.uni_to_beta(descendant.text)
                    elif descendant.getparent().attrib.get(f"{XML_NS}lang") == "eng":
                        descendant.text = conv.uni_to_beta(descendant.text)
                    else:
                        descendant.text = conv.beta_to_uni(descendant.text)

                if descendant.tail is not None:
                    if descendant.getparent().attrib.get(f"{XML_NS}lang") == "grc":
                        descendant.tail = conv.beta_to_uni(descendant.tail)
                    elif descendant.getparent().attrib.get(f"{XML_NS}lang") == "eng":
                        descendant.tail = conv.uni_to_beta(descendant.text)

        for gap in self.tree.iterfind(f".//{TEI_NS}gap"):
            logging.info("Found a <gap> element -- checking parent for language")

            gap_parent = gap.getparent()

            if gap_parent.get(f"{XML_NS}lang") == "grc" and gap.tail is not None:
                logging.info(
                    f"<gap> element's parent declares 'grc' @lang and <gap> has tail text -- converting {gap.tail} to Unicode"
                )

                gap.tail = conv.beta_to_uni(gap.tail)

        logging.info("convert_betacode_to_unicode() finished")

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

            if lang is None:
                lang = lang_el.get("id")
                del lang_el.attrib["id"]

            lang_el.attrib["ident"] = fix_lang(lang)

    def convert_milestones_to_textparts(self):
        """
        Converts reffable milestones --- milestones whose `unit` attributes
        match the `n` attributes of a `cRefPattern` declared in the `refsDecl[@n='CTS']`
        --- into textparts by collecting all of the sibling nodes between one
        milestone and the next milestone with the same `unit` attribute and appending
        them as children to a new `<div type="textpart" subtype="unit" n="n">` where
        `"unit"` is the milestone's `unit` and `"n"` is its `n` attribute.
        """

        for milestone in self.tree.iterfind(f".//{TEI_NS}milestone"):
            current_unit = milestone.get("unit")

            if (
                current_unit in SKIPPABLE_MILESTONE_UNITS
                or current_unit not in self.refable_units
            ):
                continue

            siblings = []

            for sibling in milestone.itersiblings():
                if (
                    sibling.tag == f"{TEI_NS}milestone"
                    and sibling.get("unit") == current_unit
                ):
                    break
                siblings.append(sibling)

            if len(siblings) == 0:
                LOGGER.warn(
                    f"No siblings found for milestone {milestone.get('n')}; not converting."
                )
                continue

            div = DIV(
                type="textpart",
                subtype=current_unit,
                n=milestone.get("n", ""),
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

    def number_textparts(self, root=None):
        """
        Attempts to number textparts sequentially,
        starting from what should be the CTS
        root element at .//text/body/div.

        If this element is found, the function is
        called recursively with each textpart as root.

        If this element is not found, a warning is
        logged and the function becomes a noop.

        Note that there is an assumption that either all
        parts are numbered or no parts are numbered. Thus,
        something like,

        ```xml
        <div>
            <div n="2"></div>
            <div></div>
        </div>
        ```

        will result in the following:

        ```xml
        <div n="1">
            <div n="2"></div>
            <div n="1"></div>
        </div>
        ```

        because `n` was not incremented in the internal
        for-loop for the div[@n='2'] node.
        """
        LOGGER.debug("number_textparts() called")
        if root is None:
            maybe_root = self.tree.find(f".//{TEI_NS}text/{TEI_NS}body/{TEI_NS}div")

            if maybe_root is not None:
                self.number_textparts(maybe_root)
            else:
                LOGGER.warning("number_textparts() could not find a root node.")
        else:
            n = 1
            for part in root.iterfind(f"./{TEI_NS}div[@type='textpart']"):
                if part.get("n") is None:
                    LOGGER.info(f"Numbering {part} with with n={n}")
                    part.attrib["n"] = str(n)
                    n += 1

                # Start counting again using the current
                # textpart as root
                self.number_textparts(part)

    def pro_lege_manilia(self):
        if "sec00009.sec004" not in self.urn:
            return None

        for section in self.tree.iterfind(f".//{TEI_NS}div[@subtype='section']"):
            # First, move any milestones that are descendants of p tags
            # so that they are siblings.
            for milestone in section.iterfind(f".//{TEI_NS}milestone[@unit='pg_l']"):
                milestone_parent = milestone.getparent()

                if milestone_parent == section:
                    continue

                LOGGER.info(f"milestone_parent @n: {milestone_parent.get('n')}")
                LOGGER.info(f"milestone @n: {milestone.get('n')}")

                milestone_parent.addnext(milestone)

            # Then, starting from each milestone, take all of the siblings until we
            # reach the next milestone. These siblings should become the descendants
            # of the div[@subtype='subsection'] that will replace the milestone.
            for milestone in section.iterfind(f"./{TEI_NS}milestone[@unit='pg_l']"):
                siblings = []

                for sibling in milestone.itersiblings():
                    if sibling.tag == "milestone":
                        break
                    else:
                        siblings.append(sibling)

                n = milestone.get("n").replace(".", "_")
                div = DIV(
                    type="textpart",
                    subtype="subsection",
                    n=n,
                    *siblings,
                )

                section.append(div)

                milestone.getparent().remove(milestone)

    def remove_div_pg_l(self):
        LOGGER.info("remove_div_pg_l() called")
        for div_pg_l in self.tree.iterfind(f".//{TEI_NS}*[@subtype='pg_l']"):
            parent = div_pg_l.getparent()

            for child in div_pg_l:
                parent.append(child)

            parent.remove(div_pg_l)

    def remove_targOrder_attr(self):
        for el in self.tree.iterfind(".//*[@targOrder]"):
            del el.attrib["targOrder"]

    def uproot_smyth_parts(self):
        if "viaf20462595.viaf001" not in self.filename:
            return None

        self.uproot_sections()
        self.uproot_subsections()
        self.uproot_subsubsections()
        self.uproot_subsubsubsections()

    def uproot_sections(self):
        self.uproot_children_of("section")

    def uproot_subsections(self):
        self.uproot_children_of("subsection")

    def uproot_subsubsections(self):
        self.uproot_children_of("subsubsection")

    def uproot_subsubsubsections(self):
        self.uproot_children_of("subsubsubsection")

    def uproot_children_of(self, textpart_subtype: str):
        xpath_expr = f".//tei:div[@subtype='{textpart_subtype}']"

        LOGGER.info(f"Uprooting children of {textpart_subtype}")
        elements = self.tree.xpath(xpath_expr, namespaces=NAMESPACES)

        LOGGER.info(len(elements))
        for part in elements:
            LOGGER.info(part)
            parent = part.getparent()
            for child in part:
                part.addprevious(deepcopy(child))
            parent.remove(part)

    def write_etree(self):
        with open(self.filename, "wb") as f:
            etree.indent(self.tree, space="\t")
            f.write(etree.tostring(self.tree, encoding="utf-8", xml_declaration=True))
