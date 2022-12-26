import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np


class Definition:
    def __init__(self, meaning=None, pos=None, stem=None, conjugation=None, tense=None):
        self.meaning = meaning
        self.pos = pos
        self.stem = stem
        self.conjugation = conjugation
        self.tense = tense

    def __str__(self):
        return f"Meaning: {self.meaning}, pos: {self.pos}, stem: {self.stem}, conjugation: {self.conjugation}, tense: {self.tense}"

    def __eq__(self, other):
        return self.meaning == other.meaning and self.pos == other.pos and self.stem == other.stem and self.conjugation == other.conjugation and self.tense == other.tense


class Word:
    def __init__(self, word, defs):
        self.word = word
        self.defs = defs


conjs = ['yo', 'tú', 'él/ella/usted', 'nosotros', 'vosotros', 'ellos/ellas/ustedes']
ind_tenses = ['Present', 'Preterite', 'Imperfect', 'Conditional', 'Future']
subj_tenses = ['Present', 'Imperfect', 'Future']
imp_tenses = ['Affirmative', 'Negative']
prog_tenses = ['Present', 'Preterite', 'Imperfect', 'Conditional',
               'Future']
perf_tenses = ['Present', 'Preterite', 'Past', 'Conditional', 'Future']
perf_subj_tenses = ['Present', 'Past', 'Future']

tense_group = ['Indicative', 'Subjunctive', 'Imperative', 'Progressive', 'Perfect', 'Perfect Subjunctive']
tense_group_lists = [ind_tenses, subj_tenses, imp_tenses, prog_tenses, perf_tenses, perf_subj_tenses]


def get_examples_for_word(word):
    page = requests.get(f'https://www.spanishdict.com/examples/{word}?lang=es')
    soup = BeautifulSoup(page.content, "html.parser")
    examples = pd.DataFrame(columns=['es', 'en'])

    # indicative
    try:
        examples_table = soup.find("table", class_="pczAfAy5")
        rows = examples_table.find_all("tr")

        for i, row in enumerate(rows):
            cols = row.find_all("td")

            new_df = pd.DataFrame(
                data={'es': cols[0].text.strip(), 'en': cols[1].text.strip()}, index=[0])
            examples = pd.concat([examples, new_df], ignore_index=True)
        return examples
    except:
        return examples


def get_all_conjugations(word):
    page = requests.get(f'https://www.spanishdict.com/conjugate/{word}')
    soup = BeautifulSoup(page.content, "html.parser")

    tenses = {}
    try:
        conjs_table = soup.find_all("table", class_="xus0pkCd")

        for i, tense_gr in enumerate(tense_group_lists):
            table = conjs_table[i]
            rows = table.find_all("tr")
            tenses[tense_group[i]] = {}
            for j, row in enumerate(rows[1:]):
                cols = row.find_all("td")
                for k, col in enumerate(cols[1:]):
                    if j == 0:
                        tenses[tense_group[i]][tense_group_lists[i][k]] = {}
                    tenses[tense_group[i]][tense_group_lists[i][k]][conjs[j]] = col.text.strip()

        return tenses
    except:
        return tenses


def get_word_info(word):
    definitions = []

    page = requests.get(f'https://www.spanishdict.com/translate/{word}')
    soup = BeautifulSoup(page.content, "html.parser")

    # try:
    defs_box = soup.find("div", class_="RXc30NZF")
    upper_defs = defs_box.find_all("div", recursive=False)

    for defs in upper_defs:
        lines = defs.find_all("div", recursive=False)
        curr_def = []
        for line in lines:
            if 'conjugation of' in line.text.strip():
                words = line.find_all("span")
                tense = words[0].text.strip()
                conjugation = words[1].text.strip()
                stem = words[3].text.strip()
                curr_def = Definition(meaning=curr_def, tense=tense, conjugation=conjugation, stem=stem, pos='verb')
                definitions.append(curr_def)
            elif f"{word}" in line.text.strip():
                words = line.find_all("a")
                for curr_word in words:
                    curr_def.append(curr_word.text.strip())
    # except:
    #     pass

    try:
        dict_box = soup.find("div", id="dictionary-neodict-es")

        all_spans = dict_box.find_all("span")
        for num in range(10):
            for i, span in enumerate(all_spans):
                if f"{num}." in span.text.strip():
                    span_group = span.parent.parent
                    group_defs = span_group.find_all("div")
                    for group in group_defs:
                        defs = group.find_all("a")
                        for def_ in defs:
                            if def_.text.strip().startswith("to "):
                                new_def = Definition(meaning=def_.text.strip(), pos="verb")
                            else:
                                new_def = Definition(meaning=def_.text.strip(), pos="noun")
                            if new_def not in definitions:
                                definitions.append(new_def)
                        # print(defs)
                    # for def_ in defs:
                    #     print(def_.text.strip())
                    #     new_def = Definition(meaning=def_.text.strip(), pos="noun")
                    #     definitions.append(new_def)
                    # all_spans = all_spans[i+1:]
    except:
        pass

    word = Word(word, definitions)
    return word


def get_all_example_sentences(no_egs):
    difficulty = input('Difficulty: easy->hard 1-10: ')

    examples = pd.DataFrame(columns=['es', 'en', 'word_to_remove'])

    verbs = []
    import csv
    with open('verbs.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            verbs.append(row[0])

    verb_selections = np.random.normal(loc=(int(difficulty) / 10) * len(verbs), scale=len(verbs) * 0.2, size=no_egs)
    verb_selections = np.clip(verb_selections, 1, len(verbs) - 1)

    tense_selections = input("Difficulty: 0='Indicative', 1='Subjunctive', 2='Imperative', 3='Progressive', "
                             "4='Perfect', 5='Perfect Subjunctive'")

    tenses = [tense_group[int(sel)] for sel in tense_selections.split()]

    print("\nGetting sentences...")

    for verb_no in verb_selections:
        try:
            verb = verbs[int(verb_no)]

            print(f"Getting sentences for verb {verb}")
            verb_forms = get_all_conjugations(verb)

            for tense in tenses:
                verb_forms_to_get_egs = list(verb_forms[tense].values())[0].values()
                for verb_form_to_get_egs in verb_forms_to_get_egs:
                    egs = get_examples_for_word(verb_form_to_get_egs)
                    egs['word_to_remove'] = verb_form_to_get_egs
                    examples = pd.concat([examples, egs], ignore_index=True)
        except:
            pass
        
    return examples


to_remove = ['.', ',', ':', '!', '?', ';', '¿', '¡']


def clean_word(word):
    for char in to_remove:
        word = word.replace(char, '')
    return word


def test_on_examples(egs):
    ans = ''
    while ans != 'end':
        row = egs.sample()
        word_to_remove = row.iloc[0]['word_to_remove']
        row_replaced = row.iloc[0]['es'].replace(word_to_remove, ' ___ ')
        get_word_info(word_to_remove)
        print(f"\n\n{row.iloc[0]['en']}\n{row_replaced}")
        ans = input("Your answer: ")
        ans = clean_word(ans)
        if ans.lower() == word_to_remove.lower():
            print("CORRECT!")
        else:
            print(f"INCORRECT! the answer was {word_to_remove}")


if __name__ == "__main__":
    # word = get_word_info("esté")
    # print(word.word)
    # print([{str(def_)} for def_ in word.defs])
    examples = get_all_example_sentences(10)
    test_on_examples(examples)
