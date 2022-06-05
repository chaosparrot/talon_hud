from english_syllables import english_vowel_cluster_determine_map
from speech_types import WordInfo, VowelCluster

def string_to_speakable_string(str: str) -> str:
    return re.sub(r"([!?-_\,\.])", " ", str.lower()).strip()
    
english_ipa_vowels = {
    "e": "/ae/",  # wEnt, ExpEnsive
    "æ": "/ae/",  # cAt
    "ʌ": "/uh/",  # fUn, mOney
    "ʊ": "/oo/",  # lOOk, bOOt, shOUld
    "ɒ": "/oh/",  # rOb, tOrn
    "ə": "/er/",  # evEn
    "ɪ": "/ih/",  # sIt, kIt, Inn
    "i:": "/iy/", # nEEd, lEAn
    "ɜ:": "/eu/", # nUrse, sErvice, bIrd
    "ɔ:": "/oh/", # tAlk, jAw
    "u:": "/u/",  # qUEUE
    "ɑ:": "/ah/", # fAst, cAr
    "ɪə": "/iy/", # fEAr, bEEr
    "eə": "/ae/", # hAIr, stAre
    "eɪ": "/ay/", # spAce, stAIn, EIght
    "ɔɪ": "/oy/", # jOY, fOIl
    "aɪ": "/ai/", # mY, stYle, kInd, rIght
    "əʊ": "/ow/", # nO, blOWn, grOWn, rObe
    "aʊ": "/au/", # mOUth, tOWn, OUt, lOUd
}

english_letters_to_ipa_vowels = {
    "a": "eɪ",
    "b": "i:",
    "c": "i:",
    "d": "i:",
    "e": "i:",
    "f": "e",
    "g": "i:",
    "h": "eɪ",
    "i": "aɪ",
    "j": "eɪ",
    "k": "eɪ",
    "l": "e",
    "m": "e",
    "n": "e",
    "o": "əʊ",
    "p": "i:",
    "q": "u",
    "r": "ɑ:",
    "s": "e",
    "t": "i:",    
    "u": "u",
    "w": "ʌ ə u",
    "v": "i:",
    "x": "e",
    "y": "aɪ",
    "z": "i:",    
}

def acronym_to_approx_vowels(acronym: str, lang:str = "en") -> list:
    """Takes an acronym and turns it into an approximate list of IPA vowels"""
    vowels = []
    for letter in acronym:
        vowels.extend(english_letters_to_ipa_vowels[letter.lower()].split(" "))
    return vowels

def get_word_info(word: str, lang:str = "en") -> list:
    """Takes a word and turns it into an approximate list of syllable clusters containing vowels"""
    info = WordInfo(word, len(word), [])
    current_vowels = ""
    for index, char in enumerate(word):
        final_char = (index + 1) == len(word)
        if char in "iaeuowy":
            current_vowels += char
        if final_char or char not in "iaeuowy":
            # Remove Y and W from the start of syllable clusters
            if current_vowels.startswith("w"):
                current_vowels = current_vowels[1:]
            if current_vowels.startswith("y") and len(current_vowels) > 1:
                current_vowels = current_vowels[1:]
            if len(current_vowels) > 0:
                start_pos = info.word_len - len(current_vowels) if final_char and char in "iaeuowy" else index - len(current_vowels)            
                end_pos = start_pos + len(current_vowels) - 1
                info.vowel_clusters.append(VowelCluster(current_vowels, start_pos, end_pos))
            current_vowels = ""
            
    return info

def word_to_approx_vowels(word: str, lang:str = "en") -> list:
    """Takes a word and turns it into an approximate list of IPA vowels"""
    vowels = []
    first_vowel = True
    
    info = get_word_info(word)
    
    # If there are no vowel clusters, immediately go for an acronym spelling
    if len(info.vowel_clusters) == 0:
        return acronym_to_approx_vowels(word, lang)
    else:
        for index in range(0, len(info.vowel_clusters)):
            cluster = info.vowel_clusters[index]
            if cluster.vowels in english_vowel_cluster_determine_map:
                new_vowels = english_vowel_cluster_determine_map[cluster.vowels](info, index)
                vowels.extend(list(filter(bool,new_vowels)))
    
    return vowels
    