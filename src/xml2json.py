import json
import sqlite3
import re
import os
import subprocess
import sys
from collections import defaultdict, Counter


ID_PATTERN = re.compile(r'xml:id="(?P<id>\w+)"')
SRC_ID_PATTERN = re.compile(r'corresp="src:(?P<id>\w+)"')
TEXT_PATTERN = re.compile(
    r"""
    >
    (?P<text>[^<>]+)
    (
    </add>|
    </del>|
    </supplied>|
    </unclear>|
    </damage>
    )?</w>""",
    re.VERBOSE)
LEMMA_PATTERN = re.compile(r'lemmaRef="tla:(?P<lemma>\d+)"')
MDC_PATTERN = re.compile(r'ref="#(?P<MDC>\w+)"')
ADD_PATTERN = re.compile(r'<add place="(?P<place>\w+)">')
DEL_PATTERN = re.compile(r'<del rend="(?P<rend>\w+)">')
SUPP_PATTERN = re.compile(r'<supplied reason="(?P<reason>\w+)">')
# COORD_PATTERN = re.compile(r'n="\[(?P<coord>(Verso )?(A[m-q])?(\.)?(\d+,)?\d+\w?)\]"')
COORD_PATTERN = re.compile(r'n="\[(?P<coord>.+)\]"')
FEATS_PATTERN = re.compile(r'feats="(?P<feats>[^/]+)"')
TRNSC_PATTERN = re.compile(r'>(?P<chars>[^<]+)<')

POS_RENAMING_DICT = {
    'commonNoun':       'N',
    'mainVerb':         'VB',
    'pseudoParticiple': 'VB',
    'infinitive':       'VB',
    'participle':       'VB',
    'adjective':        'ADJ',
    'particle':         'PART',
    'relativePronoun':  'PRON',
    'numeral':          'NUM',
    'adverb':           'ADV',
    'cardinalNumeral':  'NUM',
    'personalPronoun':  'PRON',
}

all_features = set()

XML_PATH = sys.argv[1]


def LINE():
    return sys._getframe(1).f_lineno


def get_raw_word(line):
    buffer = []
    for match in TRNSC_PATTERN.finditer(line):
        buffer.append(match.group('chars'))
    return ''.join(buffer)


def get_sentences(witness_name):
    path = f'{XML_PATH}/{witness_name}.xml'
    sentences = {}
    sentence_id = None
    with open(path, 'r', encoding='utf-8') as inp:
        sentence = []
        for line in inp:
            if line.startswith('<s '):
                try:
                    sentence_id = ID_PATTERN.search(line).group('id')
                except AttributeError as e:
                    print(line, e, LINE())
                    input()
            elif line.startswith('<w'):
                sentence.append(get_raw_word(line))
            elif line.startswith('</s>'):
                assert sentence_id is not None
                sentences[sentence_id] = ' '.join(sentence)
                sentence = []
                sentence_id = None
    return sentences


def get_sentence_translations(witness_name):
    path = f'{XML_PATH}/{witness_name}_st.xml'
    translations = {}
    with open(path, 'r', encoding='utf-8') as inp:
        for line in inp:
            if line.startswith('<s '):
                sentence_id = SRC_ID_PATTERN.search(line).group('id')
                translations[sentence_id] = get_raw_word(line)
    return translations


def get_feats(feats_str):
    result = []
    for f in feats_str.split():
        tag, value = f.split(':')
        result.append(value)
        all_features.add((tag, value))
    return result


def get_word(word_line):
    lemma_match = LEMMA_PATTERN.search(word_line)
    if lemma_match:
        lemma = lemma_match.group('lemma')
    else:
        lemma = None

    # Check for additions/deletions
    add_match = ADD_PATTERN.search(word_line)
    del_match = DEL_PATTERN.search(word_line)
    supp_match = SUPP_PATTERN.search(word_line)
    if add_match:
        scribal = f'add: place={add_match.group("place")}'
    elif del_match:
        scribal = f'del: rend={del_match.group("rend")}'
    elif supp_match:
        scribal = f'supplied: reason={supp_match.group("reason")}'
    elif '<unclear>' in word_line:
        scribal = 'unclear'
    elif '<damage>' in word_line:
        scribal = 'damage'
    else:
        scribal = None

    # Extract features
    try:
        features = get_feats(
            FEATS_PATTERN.search(word_line).group('feats')
        )
    except AttributeError as e:
        print(word_line, e, LINE())
        input()
    for feature in features:
        if feature in POS_RENAMING_DICT:
            POS = POS_RENAMING_DICT[feature]
            break
    else:
        POS = None
    features = filter(lambda x: x not in POS_RENAMING_DICT, features)

    return {
        'id':                ID_PATTERN.search(word_line).group('id'),
        'lemma':             lemma,
        'textological_note': scribal,
        'part_of_speech':    POS,
        'features':          ', '.join(features)
    }


def get_transliterations(witness_name):
    transliteration = defaultdict(list)
    with open(f'{XML_PATH}/{witness_name}_hiero.xml',
              'r',
              encoding='utf-8'
              ) as inp:
        for line in inp:
            if line.startswith('<g'):
                try:
                    token_id = SRC_ID_PATTERN.search(line).group('id')
                except AttributeError as e:
                    print(line, e, LINE())
                    continue
                if line.startswith('<gap'):
                    mdc = ''
                else:
                    try:
                        mdc = MDC_PATTERN.search(line).group('MDC')
                    except AttributeError as e:
                        print(line, e, LINE())
                        continue
                transliteration[token_id].append(mdc)
    for token_id, mdc_buffer in transliteration.items():
        transliteration[token_id] = '-'.join(mdc_buffer)
    return transliteration


def get_translations(witness_name):
    translation = {}
    with open(f'{XML_PATH}/{witness_name}_wt.xml',
              'r',
              encoding='utf-8'
              ) as inp:
        for line in inp:
            if line.startswith('<w '):
                try:
                    token_id = SRC_ID_PATTERN.search(line).group('id')
                except AttributeError as e:
                    print(line, e, LINE()-2)
                    input()
                try:
                    meaning = TEXT_PATTERN.search(line).group('text')
                except AttributeError as e:
                    print(line, e, LINE()-2)
                    meaning = '?'
                translation[token_id] = meaning
    return translation


def process_witness(witness_name, coordinates=None):
    sentences = get_sentences(witness_name)
    sentence_translations = get_sentence_translations(witness_name)
    token_transliterations = get_transliterations(witness_name)
    token_translations = get_translations(witness_name)
    words = []
    with open(f'{XML_PATH}/{witness_name}.xml', 'r', encoding='utf-8') as inp:
        for line in inp:
            line = line.strip()

            # Strip addName and persName tags
            # <addName type="epithet" subtype="deity">
            if line.startswith('<addName type="epithet" subtype="deity">'):
                line = line[
                    len('<addName type="epithet" subtype="deity">'):
                    -len('</addName>')
                ]
            # <addName type="epithet" subtype="royal">
            elif line.startswith('<addName type="epithet" subtype="royal">'):
                line = line[
                    len('<addName type="epithet" subtype="royal">'):
                    -len('</addName>')
                ]
            # <persName type="deity">
            elif line.startswith('<persName type="deity">'):
                line = line[
                    len('<persName type="deity">'):
                    -len('</persName>')
                ]
            # <persName type="royal">
            elif line.startswith('<persName type="royal">'):
                line = line[
                    len('<persName type="royal">'):
                    -len('</persName>')
                ]
            # <name type="institution">
            elif line.startswith('<name type="institution">'):
                line = line[
                    len('<name type="institution">'):
                    -len('</name>')
                ]
            # <name type="object">
            elif line.startswith('<name type="object">'):
                line = line[
                    len('<name type="object">'):
                    -len('</name>')
                ]
            # <persName>
            elif line.startswith('<persName>'):
                line = line[
                    len('<persName>'):
                    -len('</persName>')
                ]
            # <placeName>
            elif line.startswith('<placeName>'):
                line = line[
                    len('<placeName>'):
                    -len('</placeName>')
                ]
            # <roleName>
            elif line.startswith('<roleName>'):
                line = line[
                    len('<roleName>'):
                    -len('</roleName>')
                ]

            if line.startswith('<s '):
                sentence_id = ID_PATTERN.search(line).group('id')
                sentence = sentences[sentence_id]
                sentence_translation = sentence_translations.get(
                    sentence_id, '???')
            elif line.startswith('<lb'):
                try:
                    coordinates = COORD_PATTERN.search(line).group('coord')
                except AttributeError as e:
                    print(line, e, LINE())
                    input()
            elif line.startswith('<w '):
                token = get_word(line)
                token['MDC'] = token_transliterations.get(token['id'], None)
                token['meaning'] = token_translations.get(token['id'], None)
                token['syntactic_relation'] = sentence + \
                    ' ’' + sentence_translation + '’'
                # Coordinates can be none at the beginning of the first section
                # but never afterwards.
                assert coordinates is not None
                token['coordinates'] = coordinates
                words.append(token)
    return words, coordinates


def none2str(inp):
    if inp is None:
        return ''
    else:
        return inp


def get_translations_from_aaew_record(record):
    if 'translations' not in record:
        return ''
    trans_dict = record['translations']
    return 'en: ' + none2str(trans_dict.get('en', '')) + '; de: ' + none2str(trans_dict.get('de', ''))


def extract_comments(token_dict):
    if token_dict['textological_note'] is not None and \
            token_dict['textological_note'] != '':
        textological_note = token_dict['textological_note']
    else:
        textological_note = ''

    if token_dict['features'] is not None and \
            token_dict['features'] != '':
        features_str = token_dict['features']
    else:
        features_str = ''

    if textological_note and features_str:
        return f'{textological_note}; {features_str}'
    elif textological_note:
        return textological_note
    else:  # Will return '' in the default case.
        return features_str


if __name__ == "__main__":
    # The dictionary for lemma transliterations and meanings
    with open(f'aaew_wlist_small.json', 'r', encoding='utf-8') as inp:
        aaew = json.load(inp)
    db_filename = f'clf_{XML_PATH.split("/")[-1].replace(" ", "_").replace(",", "")}.db'
    # Delete the database file if it exists.
    subprocess.run(['rm', db_filename])
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    with open(f'initialise_db.sql', 'r', encoding='utf-8') as inp:
        initialisation_script = inp.read()
    cursor.executescript(initialisation_script)

    pos_counts = Counter()
    witnesses = set()
    for fname in os.listdir(XML_PATH):
        if fname.endswith('.xml'):
            witnesses.add(fname.split('.')[0].split('_')[0])
    all_lemma_ids = set()
    coordinates = None
    for witness_id, witness in enumerate(sorted(witnesses)):
        witness_id += 1
        print(witness, witness_id)
        try:
            tokens, coordinates = process_witness(witness, coordinates)
            for t in tokens:
                if t['lemma'] is not None:
                    all_lemma_ids.add(t['lemma'])
                pos_counts[t['part_of_speech']] += 1
                cursor.execute(
                    """
                    INSERT INTO tokens (
                        `witness_id`,
                        `coordinates_in_witness`,
                        `lemma_id`,
                        mdc,
                        `context_meaning`,
                        `syntactic_relation`,
                        pos,
                        comments
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        witness_id,
                        t['coordinates'],
                        t['lemma'],
                        t['MDC'],
                        t['meaning'],
                        t['syntactic_relation'],
                        t['part_of_speech'],
                        extract_comments(t)
                    ))
        except FileNotFoundError as e:
            print(e)
            continue

    # Add lemmas to the lemma table
    for lemma_id in sorted(all_lemma_ids):
        if str(lemma_id) not in aaew:
            transliteration = '?'
            meaning = '?'
        else:
            transliteration = aaew[str(lemma_id)]['name']
            meaning = get_translations_from_aaew_record(aaew[str(lemma_id)])
        cursor.execute(
            """
            INSERT INTO lemmas (
                id,
                transliteration,
                meaning
            ) VALUES (?,?,?)
            """,
            (lemma_id, transliteration, meaning))

    conn.commit()

    print(pos_counts.most_common())


# print(all_features)

# with open('../json/words.json', 'w', encoding='utf-8') as out:
#     json.dump(words, out, indent=2, ensure_ascii=False)
# ebers_df = pd.DataFrame.from_records(words)
# ebers_df = ebers_df[['text', 'lemma', 'MDC',
#                      'meaning', 'part_of_speech', 'features',
#                      'coordinates', 'textological_note']]
# ebers_df.to_excel('ebers_tokens.xlsx', index=False)
