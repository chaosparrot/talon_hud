from dataclasses import dataclass

@dataclass
class VowelCluster:
    vowels: str
    start_pos: int
    end_pos: int

@dataclass
class WordInfo:
    word: str
    word_len: int
    vowel_clusters: list