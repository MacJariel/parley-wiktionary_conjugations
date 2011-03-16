#!/usr/bin/env kross
# -*- coding: utf-8 -*-
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
# Copyright 2011 MacJariel <macjariel@gmail.com>

import Parley
import mwclient
import re
import string

# Connected to the action menu
def fetchConjugations():
    print "wiktionary_conjugations.py: Fetching conjugations for selected translations."
    tr = Parley.selectedTranslations()
    for word in tr:
        fetchConjugationsForTranslation(word)

def fetchConjugationsForTranslation(word):
    locale = getLocale(word)
    wikiLocale = string.lower(locale[:2])
    conjugations = getConjugations(wikiLocale, word.text)
    if conjugations:
        applyConjugations(word, conjugations)

def applyConjugations(word, conjugations):
    print "wiktionary_conjugations.py: Adding conjugation of word %s." % (word.text)
    for tenseName in conjugations:
        tenseConjugations = conjugations[tenseName]
        for i in xrange(len(tenseConjugations)):
            if i / 3 == 0:
                flags = Parley.Singular
            else:
                flags = Parley.Plural
            
            if i % 3 == 0:
                flags |= Parley.First
            elif i % 3 == 1:
                flags |= Parley.Second
            else:
                flags |= Parley.Third | Parley.Neuter
            word.setConjugationText(tenseConjugations[i], tenseName, flags)

# locale of the given translation
def getLocale(trans):
    sel_entries = Parley.selectedEntries()
    for entry in sel_entries:
        for i in entry.translationIndices():
            if entry.translation(i).text == trans.text:
                return Parley.doc.identifier(i).locale

def getConjugations(lang, word):
    if not word:
        return None
    word = word.decode('utf-8')
    url = "http://en.wikitionary.org/wiki/%s" % word
    site = mwclient.Site('en.wiktionary.org')
    print "wiktionary_conjugations.py: Fetching %s" % url
    pageText = site.Pages[word].edit()

    # search for conj template
    match = re.compile('(\{\{%s-conj[^\}]+\}\})' % lang).search(pageText)
    if not match:
        print "wiktionary_conjugations.py: %s does not contain conjugations for language %s." % (url, lang)
        return None
    template = match.groups()[0]
    
    # get conjugation table
    conjText = site.expandtemplates(template)
    match = re.compile(r'\{\|(.*)\|\}', re.DOTALL).search(conjText)
    if not match:
        print "wiktionary_conjugations.py: Conjugation table on %s for language %s not found." % (url, lang)
        return None
    
    tableText = match.groups()[0]
    
    # remove hyperlink marks and extra whitespaces
    tableText = tableText.replace('[[', '').replace(']]', '')
    tableFields = tableText.split('|')
    tableFields = [' '.join(x.strip().split()) for x in tableFields]
    parser = getConjugationTableParser(lang)
    
    if parser:
        return parser(tableFields)
    else:
        print "wiktionary_conjugations.py: Language %s(%s) not supported" % (lang, lang)
        return None

def spanishParser(f):
    c = {}
    c[u'Presente de indicativo'] = f[35:41]
    c[u'Pretérito imperfecto de indicativo'] = f[43:49]
    c[u'Pretérito perfecto simple de indicativo'] = f[51:57]
    c[u'Futuro simple de indicativo'] = f[59:65]
    c[u'Conditional simple de indicativo'] = f[67:73]
    c[u'Presente de subjuntivo'] = f[84:90]
    c[u'Pretérito imperfecto de subjuntivo (-ra)'] = f[92:98]
    c[u'Pretérito imperfecto de subjuntivo (-se)'] = f[100:106]
    c[u'Futuro simple de subjuntivo'] = f[108:114]
    c[u'Imperativo positivo'] = f[125:131]
    c[u'Imperativo negativo'] = f[133:139]
    return c

def frenchParser(f):
    c = {}
    assert(f[46] == u"present")
    c[u"Présent de l'indicatif"] = f[47:53]
    assert(f[54] == u"imperfect")
    c[u"Imparfait de l'indicatif"] = f[55:61]
    assert(f[54] == u"imperfect")
    c[u"Passé simple de l'indicatif"] = f[63:69]
    c[u"Futur simple de l'indicatif"] = f[71:77]
    c[u"Présent du conditionnel"] = f[79:85]
    return c

def testParser(f):
    print "No parser defined for this language. The conjugation table follows:"
    for i in xrange(len(f)):
        print i, f[i]

def getConjugationTableParser(lang):
    if lang == 'es':
        return spanishParser
    elif lang == "fr":
        return frenchParser
    else:
        return testParser

#create a new action in Parley's script menu
action = Parley.newAction("fetch_conjugations","Fetch Conjugations")
action.statusTip="Fetches conjugations from en.wiktionary.org"
Parley.connect(action,"triggered()",fetchConjugations)

print "We got executed.."

