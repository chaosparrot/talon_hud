def string_to_speakable_string(str: str) -> str:
    return re.sub(r"([!?-_\,\.])", " ", str.lower()).strip()
    
english_ipa_vowels = {
    "e": "/ae/", # wEnt, ExpEnsive
    "æ": "/ae/", # cAt
    "ʌ": "/uh/", # fUn, mOney
    "ʊ": "/oo/", # lOOk, shOUld
    "ɒ": "/oh/", # rOb, tOrn
    "ə": "/er/", # strangER
    "ɪ": "/ih/", # sIt, kIt, Inn
    "i:": "/iy/", # nEEd, lEAn
    "ɜ:": "/eu/", # nUrse, sErvice, bIrd
    "ɔ:": "/oh/", # tAlk, jAw
    "u:": "/u/", # bOOt, qUEUE
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


vowel_map = {
    "o": ["ɒ"],
    "oo": ["u:"],
    "ou": ["aʊ"],    
    "oi": ["ɔɪ"],
    "oa": ["əʊ"],
    "ioa": ["i:", "əʊ", "e"],
    "uou": ["u:", "ə"],
    "y": ["i:"],
    "yi": ["aɪ", "ɪ"],
    "ya": ["aɪ", "ə"],
    "ey": ["i:"],
    "eyi": ["ɜ:", "eɪ", "ɪ"],
    "uy": ["aɪ"],
    "uyi": ["aɪ", "ɪ"],
    "oy": ["ɔɪ"],
    "oye": ["ɔɪ"],
    "ay": ["eɪ"],
    "aye": ["eɪ"],    
    "ayo": ["eɪ", "əʊ"],
    "ui": ["ɪ"],
    "uie": ["aɪ", "ə"],
    "uia": ["i:", "ə"],
    "uiu": ["i:", "ə"],    
    "uo": ["əʊ"],
    "uou": ["u:", "ə"],
    "ue": ["u:"],
    "ueue": ["u:"],
    "uu": ["u:"],
    "u": ["ʌ"],
    "aa": ["ɑ:"],
    "ae": ["æ"],
    "ai": ["eɪ"],
    "au": ["ɔ:"],
    "ao": ["ɔː"],
    "a": ["eɪ"],
    "ia": ["i:", "ə"],    
    "ie": ["i:", "ə"],    
    "io": ["ə"],
    "ii": ["i:", "ɪ"],
    "iu": ["i:", "ə"],
    "i": ["ɪ"],
    "eo": ["i:", "ɔ:"],
    "eau": ["u:"],
    "eu": ["u:"],
    "ei": ["eɪ"],
    "ee": ["i:"],
    "ea": ["ɪə"],
    "e": ["ə"],
}

def word_to_approx_vowels(word: str, lang:str = "en") -> list:
    """Takes a word and turns it into an approximate list of IPA vowels"""
    vowels = []
    first_vowel = True
    previous_is_vowel = False
    current_vowels = ""
    for index, char in enumerate(word):
        final_char = (index + 1) == len(word)
        if char in "iaeuo":
            current_vowels += char
        if final_char or char not in "iaeuo":
            if current_vowels in vowel_map:
                if not (final_char and char == "e" and current_vowels == "e"):
                    syllable = vowel_map[current_vowels]
                    vowels.extend(syllable)
                    if first_vowel:
                        first_vowel = False
            elif final_char and char == "y":
                vowels.extend(vowel_map[char])
            current_vowels = ""
    
    return vowels
    