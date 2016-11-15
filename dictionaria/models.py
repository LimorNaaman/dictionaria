from __future__ import unicode_literals

from zope.interface import implementer
from sqlalchemy import (
    Column,
    Unicode,
    Integer,
    ForeignKey,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models import common
from clld.web.util.htmllib import HTML
from clld_glottologfamily_plugin.models import HasFamilyMixin

from dictionaria.util import split


@implementer(interfaces.ILanguage)
class Variety(CustomModelMixin, common.Language, HasFamilyMixin):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)


@implementer(interfaces.IContribution)
class Dictionary(CustomModelMixin, common.Contribution):
    """Contributions in WOW are dictionaries which are always related to one language.
    """
    pk = Column(Integer, ForeignKey('contribution.pk'), primary_key=True)
    language_pk = Column(Integer, ForeignKey('language.pk'))
    language = relationship('Language', backref='dictionaries')
    published = Column(Date)
    count_words = Column(Integer)
    count_audio = Column(Integer)
    count_image = Column(Integer)
    semantic_domains = Column(Unicode)

    def metalanguage_label(self, lang):
        style = self.jsondata['metalanguage_styles'].get(lang)
        style = "label label-{0}".format(style) if style else lang
        return HTML.span(lang, class_=style)


@implementer(interfaces.IParameter)
class ComparisonMeaning(CustomModelMixin, common.Parameter):
    pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
    concepticon_url = Column(Unicode)
    representation = Column(Integer)


@implementer(interfaces.IUnit)
class Word(CustomModelMixin, common.Unit):
    """Words are units of a particular language, but are still considered part of a
    dictionary, i.e. part of a contribution.
    """
    pk = Column(Integer, ForeignKey('unit.pk'), primary_key=True)
    semantic_domain = Column(Unicode)
    phonetic = Column(Unicode)
    #script = Column(Unicode)
    #borrowed = Column(Unicode)

    # original ...?

    # the concatenated values for the UnitParameter part of speech is stored denormalized.
    pos = Column(Unicode)

    dictionary_pk = Column(Integer, ForeignKey('dictionary.pk'))
    dictionary = relationship(Dictionary, backref='words')
    number = Column(Integer, default=0)  # for disambiguation of words with the same name

    @property
    def label(self):
        args = [self.name]
        if self.number:
            args.append(HTML.sup('{0}'.format(self.number)))
        return HTML.span(*args, **{'class': 'lemma'})

    @property
    def linked_from(self):
        return [(w.source, w.description) for w in self.source_assocs]

    @property
    def links_to(self):
        return [(w.target, w.description) for w in self.target_assocs]

    @property
    def description_list(self):
        return split(self.description)

    @property
    def semantic_domain_list(self):
        return split(self.semantic_domain)


class SeeAlso(Base):
    source_pk = Column(Integer, ForeignKey('word.pk'))
    target_pk = Column(Integer, ForeignKey('word.pk'))
    description = Column(Unicode())

    source = relationship(Word, foreign_keys=[source_pk], backref='target_assocs')
    target = relationship(Word, foreign_keys=[target_pk], backref='source_assocs')


class Meaning(Base, common.IdNameDescriptionMixin):
    word_pk = Column(Integer, ForeignKey('word.pk'))
    ord = Column(Integer, default=1)
    gloss = Column(Unicode)
    language = Column(Unicode, default='en')
    semantic_domain = Column(Unicode)
    reverse = Column(Unicode)
    alt_translation1 = Column(Unicode)
    alt_translation_language1 = Column(Unicode)
    alt_translation2 = Column(Unicode)
    alt_translation_language2 = Column(Unicode)

    @declared_attr
    def word(cls):
        return relationship(Word, backref=backref('meanings', order_by=[cls.ord]))

    @property
    def semantic_domain_list(self):
        return split(self.semantic_domain)


#
# FIXME: need relations between senses as well!
#


class MeaningSentence(Base):
    meaning_pk = Column(Integer, ForeignKey('meaning.pk'))
    sentence_pk = Column(Integer, ForeignKey('sentence.pk'))
    description = Column(Unicode())

    meaning = relationship(Meaning, backref='sentence_assocs')
    sentence = relationship(
        common.Sentence, backref='meaning_assocs', order_by=common.Sentence.id)


@implementer(interfaces.IValue)
class Counterpart(CustomModelMixin, common.Value):
    """Counterparts relate a word to a meaning, i.e. they are the values for meaning
    parameters.
    """
    pk = Column(Integer, ForeignKey('value.pk'), primary_key=True)

    word_pk = Column(Integer, ForeignKey('word.pk'))
    word = relationship(Word, backref='counterparts')


@implementer(interfaces.ISentence)
class Example(CustomModelMixin, common.Sentence):
    pk = Column(Integer, ForeignKey('sentence.pk'), primary_key=True)
    alt_translation1 = Column(Unicode)
    alt_translation_language1 = Column(Unicode)
    alt_translation2 = Column(Unicode)
    alt_translation_language2 = Column(Unicode)
    dictionary_pk = Column(Integer, ForeignKey('dictionary.pk'))
    dictionary = relationship(Dictionary, backref='examples')
