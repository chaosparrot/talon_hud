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
    
    # yOU, yOUr
    if pushing_pos >= 0 and info.word[pushing_pos] == "y":
        syllable = ["ʊ"]
        
        if trailing_pos < info.word_len and info.word[trailing_pos] == "r":
            syllable.append("ə")
        return syllable
    
    # anonymOUs
    if trailing_pos < info.word_len and info.word[trailing_pos] == "s":
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

def determine_ae(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    # metAEthical
    if len(info.vowel_clusters) > 2 and pushing_pos >= 0 and info.word[pushing_pos] in "t":
        return ["ɑ:", "æ"]

    if trialing_pos < info.word_len and info.word[trailing_pos] in "rs":
        # AEro, AEstetic
        return ["æ"]

    # prAEtor, florAE
    return ["eɪ"]
    
def determine_ai(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    # metAEthical
    if len(info.vowel_clusters) > 2 and pushing_pos >= 0 and info.word[pushing_pos] in "t":
        return ["ɑ:", "æ"]

    if trialing_pos < info.word_len: 
        # AIr, fAIr, stAIrs    
        if info.word[trailing_pos] in "r":
            return ["æ"]
            
        # algebrAIc
        elif info.word[trailing_pos] in "c":
            return ["eɪ", "ɪ"]
        # AIr
        return ["æ"]

    # plAIn, rAIn, AIlments
    return ["eɪ"]
    
def determine_ao(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    # extrAOrdinary
    if pushing_pos >= 0 and info.word[pushing_pos] == "r":
        return ["ɑ:", "ɒ"]

    # chAOtic
    return ["eɪ", "ɒ"]
    
def determine_ie(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    if trailing_pos < info.word_len:         

        if info.word[trailing_pos] in "rt":
            # pIErce, fIErce
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "c":
                return ["ɪə"]

            # multiplIEr, sobrIEty 
            return ["aɪ", "ə"]

        # experIEnce, convinIEnt
        elif info.word[trailing_pos] == "n":
            return ["i:", "ə"]

        # serIEs, achIEve, chIEf, pIEce, fIEld, prIEst
        elif info.word[trailing_pos] in "svfcl":
            return ["i:"]
    
    # dIE, pIE, classifIEd
    return ["aɪ"]
    
def determine_iu(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    if pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] + info.word[pushing_pos] == "tr":
        trailing_pos = info.vowel_clusters[index].end_pos + 1
        # trIUmph        
        if trailing_pos + 1 < info.word_len and info.word[trailing_pos] + info.word[trailing_pos + 1] == "mp":
            return ["aɪ", "ʌ"]
    
    # odIUm, premIUm, genIUs
    return ["i:", "ə"]
    
def determine_ia(info: WordInfo, index: int) -> list:
    # hysterIA, millenIA, medIA
    if index == len(info.vowel_clusters) - 1:
        if info.word_len - 1 == info.vowel_clusters[index].end_pos:
            return ["i:", "ɑ:"]
            
        # trIAl, lIAr
        elif info.word == "trial" or info.word == "liar":
            return ["aɪ", "ə"]
            
    # dIAmeter, dIAmond, dIArrhea
    if index == 0 and (info.word.startswith("diam") or info.word.startswith("diar")):
        return ["aɪ"]
        
    # industrIAl, pedestrIAn, differentIAble, familIAr, specIAl
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    if trailing_pos < info.word_len and info.word[trailing_pos] in "lnbr":
        return ["i:" "ə"]

    # manIAc
    elif trailing_pos < info.word_len and info.word[trailing_pos] == "c":
        return ["i:" "æ"]
    
    # differentIAte, initIAting
    return ["i:", "eɪ"]
    
def determine_io(info: WordInfo, index: int) -> list:
    # IOnic
    if info.vowel_clusters[index].start_pos == 0:
        return ["aɪ", "ɒ"]

    # radIO, patIO
    if info.vowel_clusters[index].end_pos == info.word_len - 1:
        return ["i:", "əʊ"]
        
    pushing_pos = info.vowel_clusters[index].start_pos - 1    
    if pushing_pos >= 0:
        # bIOme, vIOlence
        if info.word[pushing_pos] in "bvc":
            return ["aɪ", "əʊ"]
        # rIOt, lIOn
        elif info.word[pushing_pos] in "lr":
            return ["aɪ", "ə"]
    
    trailing_pos = info.vowel_clusters[index].end_pos + 1

    # senIOr, warrIOr
    if trailing_pos < info.word_len:
        if info.word[trailing_pos] == "r":
            return ["ɜ:"]
    
    # situatIOn, inflatIOn
    return ["ə"]
    
def determine_ee(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1

    # bEEr, pEEr
    if trailing_pos < info.word_len and info.word[trailing_pos] == "r":
        return ["ɪə"]

    # sEEk, frEE, EEl
    return ["i:"]
    
def determine_eu(info: WordInfo, index: int) -> list:
    # rEUsed
    pushing_pos = info.vowel_clusters[index].start_pos - 1    
    if pushing_pos >= 0:
        return ["i:", "u:"]

    # nEUtral, EUrope
    return ["u:"]
    
def determine_ea(info: WordInfo, index: int) -> list:
    # Determine consonants around vowels
    syllable = ""
    start_pos = info.vowel_clusters[index].start_pos
    end_pos = info.vowel_clusters[index].end_pos
    for char_index in range(max(0, start_pos - 2), min(info.word_len, end_pos + 3)):
        if char_index == start_pos or char_index >= end_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]

    # swEAring, hEAding, mEAdow, mEAsure, brEAd, brEAth, dEAth, thrEAtening, thrEAd, fEAther, wEALthy, brEAst, lEAther, plEAsure
    if "wear" in syllable or "head" in syllable or "mea" in syllable or "bread" in syllable or \
        "breast" in syllable or "eath" in syllable or "ealth" in syllable or "hrea" in syllable or "pleas" in syllable:
        return ["e"]
    
    if "ear" in syllable:
        # EArn, lEArn, EArth, hEArd, rehEArsal, sEArching
        if "earn" in syllable or "earth" in syllable or "eard" in syllable or "ears" in syllable or "earch" in syllable:
            return ["ɜ:"]
        # dishEArtening
        elif "heart" in syllable:
            return ["ɑ:"]
        else:
            # fEAr, nEAr, hEAring, EAr, disappEAr
            return ["ɪə"]
    
    # rEAson, sEAson, flEAs, fEAst, EAstern, bEAst, brEAch, EAch, lEAgue, cEAseless, sEAsick
    if "eas" in syllable or "eag" in syllable or "each" in syllable:
        return ["i:"]

    # brEAk, stEAk
    if "eak" in syllable:
        if "break" in syllable or "steak" in syllable:
            return ["eɪ"]
            
        # spEAker, tEAk, wEAkling    
        else:
            return ["i:"]

    # ocEAn, subterranEAn, vengEAnce, caesarean
    if "ean" in syllable and ( "cean" in syllable or "gean" in syllable or "nean" in syllable or "rean" in syllable ):
       return ["i:", "ə"]
       
    # changEAble
    if "eab" in syllable:
        return ["ə"]
    
    if "reat" in syllable:
        # crEAtion
        if "creat" in syllable:
            return ["i:", "eɪ"]
        # grEAtness
        return ["eɪ"]    
        
    if syllable.startswith("reac") or ( syllable.startswith("real") and (info.word != "real" and not syllable.startswith("reall"))):
        # rEAction
        if "react" in syllable:
            return ["i:", "æ"]
    
        # rEAlize, rEAcredit
        return ["i:", "ɑ:"]

    # thEAtrical
    if "theat" in syllable:    
        return ["i:" "æ"]

    # rEAl, rEAlly, rEAding, drEAming, stEAmed, bEAd, bEAn, dEAl, crEAm, chEAt, pEAce
    return ["i:"]
    
def determine_eo(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    if trailing_pos < info.word_len:
    
        # pidgEOn, stergEOn
        if info.word[trailing_pos] == "n":
            return ["ə"]
        # rEOrganize, thEOrist, rEOrient, metEOr  
        elif info.word[trailing_pos] == "r":
            return ["i:", "ɒ"]

    # nEOgenesis, sterEO, gEOde
    return ["i:", "əʊ"]
    
def determine_ei(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    starts_with_r = False
    if pushing_pos >= 0:
        # dYEIng    
        if info.word[pushing_pos] == "y":
            return ["aɪ", "ɪ"]
        # vEIl, vEIn
        elif info.word[pushing_pos] == "v":
            return ["eɪ"]
            
        starts_with_r = info.word[pushing_pos] == "r"
    
    if trailing_pos < info.word_len:
        # aparthEId, fEIst
        if info.word[trailing_pos] in "sd":
            return ["aɪ"]
        
        # EIther, sEIze, recEIve        
        if info.word[trailing_pos] in "tzv":
            return ["i:"]
            
        if info.word[trailing_pos] == "g":
            # fEIgn, EIght, rEIgn
            if traling_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "hn":
                return ["eɪ"]                
            
            # EIgenvector
            return ["aɪ"]
    
    # thEIrs
    if len(info.vowel_clusters[index]) == 1 and info.word.startswith("their"):
        return ["e"]
    
    # rEInvigorate, rEInforce
    if starts_with_r:
        return ["i:", "ɪ"]
    return ["i:"]

def determine_y(info: WordInfo, index: int) -> list:
    if index == info.word_len - 1:
        pushing_pos = info.vowel_clusters[index].start_pos - 1
    
        # whY, mY, crY, justifY
        if len(info.vowel_clusters) == 1 or ( pushing_pos >= 0 and info.word[pushing_pos] == "f" ):
            return ["aɪ"]
        # eternitY, icY, anY
        else:
            return ["i:"]
            
    # everYwhere, everYthing, everYbody, anYthing, anYwhere, anYbody
    if ( index == 2 and info.word.startswith("every") ) or \
        ( index == 1 and info.word.startswith("any") ):
        return ["i:"]
    
    syllable = ""
    start_pos = info.vowel_clusters[index].start_pos
    end_pos = info.vowel_clusters[index].end_pos
    for char_index in range(max(0, start_pos - 1), min(info.word_len, end_pos + 2)):
        if char_index == start_pos or char_index == end_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]
    
    # sYnthesize, sYllable, sYnchronous, sYndrome, sYmmetry
    if "sy" in syllable and "psy" not in syllable:
        return ["ɪ"]

    # crYpt, apocalYpse, crYstal, analYsis, analYtical
    if "ypt" in syllable or "yps" in syllable or "ypt" in syllable or "lys" in syllable or "lyt" in syllable:
        return ["ɪ"]
        
    # hYper, psYcho, pYro, thYroid, cYcle, dYnamic
    return ["aɪ"]
    
def determine_u(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    if trailing_pos < info.word_len:
        # pictUre, figUrine, structUre,
        if info.word[trailing_pos] == "r":
            return ["ɜ:"]
        
        if pushing_pos >= 0 and info.word[pushing_pos] == "p" and \
            info.word[trailing_pos] == "t":
            # repUtation, compUter
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in ["aei"]:
                return ["u:"]
            # pUt
            else:
                return ["ʊ"]
        
        # blUnt, Utterly, Udder, blUnder, Ultra, sUbmarine
        if trailing_pos + 1 < info.word_len and \
            info.word[trailing_pos] not in ["aeiuoy"] and \
            info.word[trailing_pos + 1] not in ["aeiuoy"]:
            return ["ʌ"]    
    
    # mUd, virUs, rUt, gUt
    if index == len(info.vowel_clusters) - 1:
        return ["ʌ"]
    
    # brUte, flUte, particUlar, commUnication, sUper, contribUtion, institUtion
    return ["u:"]
    
def determine_o(info: WordInfo, index: int) -> list:
    # Other, mOther, mOth, Old, cOld, cOntemporary, cOmpatible, Optics, cOnsOlidate
    # pOpulation, dOcumentation, apprOximate, respOnsible, mOdification, prOper, lOgic
    # recOgnition, pOssibility, nOne, One, prObable, becOming, becOme, sOme, tOld, gOlf
    # sOng, sOft, Once, gOne, shOt, mOnth, Of, Or, Observe, pOssession
    
    # wOrk, processOr, authOr, directOr, majOr, wOrld
    
    # imprOve, twO, intO, mOve, tOday
    
    # fOrward, Organic, infOrm, accOrdingly, impOrtant, Ordinary, enOrmous, priOrity, platfOrm, mOrtgage

    # phOtO, pOst, Over, micrO, prOfessional, satisfactOry, assOciation, rOse, hOle, zOne
    # vOte, cOde, bOth, hOme, mOre, rOle, nOting, alOne, tOtal, clOse, sO, gO, nO, Only, mOstly
    # brOken, clOsed, tOme, intrO

    return []

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
    "ae": determine_ae, 
    "ai": determine_ai,    
    "ao": determine_ao,
    "ie": determine_ie,
    "iu": determine_iu,
    "ia": determine_ia,
    "io": determine_io,
    "ee": determine_ee,
    "eu": determine_eu,
    "ea": determine_ea,
    "eo": determine_eo,
    "ei": determine_ei,
    # Single letter
    "y": determine_y,   
    #"o":
    "u": determine_u,
    #"a":
    #"i":    
    #"e":    
}

unambiguous_syllables = {
    "eau": ["u:"],
    "aa": ["ɑ:"],
    "au": ["ɔ:"],
    "ay": ["eɪ"],
    "ayi": ["eɪ", "ɪ"],    
    "ayo": ["eɪ", "əʊ"],
    "aeo": ["i:", "ɔ:"],
    "aw": ["ɔ:"],
    "awi": ["ɔ:", "ɪ"],
    "ew": ["u:"],
    "ewi": ["u:", "ɪ"],
    "iew": ["u:"],
    "iewi": ["u:", "ɪ"],    
    "uy": ["aɪ"],
    "uyi": ["aɪ", "ɪ"],
    "eou": ["ə"],
    "eea": ["i:", "ə"],    
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
    "yi": ["aɪ", "ɪ"],
    "yei": ["aɪ", "ɪ"],
    "oyi": ["ɔɪ", "ɪ"],
    "uie": ["aɪ", "ə"],
    "uia": ["i:", "ə"],
    "uiu": ["i:", "ə"],    
    "ioa": ["i:", "əʊ", "e"],
    "ioe": ["aɪ", "əʊ", "e"],
    "iou": ["i:", "ə"],
    "ooi": ["u:", "ɪ"],
    "oei": ["əʊ", "ɪ"],
}

for item in unambiguous_syllables.items():
    syllable = item[1]
    english_vowel_cluster_determine_map[item[0]] = lambda _, _2, syllable=syllable: syllable
