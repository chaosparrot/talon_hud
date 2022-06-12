from .speech_types import WordInfo

def determine_oo(info: WordInfo, index: int) -> list:
    r_pos = info.vowel_clusters[index].end_pos + 1
    c_pos = info.vowel_clusters[index].start_pos - 1
    # cOOrdinate
    if len(info.vowel_clusters) > 1 and c_pos >= 0 and info.word[c_pos] == "c":
        return ["əʊ", "ɒ"]
    # dOOr, flOOr
    elif r_pos < info.word_len and info.word[r_pos] == "r":
        return ["ɔː"]

    # bOOt
    else:
        return ["u:"]

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
        # herOIc, stOIc, herOIn
        elif trailing_pos < info.word_len and ( info.word[trailing_pos] in "c" or \
           ( index > 0 and info.word[trailing_pos] in "n" ) ):
           return ["əʊ", "ɪ"]
        # hemerOId, sterOIds
        elif trailing_pos < info.word_len and info.word[trailing_pos] == "d":
           return ["ɔɪ"]
           
    # OIl, cOIn
    return ["ɔɪ"]

def determine_ow(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1

    # OWn, OWning
    if index == 0 and info.word.startswith("own"):
        return ["əʊ"]
    
    # rOW, grOW, blOW, stOW, glOW, thrOW, lOW
    previous_two_letters = ""
    if pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] in "bshg":
        previous_two_letters += info.word[pushing_pos - 1]
    if pushing_pos >= 0:
        previous_two_letters += info.word[pushing_pos]

    if any(s for s in ["gr", "r", "st", "hr"] if s == previous_two_letters) or \
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
        if any(s for s in ["could", "should", "would"] if s == info.word):
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
    
    if pushing_pos >= 0 and info.word[pushing_pos] in "qg":
        # technique, leagUE
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
        trailing_pos = info.vowel_clusters[index].end_pos + 1        
    
        if info.word[pushing_pos] in "bqgc":
            # gUIde, gUIdance
            if trailing_pos < info.word_len and info.word[pushing_pos] == "g" and info.word[trailing_pos] == "d":
                return ["aɪ"]
                
            # liQUId, qUIck, qUIll, extingUIsh, gUIlt, circUIt, sqUIsh, bUIlding                
            return ["ɪ"]
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

    if pushing_pos >= 0 and trailing_pos < info.word_len:
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

    if pushing_pos >= 0 and trailing_pos < info.word_len:
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
        
    # cAEsar
    if pushing_pos >= 0 and info.word[pushing_pos] in "c":
        return ["i:"]

    if trailing_pos < info.word_len and info.word[trailing_pos] in "rs":
        # AEro, AEstetic
        return ["æ"]

    # prAEtor, florAE
    return ["eɪ"]
    
def determine_ai(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    if trailing_pos < info.word_len: 
        # AIr, fAIr, stAIrs, hAIr
        if info.word[trailing_pos] in "r":
            return ["eə"]
            
        # algebrAIc
        elif info.word[trailing_pos] in "c":
            return ["eɪ", "ɪ"]

    # plAIn, rAIn, AIlments
    return ["eɪ"]
    
def determine_aye(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    if trailing_pos < info.word_len: 
        # plAYEr, slAYEr    
        if info.word[trailing_pos] in "r":
            return ["eɪ", "ə"]

    # plAYEd, frAYEd
    return ["eɪ"]

def determine_eyi(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1        

    # EYIng
    if pushing_pos < 0: 
        return ["aɪ", "ɪ"]

    # survEYIng
    return ["eɪ", "ɪ"]

def determine_oye(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1        

    if trailing_pos < info.word_len: 
        # emplOYEr    
        if info.word[trailing_pos] in "r":
            return ["ɔɪ", "ə"]

    # emplOYEd
    return ["ɔɪ"]
    
def determine_ao(info: WordInfo, index: int) -> list:
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    # extrAOrdinary
    if pushing_pos >= 0 and info.word[pushing_pos] == "r":
        return ["ɑ:", "ɒ"]

    # chAOtic
    return ["eɪ", "ɒ"]
    
def determine_ie(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    if trailing_pos < info.word_len:         

        if info.word[trailing_pos] in "rt":
            # pIErce, fIErce
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "c":
                return ["ɪə"]

            # multiplIEr, sobrIEty 
            return ["aɪ", "ə"]

        # experIEnce, convinIEnt
        elif info.word[trailing_pos] == "n":
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] == "d":
                # frIEnd, frIEndship
                if pushing_pos >= 0 and info.word[pushing_pos] == "r":
                    return ["e"]
                # fIEnd
                else:
                    return ["i:"]
            return ["i:", "ə"]

        # serIEs, achIEve, chIEf, pIEce, fIEld, prIEst
        elif info.word[trailing_pos] in "svfcl":
            return ["i:"]
    
    if pushing_pos >= 0 and info.word[pushing_pos] == "v":
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
            
    # gIAnt, defIAnt, relIAnt
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    trailing_pos = info.vowel_clusters[index].end_pos + 1    
    if pushing_pos >= 0 and info.word[pushing_pos] in "fgl" and \
        trailing_pos < info.word_len and info.word[trailing_pos] == "n":
        return ["aɪ", "ə"]

    # dIAmond
    if index == 0 and info.word.startswith("dia"):
        if info.word.startswith("diamo"):
            return ["aɪ"]
        # dIAmeter
        elif info.word.startswith("diame"):            
            return ["aɪ", "æ"]
        # dIAry, dIAmeter, dIAgram
        else:
            return ["aɪ", "ə"]
    # industrIAl, pedestrIAn, differentIAble, familIAr, specIAl, alIAs
    if trailing_pos < info.word_len and info.word[trailing_pos] in "lnbrs":
        return ["i:", "ə"]

    # manIAc
    elif trailing_pos < info.word_len and info.word[trailing_pos] == "c":
        return ["i:", "æ"]
    
    # differentIAte, initIAting
    return ["i:", "eɪ"]
    
def determine_io(info: WordInfo, index: int) -> list:
    # IOnic
    if info.vowel_clusters[index].start_pos == 0:
        return ["aɪ", "ɒ"]
        
    # rIOt, lIOn
    pushing_pos = info.vowel_clusters[index].start_pos - 1    
    if index == 0 and info.word[pushing_pos] in "rl":
        return ["aɪ", "ə"]

    # radIO, patIO
    if info.vowel_clusters[index].end_pos == info.word_len - 1:
        return ["i:", "əʊ"]
        
    if pushing_pos >= 0:
        # bIOme, vIOlence
        if info.word[pushing_pos] in "bvc":
            return ["aɪ", "əʊ"]
    
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
        
    # TODO dEEScalate, rEEntry?

    # sEEk, frEE, EEl
    return ["i:"]
    
def determine_eu(info: WordInfo, index: int) -> list:
    # rEUsed
    pushing_pos = info.vowel_clusters[index].start_pos - 1    
    if pushing_pos >= 0 and info.word[pushing_pos] == "r":
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

    # idEA
    if end_pos == info.word_len - 1:
        return ["i:", "ə"]

    # swEAring, hEAding, mEAdow, mEAsure, brEAd, brEAth, dEAth, thrEAtening, thrEAd, fEAther, wEALthy, brEAst, lEAther, plEAsure
    if "wear" in syllable or "head" in syllable or "mea" in syllable or "bread" in syllable or \
        "breast" in syllable or "eath" in syllable or "ealth" in syllable or "hrea" in syllable or \
        ( "pleas" in syllable and not "please" in syllable ):
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
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    if trailing_pos < info.word_len:
        # pidgEOn, stergEOn
        if info.word[trailing_pos] == "n" and not (pushing_pos >= 0 and info.word[pushing_pos] == "n" ):
            return ["ə"]
        # rEOrganize, thEOrist, rEOrient, metEOr, nEOn
        elif info.word[trailing_pos] in "rn":
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
    
    # thEIrs
    if len(info.vowel_clusters) == 1 and info.word.startswith("their"):
        return ["e"]
    
    if trailing_pos < info.word_len:
        # aparthEId, fEIst
        if info.word[trailing_pos] in "sd":
            return ["aɪ"]
        
        # EIther, sEIze, recEIve        
        elif info.word[trailing_pos] in "tzv":
            return ["i:"]
            
        elif info.word[trailing_pos] == "g":
            # fEIgn, EIght, rEIgn
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "hn":
                return ["eɪ"]                
            
            # EIgenvector
            return ["aɪ"]

        # wEIrd, wEIrdly, wEIrdo
        elif info.word[trailing_pos] == "r" and trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] == "d":
            return ["ɪə"]
    
    # rEInvigorate, rEInforce
    if starts_with_r or ( pushing_pos >= 0 and info.word[pushing_pos] == "b" ):
        return ["i:", "ɪ"]
    return ["i:"]

def determine_y(info: WordInfo, index: int) -> list:
    if info.vowel_clusters[index].end_pos == info.word_len - 1:
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
    for char_index in range(max(0, start_pos - 2), min(info.word_len, end_pos + 2)):
        if char_index == start_pos or char_index == end_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]
    
    # sYnthesize, sYllable, sYnchronous, sYndrome, sYmmetry
    if "sy" in syllable and "psy" not in syllable:
        return ["ɪ"]

    # crYpt, apocalYpse, crYstal, analYsis, analYtical, phYsisian, phYsics
    if "ypt" in syllable or "yps" in syllable or "ypt" in syllable or "lys" in syllable or "lyt" in syllable or "phy" in syllable:
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
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "aei":
                return ["u:"]
            # pUt
            else:
                return ["ʊ"]
        
        # blUnt, Utterly, Udder, blUnder, Ultra, sUbmarine
        if trailing_pos + 1 < info.word_len and \
            info.word[trailing_pos] not in "aeiuoy" and \
            info.word[trailing_pos + 1] not in "aeiuoy":
            return ["ʌ"]    
    
    # mUd, virUs, rUt, gUt
    if index == len(info.vowel_clusters) - 1:
        return ["ʌ"]
    
    # brUte, flUte, particUlar, commUnication, sUper, contribUtion, institUtion, cUte
    return ["u:"]
    
def determine_o(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    
    if trailing_pos < info.word_len:
        if info.word[trailing_pos] == "r":
           # wOrk, processOr, authOr, directOr, majOr, wOrld, wOrse
            if trailing_pos + 1 > info.word_len or ( info.word != "or" and info.word[trailing_pos + 1] in "ks" ):
                return ["ɜ:"]
                
            # Or, fOrward, Organic, infOrm, accOrdingly, impOrtant, Ordinary, enOrmous, priOrity, platfOrm, mOrtgage
            else:
                return ["ɔ:"]
    
    syllable = ""
    start_pos = info.vowel_clusters[index].start_pos
    for char_index in range(max(0, start_pos - 2), min(info.word_len, trailing_pos + 2)):
        if char_index >= start_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]

    # autOmate
    if index > 0 and "to" in syllable and info.vowel_clusters[index - 1].vowels == "au":
        return ["əʊ"]

    # imprOve, twO, intO, mOve, tOday    
    if ( "to" in syllable and "oto" not in syllable and "e" not in syllable ) or "two" in syllable \
        or "mov" in syllable or "prove" in syllable:
        return ["u:"]
    
    # becOme, sOme, becOming, nOne, One, 
    if "some" in syllable or "com" in syllable or "ox" in syllable or \
        ( "one" in syllable and not "zone" in syllable and not "drone" in syllable and not "tone" in syllable ):
        return ["ɒ"]
    
    # phOtO, pOst, Over, micrO, prOfessional, satisfactOry, assOciation, rOse, hOle, zOne
    # vOte, cOde, bOth, hOme, mOre, rOle, nOting, alOne, tOtal, clOse, sO, gO, nO, Only, mOstly
    # brOken, clOsed, tOme, intrO, cOld, sOld, fOld, tOld
    if syllable.endswith("e") or syllable.endswith("o") or "old" in syllable or "ory" in syllable or \
        "cro" in syllable or ( "pro" in syllable and "prop" not in syllable ) or \
        "ost" in syllable or "i" in syllable:
        return ["əʊ"]

    # aerOplane
    if index + 1 < len(info.vowel_clusters):
        result = english_vowel_cluster_determine_map[info.vowel_clusters[index + 1].vowels](info, index + 1)
        if result[0].startswith("eɪ"):
           return ["əʊ"]

    # Other, mOther, mOth, cOntemporary, cOmpatible, Optics, cOnsOlidate
    # pOpulation, dOcumentation, apprOximate, respOnsible, mOdification, prOper, lOgic
    # recOgnition, pOssibility, prObable, gOlf, nOt
    # sOng, sOft, Once, gOne, shOt, mOnth, Observe, pOssession, Office
    return ["ɒ"]
    
def determine_a(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    start_pos = info.vowel_clusters[index].start_pos    
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    if trailing_pos < info.word_len:
        if info.word[trailing_pos] == "r":
            if info.word != "are" and trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "eri":
                # vArience, secondAries, primAries
                if trailing_pos + 2 < info.word_len and info.word[trailing_pos + 1] + info.word[trailing_pos + 2] == "ie":
                    return ["æ"]            
                # pArent, prepAre, Arrow, nArrow, embArrassment
                elif ( pushing_pos >= 0 and info.word[pushing_pos] == "p" ) or info.word[trailing_pos + 1] == "r":
                    return ["æ"]
                # wAres, stAre, flAre, declAre
                else:
                    return ["eə"]
            
            # contemporAry
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "y":
                return ["ə"]
                
            # pArticular, bArd, Art, chArcoal, Arches, smArt, gnArliest, nArwal
            # Armament, wArmer, wArning, Arbiter, phArmacy, Argue
            # Ardeous, bArd, lArd, stArt, mArt, gArment, Art, cArdio
            # mArket, cArnivorous, stArvation, tArget
            elif trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "gtdclwmnvk":
                return ["ɑ:"]
            # particulAr, simulArly, mArine, similArity, perticulAr, seculArism, grammAr
            elif index > 0 and info.word[pushing_pos] in "lm":
                return ["ə"]
            # caesAr, lunAr
            elif index == len(info.vowel_clusters) - 1 and info.word[pushing_pos] in "ns":
                return ["ə"]
            # chAracter, Arab, compArable
            elif index == 0 and ( info.word[trailing_pos + 1] in "a" or \
                ( pushing_pos >= 0 and info.word[pushing_pos] == "p" ) ):
                return ["æ"]
            # wAr, Are
            else:
                return ["ɑ:"]
        
        # neutrAl, retrievAl, approximAnt, elephAnt
        if index == len(info.vowel_clusters) - 1 and info.word.endswith("al") or info.word.endswith("als") or \
            info.word.endswith("ant") or info.word.endswith("ants"):
            return ["ə"]
        
        # cyAn
        if info.word.startswith("cya"):
            return ["aɪ", "ə"]
        
        if index == 0 and start_pos == 0 and trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] == info.word[trailing_pos]:
            # Apple, Application, App
            if len(info.vowel_clusters) == 1 or ( info.word.startswith("appl") and not info.word.startswith("apply") ):
                return ["æ"]
            # Applying, Affinity, Assessment, Assistence, Assumption, Assortment, Assault
            else:
                return ["ə"]
    # traumA, extrA
    else:
        return ["ɑ:"]

    syllable = ""
    for char_index in range(max(0, start_pos - 2), min(info.word_len, trailing_pos + 2)):
        if char_index >= start_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]
            
    # Agreed
    if "agr" in syllable:
        return ["ə"]

    # wAshing, wAs, wAtch, wAsp, wAnt, wAll
    if pushing_pos >= info.word_len and info.word[pushing_pos] in "w" or \
        syllable.startswith("wha"):
        return ["ɑ:"]
    
    # pAck, Anticompetitive, Action, fAct, And, Amplify, bAss, bAstard, lAss, disAster, fAscination, charActer
    # pAssion, mAsquerade, clAssifier, rAspberry, smAsh, glAss, cAscade, Ash, pAstel, fAshion, embarrAssment
    if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] not in "aeiouy" and \
        info.word[trailing_pos] + info.word[trailing_pos + 1] != "bl" and "cal" not in syllable:
        return ["æ"]
        
    next_syllable = None
    if index < len(info.vowel_clusters) - 1:
        next_syllable = english_vowel_cluster_determine_map[info.vowel_clusters[index + 1].vowels](info, index + 1)[0]

    # cAlm, fAll, infrAstructure
    if "fra" in syllable or ( "al" in syllable and ( "alm" in syllable or ( "all" in syllable and "cal" not in syllable ) ) ):
        return ["ɑ:"]
    
    # physicAlly, psychicAlly
    if "cal" in syllable and ( next_syllable == None or next_syllable == "i:" ):
        return [""]

    if next_syllable == "" or next_syllable == "ɜ:" or next_syllable == "i:" or next_syllable == "ə":
        # trainAble, flamAble, unbeatAbly
        if ( next_syllable == "ə" or next_syllable == "i:") and index > 0 and \
            ( "bl" in syllable and not "table" in syllable ):
            return ["ə"]
        
        # lowercAse, chAse, cascAde, lAser, hAste
        # bAthe, fAme, lAme, flAme, hAste, lAte, lAser, hAsten, wAver, Able, tAble
        # translAte, Ate, fAte, rAte, rAce, trAce, pAce, mAde, fAde, blAme, phAse, occAsion, wAste
        else:
            return ["eɪ"]

    # stAtistics, hAs, diagrAm, fAmiliar
    return ["æ"]
    
def determine_i(info: WordInfo, index: int) -> list:
    # happIness
    if index == info.word_len - 5 and info.word.endswith("ess"):
        return ["i:"]
    
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    pushing_pos = info.vowel_clusters[index].start_pos - 1
    
    # gIrl, swIrl, bIrd, gIrth
    if trailing_pos < info.word_len and info.word[trailing_pos] == "r":
        if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] not in "ie":
            return ["ɜ:"]
            
        # desIre, admIring, fIre
        else:
            return ["aɪ"]

    if pushing_pos > 0 and info.word[pushing_pos] == "y" and \
        trailing_pos < info.word_len and info.word[trailing_pos] == "n":
            if pushing_pos - 2 >= 0:
                previous_two_letters = info.word[pushing_pos - 2] + info.word[pushing_pos - 1]
                
                # bullyIng, emptyIng, varyIng, tidyIng, bodyIng
                if previous_two_letters[0] == previous_two_letters[1] or \
                    previous_two_letters == "pt" or previous_two_letters == "ar" or \
                    ( previous_two_letters[1] == "d" and previous_two_letters[0] in "aeiou" ):
                    return ["i:", "ɪ"]
                
            # dyIng, lyIng, flyIng, tryIng, petrifyIng
            return ["aɪ", "ɪ"]
    
    syllable = ""
    start_pos = info.vowel_clusters[index].start_pos
    for char_index in range(max(0, start_pos - 2), min(info.word_len, trailing_pos + 2)):
        if char_index >= start_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]

    next_vowel = "" if index + 1 >= len(info.vowel_clusters) else info.vowel_clusters[index + 1].vowels
    if next_vowel == "i":
        next_vowel_trailing = info.vowel_clusters[index + 1].end_pos + 1

        # realIzing, suffIcing
        if next_vowel_trailing + 1 < info.word_len and info.word[next_vowel_trailing] + info.word[next_vowel_trailing + 1] == "ng":
            return ["aɪ"]
        # realIstic, debIlitating            
        else:
            return ["ɪ"]
        
    # coincidEnce, incidEnt, confidEnce
    if index > 0 and next_vowel == "e":
        nv_trailing = info.vowel_clusters[index + 1].end_pos + 1
        if nv_trailing + 1 < info.word_len:
            next_syllable_end = info.word[nv_trailing] + info.word[nv_trailing + 1]
            if next_syllable_end == "nt" or next_syllable_end == "nc":
                return ["ɪ"]

    # sIde, wIfe, lIfe, strIfe, thrIve, Island, fIve, alIve,
    # Ideas, Ideology, lIne, fIne, hIgh, mIghty, realIzing, kInd, wInd, fInd, mInd
    # wIdely, prIce, prIcing, Ice, suffIce, realIse, Idea, Ideology    
    if "fiv" in syllable or "ind" in syllable or "igh" in syllable or "ign" in syllable or \
        ( ("ic" in syllable or "is" in syllable or "iz" in syllable ) and ( next_vowel == "e" or next_vowel == "i" ) ) or \
        ( ( next_vowel == "e" or next_vowel == "i" ) and ( "riv" in syllable or "iv" not in syllable ) ) or \
        syllable.startswith("ide"):
        return ["aɪ"]
    
    # evIl, stIll, fIll, IrredIscent, dIssident, lIve, gIve, lIving, Important, stInt
    # hIs, wIth, InterestIng, thIs, wIsh, natIve, tIt, satIsfied, rIch, mInImal
    # dIfference, InexpensIve, sensIbIlIty, consIderIng, If, passIve, possIble, strIng
    return ["ɪ"]
    
def determine_e(info: WordInfo, index: int) -> list:
    trailing_pos = info.vowel_clusters[index].end_pos + 1
    if trailing_pos < info.word_len:
        if info.word[trailing_pos] == "r":
            pushing_pos = info.vowel_clusters[index].start_pos - 1
            
            if pushing_pos >= 0 and info.word[pushing_pos] == "h" and \
                index < len(info.vowel_clusters) - 1:
                # thEre, whEre
                if pushing_pos - 1 >= 0 and info.word[pushing_pos - 1] in "wt":                
                    return ["e"]
                    
                # hEre
                elif index == 0 and info.word.startswith("here"):
                    return ["ɪə"]
        
            # Error , tError, tErrible, vEry
            if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "r" or \
                info.word == "very":
                return ["e"]
                
            # stErn, tErm, Ernest, cErtain, concErn, govErn, sErve, swErve, stErling, univErse
            elif trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] in "nmtvls":
                return ["ɜ:"]
            # staplEr, givEr, takEr, fakEr, evEry, chaptErs, ovEr, genEral, wintEr, hEr
            else:
                return ["ə"]

    syllable = ""
    start_pos = info.vowel_clusters[index].start_pos
    for char_index in range(max(0, start_pos - 2), min(info.word_len, trailing_pos + 2)):
        if char_index >= start_pos or ( char_index < start_pos and info.word[char_index] not in "aeiouy" ):
            syllable += info.word[char_index]    
    
    # English, prEtty
    if index == 0 and info.word.startswith("engl") or info.word.startswith("prett"):
        return ["ɪ"]
    
    # Single syllable
    if len(info.vowel_clusters) == 1:
        # thE, hE, shE, mE, wE, bE
        if info.word.endswith("e"):
            return ["i:"]
            
        # End, bEnd, yEt, frEt, gEt, wEll, frEnch, rEd, mEss
        # bEst, wEst, whEn, thEm, sElf
        else:
            return ["e"]
    
    # Last syllables
    if index == len(info.vowel_clusters) - 1:
    
        # availablE, tablE, stablE, belittlE, fickle
        if "ble" == syllable or "tle" == syllable or "kle" == syllable:
            return ["ə"]
            
        # determEnt, stainlEss, commEnt, featurelEssnEss
        elif "ness" in syllable or "less" in syllable or "ent" in syllable:
            return ["ə"]
            
        # elatEd, molassEs, drivEl, evEn, stevEn, tunnEl, teachEs, ledgEs
        # urgEs, chancEs, fencEs, biggEst, strongEst, studEnt, marshEs, boardEd
        elif "ded" in syllable or "ted" in syllable or "ses" in syllable or "ces" in syllable or \
            "ches" in syllable or "ges" in syllable or \
            ( "est" in syllable and "test" not in syllable ) or "hes" in syllable or "el" in syllable or "let" in syllable:
            return ["ə"]
            
        # livE, givE, nicE, twicE, minE, slopE, tropE, explorEs, ourselvEs, borEd
        # crashEd, themEs, positionEd, massagE, spacE, lifestylE
        # eliminatE, makEs, mistakEs, sensE, indifferencE, livEs, livEd
        elif info.word.endswith("ed") or info.word.endswith("es") or info.word.endswith("e"):
            return [""]
            
        # internEt
        else:
            return ["e"]
            
    # coincidEnce
    if "enc" in syllable and index < len(info.vowel_clusters) - 1 and info.vowel_clusters[index + 1].vowels == "e":
        return ["ə"]
       
    if index > 0 and index <= len(info.vowel_clusters) - 2:
        # enEmy, tragEdy, stratEgy
        if info.vowel_clusters[index + 1].vowels == "y":
            if info.word[trailing_pos] != "l":
                return ["ə"]
                
            # likEly
            else:
                return [""]
        # unneccEsary
        elif "ces" in syllable: 
            return ["ə"]
        else:
            # carEfull, carelEss, measurEment, retirEment, achievEments
            result = english_vowel_cluster_determine_map[info.vowel_clusters[index + 1].vowels](info, index + 1)
            if any(s for s in result[0] if s.startswith("ə") or s == ""):
                return [""]
                
            if result[0] == "eɪ" or result[0] == "u:" or result[0] == "i:":
                
                # stalEmate, grapEfruit
                if info.vowel_clusters[index - 1].vowels == "a":
                    return [""]
                # reintEgrate
                else:
                    return ["ə"]
    
    if trailing_pos + 1 < info.word_len and info.word[trailing_pos + 1] not in "aeoiuy":
        # lEdge, Edge, Entity, Enter, mEnding, assEss, Effort, lEtting, Employ
        # bEtter, rEckoning, assEssment, dEsert, dEsperate, rEscue
        if index == 0 and ( syllable.startswith("re") or syllable.startswith("pre") ) and not "sc" in syllable:
            return ["i:"]
        return ["e"]
    
    # TODO dEsert, dEsk, dEtermining, dEsperate, dEck, dEscribe, dEsolation, dEstruction, dEstablize, dEsign, dEspite
    # dEsire, dEsisting, dEstiny, dEspite, dEfeat
    
    # Erect, Electricity, Evil, prEpare, rEpair, Evening
    # maybE, bElittle, stratEgic
    if syllable.startswith("be") or syllable.startswith("pre") or syllable.startswith("re") or syllable.startswith("el"):        
        return ["i:"]
    
    if trailing_pos + 1 < info.word_len:
        # pEn, Epic, stEp, Extreme
        if info.word[trailing_pos] in "npx":
            return ["e"]
    
        if info.word[trailing_pos + 1] in "aeoiuy":
            result = english_vowel_cluster_determine_map[info.vowel_clusters[index + 1].vowels](info, index + 1)
            
            if result[0] == "ə" and trailing_pos + 2 < info.word_len and info.word[trailing_pos + 2] == "r":
                # Every, nEver, nEvertheless
                if info.word[trailing_pos] == "v":
                    return ["e"]
                else:
                    return ["i:"]            
            
            # extrEme, stratEgic, Evil
            elif any(s for s in result[0] if s == "ə" or s == "" or s == "ɪ"):
                return ["i:"]
                
            # mEdia
            elif len(result) > 1 and result[0] == "i:":
                return ["i:"]

    return ["e"]

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
    "eyi": determine_eyi,
    "aye": determine_aye,
    "oye": determine_oye,    
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
    "y": determine_y,   
    "o": determine_o,
    "u": determine_u,
    "a": determine_a,
    "i": determine_i,   
    "e": determine_e,
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
    "away": ["ə", "eɪ"],
    "awai": ["ə", "eɪ"],    
    "ew": ["u:"],
    "ewi": ["u:", "ɪ"],
    "iew": ["u:"],
    "ii": ["i:", "ɪ"],
    "iewi": ["u:", "ɪ"],    
    "uy": ["aɪ"],
    "uyi": ["aɪ", "ɪ"],
    "eou": ["ə"],
    "ey": ["i:"],
    "eye": ["aɪ"],
    "eyeo": ["aɪ", "əʊ"],
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
