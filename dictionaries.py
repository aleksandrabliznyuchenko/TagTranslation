pos_dict = {
    "ADJ": {
        "AJ0": "adjective",
        "AJC": "comparative adjective",
        "AJS": "superlative adjective",
    },
    "ADP": {
        "PRF": "preposition 'of'",
        "PRP": "preposition",
        "TO0": "infinitive marker 'to'",
    },
    "ADV": {
        "AV0": "adverb",
        "AVQ": "wh-adverb",
    },
    "AUX": {
        "VM0": "modal auxiliary verb",
    },
    "CCONJ": {
        "CJC": "coordinating conjunction",
    },
    "DET": {
        "AT0": "article",
        "DPS": "possessive determiner",
        "DT0": "general determiner",
        "DTQ": "wh-determiner",
        "EX0": "existential 'there'",
    },
    "INTJ": {
        "ITJ": "interjection",
    },
    "NOUN": {
        "NN0": "common noun",
        "NN1": "singular common noun",
        "NN2": "plural common noun",
    },
    "NUM": {
        "CRD": "cardinal number",
        "ORD": "ordinal numeral",
    },
    "PART": {
        "AVP": "adverb particle",
        "XX0": "negative particle",
    },
    "PRON": {
        "PNI": "indefinite pronoun",
        "PNP": "personal pronoun",
        "PNQ": "wh-pronoun",
        "PNX": "reflexive pronoun",
    },
    "PROPN": {
        "NP0": "proper noun",  # Mary, John. London, MIA
    },
    "PUNCT": {
        "PUL": "left bracket",
        "PUN": "general separating mark",
        "PUQ": "quotation mark",
        "PUR": "right bracket",
    },
    "SCONJ": {
        "CJS": "subordinating conjunction",
        "CJT": "subordinating conjunction 'that'",
    },
    "SYM": {
        "ZZ0": "alphabetical symbols",
    },
    "VERB": {
        "VBB": "present tense forms of the verb 'be', except for 'is'",
        "VBD": "was were",
        "VBG": "being",
        "VBI": "(to) be",
        "VBN": "been",
        "VBZ": "is",
        "VDB": "do",
        "VDD": "did",
        "VDG": "doing",
        "VDI": "(to) do",
        "VDN": "done",
        "VDZ": "does",
        "VHB": "have",
        "VHD": "had",
        "VHG": "having",
        "VHI": "have",
        "VHN": "had",
        "VHZ": "has",
        "VVB": "finite base form of lexical verbs",
        "VVD": "past tense form of lexical verbs",
        "VVG": "-ing form of lexical verbs",
        "VVI": "infinitive form of lexical verbs",
        "VVN": "past participle form of lexical verbs",
        "VVZ": "-s form of lexical verbs",
    },
    "X": {
        "UNC": "unclassified items",
        "POS": "possessive or genitive marker",
    }
}

irregular_verbs = {
    "abide": ["abode"],
    "arise": ["arose", "arisen"],
    "awake": ["awoke", "awoken"],
    "bear": ["bore", "borne", "born"],
    "beat": ["beat", "beaten"],
    "become": ["became", "become"],
    "beget": ["begat", "begot", "begotten"],
    "begin": ["began", "begun"],
    "bend": ["bent"],
    "bet": ["bet"],
    "bid": ["bid", "bade", "bidden"],
    "bite": ["bit", "bitten"],
    "bleed": ["bled"],
    "blow": ["blew", "blown"],
    "break": ["broke", "broken"],
    "bring": ["brought"],
    "broadcast": ["broadcast"],
    "build": ["built"],
    "burn": ["burnt", "burned"],
    "burst": ["burst"],
    "buy": ["bought"],
    "cast": ["cast"],
    "catch": ["caught"],
    "chide": ["chid", "chode", "chidden"],
    "choose": ["chose", "chosen"],
    "cling": ["clung"],
    "clothe": ["clad", "clothed"],
    "come": ["came", "come"],
    "cost": ["cost"],
    "creep": ["crept"],
    "cut": ["cut"],
    "deal": ["dealt"],
    "dig": ["dug"],
    "dive": ["dived", "dove"],
    "do": ["did", "done"],
    "draw": ["drew", "drawn"],
    "dream": ["dreamt", "dreamed"],
    "drink": ["drank", "drunk"],
    "drive": ["drove", "driven"],
    "dwell": ["dwelt", "dwelled"],
    "eat": ["ate", "eaten"],
    "fall": ["fell", "fallen"],
    "feed": ["fed"],
    "feel": ["felt"],
    "fight": ["fought"],
    "find": ["found"],
    "flee": ["fled"],
    "fling": ["flung"],
    "fly": ["flew", "flown"],
    "forbid": ["forbade", "forbidden"],
    "forecast": ["forecast"],
    "foresee": ["foresaw", "foreseen"],
    "forget": ["forgot", "forgotten"],
    "forgive": ["forgave", "forgiven"],
    "forsake": ["forsook", "forsaken"],
    "freeze": ["froze", "frozen"],
    "get": ["got", "gotten"],
    "give": ["gave", "given"],
    "go": ["went", "gone"],
    "grind": ["ground"],
    "grow": ["grew", "grown"],
    "hang": ["hung"],
    "hear": ["heard"],
    "hide": ["hid", "hidden"],
    "hit": ["hit"],
    "hold": ["held"],
    "hurt": ["hurt"],
    "keep": ["kept"],
    "kneel": ["knelled", "knelt"],
    "know": ["knew", "known"],
    "lay": ["laid"],
    "lead": ["led"],
    "lean": ["leaned", "leant"],
    "leap": ["leaped", "leapt"],
    "learn": ["learnt"],
    "leave": ["left"],
    "lend": ["lent"],
    "let": ["let"],
    "lie": ["lay", "lain"],
    "light": ["lighted", "lit"],
    "lose": ["lost"],
    "make": ["made"],
    "mean": ["meant"],
    "meet": ["met"],
    "mow": ["mowed", "mow", "mown"],
    "offset": ["offset"],
    "overcome": ["overcame", "overcome"],
    "partake": ["partook", "partaken"],
    "pay": ["paid"],
    "plead": ["pleaded", "pled"],
    "preset": ["preset"],
    "prove": ["proved", "proven"],
    "put": ["put"],
    "quit": ["quit"],
    "read": ["read"],
    "relay": ["relaid"],
    "rend": ["rend"],
    "rid": ["rid"],
    "ring": ["rang", "rung"],
    "rise": ["rose", "risen"],
    "run": ["ran", "run"],
    "saw": ["sawed", "saw", "sawn"],
    "say": ["said"],
    "see": ["saw", "seen"],
    "seek": ["sought"],
    "sell": ["sold"],
    "send": ["sent"],
    "set": ["set"],
    "shake": ["shook", "shaken"],
    "shed": ["shed"],
    "shine": ["shone"],
    "shoe": ["shod"],
    "shoot": ["shot"],
    "show": ["showed", "shown"],
    "shut": ["shut"],
    "sing": ["sang", "sung"],
    "sink": ["sank", "sunk", "sunken"],
    "sit": ["sat"],
    "slay": ["slew", "slain"],
    "sleep": ["slept"],
    "slide": ["slid"],
    "slit": ["slit"],
    "smell": ["smelt"],
    "sow": ["sowed", "sown"],
    "speak": ["spoke", "spoken"],
    "speed": ["sped"],
    "spell": ["spelt"],
    "spend": ["spent"],
    "spill": ["spilled", "spilt"],
    "spin": ["spun"],
    "spit": ["spit", "spat"],
    "split": ["split"],
    "spoil": ["spoilt"],
    "spread": ["spread"],
    "spring": ["sprang", "sprung"],
    "stand": ["stood"],
    "steal": ["stole", "stolen"],
    "stick": ["stuck"],
    "sting": ["stung"],
    "stink": ["stank", "stunk"],
    "strew": ["strewed", "strewn"],
    "strike": ["struck", "stricken"],
    "strive": ["strove", "striven"],
    "swear": ["swore", "sworn"],
    "sweat": ["sweat", "sweated"],
    "sweep": ["swept"],
    "swell": ["swelled", "sweated", "swollen"],
    "swim": ["swam", "swum"],
    "swing": ["swung"],
    "take": ["took", "taken"],
    "teach": ["taught"],
    "tear": ["tore", "torn"],
    "tell": ["told"],
    "think": ["thought"],
    "thrive": ["throve", "thrived", "thriven"],
    "throw": ["threw", "thrown"],
    "thrust": ["thrust"],
    "typeset": ["typeset"],
    "undergo": ["underwent", "undergone"],
    "understand": ["understood"],
    "wake": ["woke", "woken"],
    "wear": ["wore", "worn"],
    "weep": ["wept"],
    "wet": ["wet", "wetted"],
    "win": ["won"],
    "wind": ["wound"],
    "withdraw": ["withdrew", "withdrawn"],
    "wring": ["wrung"],
    "write": ["wrote", "written"],
}

# irregular_verbs = {
#     "abide": {
#         2: "abode",
#         3: "abode",
#     },
#     "arise": {
#         2: "arose",
#         3: "arisen",
#     },
#     "awake": {
#         2: "awoke",
#         3: "awoken",
#     },
#     "be": {
#         2: ["was", "were"],
#         3: "been",
#     },
#     "bear": {
#         2: "bore",
#         3: ["borne", "born"],
#     },
#     "beat": {
#         2: "beat",
#         3: "beaten",
#     },
#     "become": {
#         2: "became",
#         3: "become",
#     },
#     "beget": {
#         2: ["begat", "begot"],
#         3: "begotten",
#     },
#     "begin": {
#         2: "began",
#         3: "begun",
#     },
#     "bend": {
#         2: "bent",
#         3: "bent",
#     },
#     "bet": {
#         2: "bet",
#         3: "bet",
#     },
#     "bid": {
#         2: ["bid", "bade"],
#         3: ["bid", "bidden"],
#     },
#     "bite": {
#         2: "bit",
#         3: "bitten",
#     },
#     "bleed": {
#         2: "bled",
#         3: "bled",
#     },
#     "blow": {
#         2: "blew",
#         3: "blown",
#     },
#     "break": {
#         2: "broke",
#         3: "broken",
#     },
#     "bring": {
#         2: "brought",
#         3: "brought",
#     },
#     "broadcast": {
#         2: "broadcast",
#         3: "broadcast",
#     },
#     "build": {
#         2: "built",
#         3: "built",
#     },
#     "burn": {
#         2: ["burnt", "burned"],
#         3: ["burnt", "burned"],
#     },
#     "burst": {
#         2: "burst",
#         3: "burst",
#     },
#     "buy": {
#         2: "bought",
#         3: "bought",
#     },
#     "can": {
#         2: "could",
#         3: "could",
#     },
#     "cast": {
#         2: "cast",
#         3: "cast",
#     },
#     "catch": {
#         2: "caught",
#         3: "caught",
#     },
#     "chide": {
#         2: ["chid", "chode"],
#         3: ["chid", "chidden"],
#     },
#     "choose": {
#         2: "chose",
#         3: "chosen",
#     },
#     "cling": {
#         2: "clung",
#         3: "clung",
#     },
#     "clothe": {
#         2: ["clad", "clothed"],
#         3: ["clad", "clothed"],
#     },
#     "come": {
#         2: "came",
#         3: "come",
#     },
#     "cost": {
#         2: "cost",
#         3: "cost",
#     },
#     "creep": {
#         2: "crept",
#         3: "crept",
#     },
#     "cut": {
#         2: "cut",
#         3: "cut",
#     },
#     "deal": {
#         2: "dealt",
#         3: "dealt",
#     },
#     "dig": {
#         2: "dug",
#         3: "dug",
#     },
#     "dive": {
#         2: "dived",
#         3: ["dived", "dove"],
#     },
#     "do": {
#         2: "did",
#         3: "done",
#     },
#     "draw": {
#         2: "drew",
#         3: "drawn",
#     },
#     "dream": {
#         2: ["dreamt", "dreamed"],
#         3: ["dreamt", "dreamed"],
#     },
#     "drink": {
#         2: "drank",
#         3: "drunk",
#     },
#     "drive": {
#         2: "drove",
#         3: "driven",
#     },
#     "dwell": {
#         2: "dwelt",
#         3: ["dwelt", "dwelled"],
#     },
#     "eat": {
#         2: "ate",
#         3: "eaten",
#     },
#     "fall": {
#         2: "fell",
#         3: "fallen",
#     },
#     "feed": {
#         2: "fed",
#         3: "fed",
#     },
#     "feel": {
#         2: "felt",
#         3: "felt",
#     },
#     "fight": {
#         2: "fought",
#         3: "fought",
#     },
#     "find": {
#         2: "found",
#         3: "found",
#     },
#     "flee": {
#         2: "fled",
#         3: "fled",
#     },
#     "fling": {
#         2: "flung",
#         3: "flung",
#     },
#     "fly": {
#         2: "flew",
#         3: "flown",
#     },
#     "forbid": {
#         2: "forbade",
#         3: "forbidden",
#     },
#     "forecast": {
#         2: "forecast",
#         3: "forecast",
#     },
#     "foresee": {
#         2: "foresaw",
#         3: "foreseen",
#     },
#     "forget": {
#         2: "forgot",
#         3: ["forgot", "forgotten"],
#     },
#     "forgive": {
#         2: "forgave",
#         3: "forgiven",
#     },
#     "forsake": {
#         2: "forsook",
#         3: "forsaken",
#     },
#     "freeze": {
#         2: "froze",
#         3: "frozen",
#     },
#     "get": {
#         2: "got",
#         3: ["got", "gotten"],
#     },
#     "give": {
#         2: "gave",
#         3: "given",
#     },
#     "go": {
#         2: "went",
#         3: "gone",
#     },
#     "grind": {
#         2: "ground",
#         3: "ground",
#     },
#     "grow": {
#         2: "grew",
#         3: "grown",
#     },
#     "hang": {
#         2: "hung",
#         3: "hung",
#     },
#     "have": {
#         2: "had",
#         3: "had",
#     },
#     "hear": {
#         2: "heard",
#         3: "heard",
#     },
#     "hide": {
#         2: "hid",
#         3: "hidden",
#     },
#     "hit": {
#         2: "hit",
#         3: "hit",
#     },
#     "hold": {
#         2: "held",
#         3: "held",
#     },
#     "hurt": {
#         2: "hurt",
#         3: "hurt",
#     },
#     "keep": {
#         2: "kept",
#         3: "kept",
#     },
#     "kneel": {
#         2: ["knelled", "knelt"],
#         3: ["knelled", "knelt"],
#     },
#     "know": {
#         2: "knew",
#         3: "known",
#     },
#     "lay": {
#         2: "laid",
#         3: "laid",
#     },
#     "lead": {
#         2: "led",
#         3: "led",
#     },
#     "lean": {
#         2: ["leaned", "leant"],
#         3: ["leaned", "leant"],
#     },
#     "leap": {
#         2: ["leaped", "leapt"],
#         3: ["leaped", "leapt"],
#     },
#     "learn": {
#         2: "learnt",
#         3: "learnt",
#     },
#     "leave": {
#         2: "left",
#         3: "left",
#     },
#     "lend": {
#         2: "lent",
#         3: "lent",
#     },
#     "let": {
#         2: "let",
#         3: "let",
#     },
#     "lie": {
#         2: "lay",
#         3: "lain",
#     },
#     "light": {
#         2: ["lighted", "lit"],
#         3: ["lighted", "lit"],
#     },
#     "lose": {
#         2: "lost",
#         3: "lost",
#     },
#     "make": {
#         2: "made",
#         3: "made",
#     },
#     "mean": {
#         2: "meant",
#         3: "meant",
#     },
#     "meet": {
#         2: "met",
#         3: "met",
#     },
#     "mow": {
#         2: "mowed",
#         3: ["mow", "mown"],
#     },
#     "offset": {
#         2: "offset",
#         3: "offset",
#     },
#     "overcome": {
#         2: "overcame",
#         3: "overcome",
#     },
#     "partake": {
#         2: "partook",
#         3: "partaken",
#     },
#     "pay": {
#         2: "paid",
#         3: "paid",
#     },
#     "plead": {
#         2: ["pleaded", "pled"],
#         3: ["pleaded", "pled"],
#     },
#     "preset": {
#         2: "preset",
#         3: "preset",
#     },
#     "prove": {
#         2: "proved",
#         3: ["proved", "proven"],
#     },
#     "put": {
#         2: "put",
#         3: "put",
#     },
#     "quit": {
#         2: "quit",
#         3: "quit",
#     },
#     "read": {
#         2: "read",
#         3: "read",
#     },
#     "relay": {
#         2: "relaid",
#         3: "relaid",
#     },
#     "rend": {
#         2: "rend",
#         3: "rend",
#     },
#     "rid": {
#         2: "rid",
#         3: "rid",
#     },
#     "ring": {
#         2: "rang",
#         3: "rung",
#     },
#     "rise": {
#         2: "rose",
#         3: "risen",
#     },
#     "run": {
#         2: "ran",
#         3: "run",
#     },
#     "saw": {
#         2: ["sawed", "saw"],
#         3: ["sawed", "sawn"],
#     },
#     "say": {
#         2: "said",
#         3: "said",
#     },
#     "see": {
#         2: "saw",
#         3: "seen",
#     },
#     "seek": {
#         2: "sought",
#         3: "sought",
#     },
#     "sell": {
#         2: "sold",
#         3: "sold",
#     },
#     "send": {
#         2: "sent",
#         3: "sent",
#     },
#     "set": {
#         2: "set",
#         3: "set",
#     },
#     "shake": {
#         2: "shook",
#         3: "shaken",
#     },
#     "shed": {
#         2: "shed",
#         3: "shed",
#     },
#     "shine": {
#         2: "shone",
#         3: "shone",
#     },
#     "shoe": {
#         2: "shod",
#         3: "shod",
#     },
#     "shoot": {
#         2: "shot",
#         3: "shot",
#     },
#     "show": {
#         2: "showed",
#         3: "shown",
#     },
#     "shut": {
#         2: "shut",
#         3: "shut",
#     },
#     "sing": {
#         2: "sang",
#         3: "sung",
#     },
#     "sink": {
#         2: ["sank", "sunk"],
#         3: ["sunk", "sunken"],
#     },
#     "sit": {
#         2: "sat",
#         3: "sat",
#     },
#     "slay": {
#         2: "slew",
#         3: "slain",
#     },
#     "sleep": {
#         2: "slept",
#         3: "slept",
#     },
#     "slide": {
#         2: "slid",
#         3: "slid",
#     },
#     "slit": {
#         2: "slit",
#         3: "slit",
#     },
#     "smell": {
#         2: "smelt",
#         3: "smelt",
#     },
#     "sow": {
#         2: "sowed",
#         3: ["sowed", "sown"],
#     },
#     "speak": {
#         2: "spoke",
#         3: "spoken",
#     },
#     "speed": {
#         2: "sped",
#         3: "sped",
#     },
#     "spell": {
#         2: "spelt",
#         3: "spelt",
#     },
#     "spend": {
#         2: "spent",
#         3: "spent",
#     },
#     "spill": {
#         2: ["spilled", "spilt"],
#         3: ["spilled", "spilt"],
#     },
#     "spin": {
#         2: "spun",
#         3: "spun",
#     },
#     "spit": {
#         2: ["spit", "spat"],
#         3: ["spit", "spat"],
#     },
#     "split": {
#         2: "split",
#         3: "split",
#     },
#     "spoil": {
#         2: "spoilt",
#         3: "spoilt",
#     },
#     "spread": {
#         2: "spread",
#         3: "spread",
#     },
#     "spring": {
#         2: "sprang",
#         3: "sprung",
#     },
#     "stand": {
#         2: "stood",
#         3: "stood",
#     },
#     "steal": {
#         2: "stole",
#         3: "stolen",
#     },
#     "stick": {
#         2: "stuck",
#         3: "stuck",
#     },
#     "sting": {
#         2: "stung",
#         3: "stung",
#     },
#     "stink": {
#         2: "stank",
#         3: "stunk",
#     },
#     "strew": {
#         2: "strewed",
#         3: ["strewed", "strewn"],
#     },
#     "strike": {
#         2: "struck",
#         3: ["struck", "stricken"],
#     },
#     "strive": {
#         2: "strove",
#         3: "striven",
#     },
#     "swear": {
#         2: "swore",
#         3: "sworn",
#     },
#     "sweat": {
#         2: ["sweat", "sweated"],
#         3: ["sweat", "sweated"],
#     },
#     "sweep": {
#         2: "swept",
#         3: "swept",
#     },
#     "swell": {
#         2: ["swelled", "sweated"],
#         3: "swollen",
#     },
#     "swim": {
#         2: "swam",
#         3: "swum",
#     },
#     "swing": {
#         2: "swung",
#         3: "swung",
#     },
#     "take": {
#         2: "took",
#         3: "taken",
#     },
#     "teach": {
#         2: "taught",
#         3: "taught",
#     },
#     "tear": {
#         2: "tore",
#         3: "torn",
#     },
#     "tell": {
#         2: "told",
#         3: "told",
#     },
#     "think": {
#         2: "thought",
#         3: "thought",
#     },
#     "thrive": {
#         2: ["throve", "thrived"],
#         3: ["thriven", "thrived"],
#     },
#     "throw": {
#         2: "threw",
#         3: "thrown",
#     },
#     "thrust": {
#         2: "thrust",
#         3: "thrust",
#     },
#     "typeset": {
#         2: "typeset",
#         3: "typeset",
#     },
#     "undergo": {
#         2: "underwent",
#         3: "undergone",
#     },
#     "understand": {
#         2: "understood",
#         3: "understood",
#     },
#     "wake": {
#         2: "woke",
#         3: "woken",
#     },
#     "wear": {
#         2: "wore",
#         3: "worn",
#     },
#     "weep": {
#         2: "wept",
#         3: "wept",
#     },
#     "wet": {
#         2: ["wet", "wetted"],
#         3: ["wet", "wetted"],
#     },
#     "win": {
#         2: "won",
#         3: "won",
#     },
#     "wind": {
#         2: "wound",
#         3: "wound",
#     },
#     "withdraw": {
#         2: "withdrew",
#         3: "withdrawn",
#     },
#     "wring": {
#         2: "wrung",
#         3: "wrung",
#     },
#     "write": {
#         2: "wrote",
#         3: "written",
#     },
# }
