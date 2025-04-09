import spacy
from spaczz.matcher import FuzzyMatcher
import pandas as pd
import Levenshtein

sub_data = pd.read_csv("C:/Python/Substanzen/Test_Daten.csv", sep = ";", encoding="utf-8")
ref_tab = pd.read_csv("C:/Python/Substanzen/substanz.csv", sep = ";", encoding="utf-8")

nlp = spacy.blank("en")

matcher = FuzzyMatcher(nlp.vocab)
matcher.add("Substance", [nlp(str(sub)) for sub in ref_tab["Substanz"]])

results = []
for _, row in sub_data.iterrows():
    text = row["Bezeichnung"]
    id_num = row["ID"]

    doc = nlp(str(text))
    matches = matcher(doc)

    for match_id, start, end, ratio, pattern in matches:
        if ratio > 80:
            results.append({
                "ID": id_num,
                "input": text,
                "match": doc[start:end].text,
                "matched_to": pattern,
                "similarity": ratio
            })

# Create results DataFrame
results_df = pd.DataFrame(results)

best_matches_df = results_df.loc[results_df.groupby(["input", "match"])["similarity"].idxmax()]

best_matches_df.to_csv("output.csv", sep=";")