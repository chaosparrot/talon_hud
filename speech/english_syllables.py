from speech_types import WordInfo

def determine_oo(info: WordInfo, index: int) -> list:
    r_pos = info.vowel_clusters[index].end_pos + 1
    c_pos = info.vowel_clusters[index].start_pos - 1
    # dOOr, flOOr
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

    # OWn
    if info.word == "own":
        return ["əʊ"]
    
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
    
def determine_owe(info: WordInfo, index: int) -> list:
    syllable = determine_ow(info, index)
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    # pOWEr, grOWer, slOWer, bOWEl
    if trailing_pos < info.word_len and info.word[trailing_pos] in "rnl":
        syllable.append("ə")    

    return syllable
    
def determine_owi(info: WordInfo, index: int) -> list:
    # grOWIng
    syllable = determine_ow(info, index)
    syllable.append("ɪ")
    return syllable
    
def determine_ou(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    # anonymOUs
    if trailing_pos < info.word_len and info.word[trailing_pos] in "s":
        return ["ə"]

    # trOUble, cOUrage
    elif trailing_pos < info.word_len and info.word[trailing_pos] in "rb" and \
        pushing_pos >= 0 and info.word[pushing_pos] in "cr":
        return ["ʌ"]
    elif trailing_pos + 1 < info.word_len and \
        info.word[trailing_pos] + info.word[trailing_pos + 1] == "ld":
        
        # cOUld, shOUld, wOUld
        if any(info.word in s for s in ["could", "should", "would"]):
            return ["ʊ"]
        # bOUlder, shOUlder
        else:
            return ["əʊ"]
            
    # sOUnd, mOUth, OUt, lOUd, nOUn
    return ["aʊ"]
    
def determine_oa(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1

    # bOArd
    if trailing_pos < info.word_len and info.word[trailing_pos] == "r":
        return ["ɔː"]
    pushing_pos = info.vowel_clusters[index].start_pos - 1

    # cOAlition - TODO proper a sound determining
    if len(info.vowel_clusters) > 1 and pushing_pos >= 0 and info.word[pushing_pos] in "c":
       return ["əʊ", "ə"]
    
    # lOAn, grOAn
    return ["əʊ"]

def determine_ue(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    if pushing_pos >= 0 and info.word[pushing_pos] in "q":
        # technique
        if len(info.vowel_clusters) > 1:
            if index == len(info.vowel_clusters) - 1 and \
                ( info.word.endswith("ue") or info.word.endswith("ues") ):
                return [""]
                
            # freqUEnt, qUEry, seqUEnce
            if trailing_pos < info.word_len and info.word[trailing_pos] in "rn":
                return ["ə"]
        # qUEst
        return ["e"]

    # gUEss, gUEst
    if pushing_pos >= 0 and info.word[pushing_pos] in "g" and \
        trailing_pos < info.word_len and info.word[trailing_pos] == "s":
        return ["e"]
    
    # rescUEr, flUEnt    
    syllable = ["u:"]
    if trailing_pos < info.word_len and info.word[trailing_pos] in "rn":
        syllable.append("ə")

    # cUE, blUE
    return syllable
    
def determine_ui(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1

    if pushing_pos >= 0:
        # liQUId, qUIck, qUIll, extingUIsh, gUIlt, circUIt, sqUIsh
        if info.word[pushing_pos] in "qgc":
            return ["ɪ"]
        trailing_pos = info.vowel_clusters[index].end_pos + 1        
        if trailing_pos < info.word_len:
            # nUIsance
            if info.word[pushing_pos] == "n" and info.word[trailing_pos] == "s":
                return ["u:"]
            
            # frUIt            
            elif pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] + info.word[pushing_pos] == "fr":
                return ["u:"]

    # flUId, sUIcide, argUIng, rUIn
    return ["u:", "ɪ"]
    
def determine_ua(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    if pushing_pos >= 0 and trialing_pos < info.word_len:
        if info.word[pushing_pos] in "q":
            # qUArter        
            if info.word[trailing_pos] == "r":
                return ["ɔː"]
            # eqUAl
            else:
                return ["ɒ"]
        if info.word[pushing_pos] in "g" and info.word[trailing_pos] == "r":
           # gUArantee
           if index + 1 < len(info.vowel_clusters) and info.vowel_clusters[index + 1] == "a":
                return ["æ"]
           # gUArd
           else:
                return ["ɑ:"]

    # strenUOs
    return ["u:", "ə"]
    
def determine_uo(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    if pushing_pos >= 0 and trialing_pos < info.word_len:
        if info.word[pushing_pos] in "qc":
            # liqUOr, viscUOs
            if info.word[trailing_pos] in "rs":
                return ["ə"]
            # qUOte
            return ["əʊ"]
            
        # flUOrescent, virtUOse
        if info.word[pushing_pos] in "tl":
            return ["u:", "ə"]
    # dUO
    return ["u:", "əʊ"]

english_vowel_cluster_determine_map = {
    "oo": determine_oo,
    "oe": determine_oe,
    "oi": determine_oi,
    "ow": determine_ow,
    "owe": determine_owe,
    "owi": determine_owi,
    "ou": determine_ou,
    "oa": determine_oa,
    "ue": determine_ue,
    "ui": determine_ui,
    "ua": determine_ua,
    "uo": determine_uo,
    # "ae": 
    # "ai":     
    # "ao":
    # "ie": 
    # "iu":     
    # "ia":    
    # "io":
    # "ee":
    # "eu":    
    # "ea":
    # "eo":
    # "ei":
    # Single letter
    #"o":
    #"u":
    #"a":
    #"i":    
    #"y":    
    #"e":    
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
    "eou": ["ə"],
    "uou": ["u:", "ə"],
    "ueue": ["u:"],
    "uoi": ["ɔ:"],    
    "uei": ["u:", "ɪ"],
    "uee": ["u:", "i:"],
    "ueuei": ["u:", "ɪ"],
    "uu": ["u:"],
    "uoy": ["ɔɪ"],
    "uoya": ["ɔɪ", "ə"],
    "oy": ["ɔɪ"],
    "oyi": ["ɔɪ", "ɪ"],
    "uie": ["aɪ", "ə"],
    "uia": ["i:", "ə"],
    "uiu": ["i:", "ə"],    
    "ioa": ["i:", "əʊ", "e"],
    "ooi": ["u:", "ɪ"],
    "oei": ["əʊ", "ɪ"],
}

for item in unambiguous_syllables.items():
    syllable = item[1]
    english_vowel_cluster_determine_map[item[0]] = lambda _, _2, syllable=syllable: syllable