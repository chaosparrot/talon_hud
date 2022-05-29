from speech_types import WordInfo

def determine_oo(info: WordInfo, index: int) -> list:
    r_pos = info.vowel_clusters[index].end_pos + 1
    c_pos = info.vowel_clusters[index].start_pos - 1
    # dOOr
    if r_pos < info.word_len and info.word[r_pos] == "r":
        return ["ɔː"]
    # cOOrdinate
    elif len(info.vowel_clusters[index]) > 1 and c_pos > 0 and info.word[c_pos] == "c":
        return ["əʊ", "ɒ"]
    # bOOt
    else:
        return ["ʊ"]

def determine_oe(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    # tOE
    syllable = ["əʊ"]
    
    # shOE
    if pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] == "s" and info.word[pushing_pos] == "h":
        syllable = ["ʊ"]
    
    elif trailing_pos < info.word_len:
        # macrOElectric
        if info.word[trailing_pos] in "qlvc":
            syllable.append("i:")
            
        elif info.word[trailing_pos] == "r":
            # dOEr
            if info.word[pushing_pos] == "d":
                syllable = ["ʊ", "ə"]
            # gOEr, cOEr
            else:
                syllable.append("ə")
        # cOExist
        elif info.word[trailing_pos] not in "nts":
            syllable.append("e")
    return syllable

def determine_oi(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1

    if pushing_pos >= 0:
        if trailing_pos + 1 < info.word_len and info.word[trailing_pos] == "n" \
            and info.word[trailing_pos + 1] == "g":
            # dOIng
            if info.word[pushing_pos] == "d":
               return ["ʊ", "ɪ"]
            # gOIng               
            else:
               return ["əʊ", "ɪ"]            
        
        # cOIntegrate
        elif info.word[pushing_pos] == "c" and len(info.vowel_clusters) > 1:
           return ["əʊ", "ɪ"]
    # OIl, cOIn
    return ["ɔɪ"]

def determine_ow(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    # rOW, grOW, blOW, stOW, glOW, thrOW, lOW
    previous_two_letters = ""
    if pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] in "bshg":
        previous_two_letters += info.word[pushing_pos - 1]
    if pushing_pos >= 0:
        previous_two_letters += info.word[pushing_pos]
    if any(previous_two_letters in s for s in ["gr", "r", "st", "hr"]) or \
        previous_two_letters.endswith("l"):
        return ["əʊ"]

    # cOW, OWl, brOWn, tOWn
    return ["aʊ"]

english_vowel_cluster_determine_map = {
    "oo": determine_oo,
    "oe": determine_oe,
    "oi": determine_oi,
    "ow": determine_ow, 
}

unambiguous_syllables = {
    "eau": ["u:"],
    "aa": ["ɑ:"],
    "au": ["ɔ:"],
    "ay": ["eɪ"],
    "ayi": ["eɪ", "ɪ"],    
    "ayo": ["eɪ", "əʊ"],
    "aw": ["ɔ:"],
    "awi": ["ɔ:", "ɪ"],
    "ew": ["u:"],
    "ewi": ["u:", "ɪ"],
    "uy": ["aɪ"],
    "uyi": ["aɪ", "ɪ"],
    "uou": ["u:", "ə"],
    "ueue": ["u:"],
    "uei": ["u:", "ɪ"],
    "ueuei": ["u:", "ɪ"],
    "uu": ["u:"],
    "oy": ["ɔɪ"],
    "oyi": ["ɔɪ", "ɪ"],
    "uie": ["aɪ", "ə"],
    "uia": ["i:", "ə"],
    "uiu": ["i:", "ə"],    
    "ioa": ["i:", "əʊ", "e"],   
    "ooi": ["u:", "ɪ"],
}

for item in unambiguous_syllables.items():
    syllable = item[1]
    english_vowel_cluster_determine_map[item[0]] = lambda _, _2, syllable=syllable: syllable