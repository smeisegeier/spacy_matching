import pandas as pd
import re
import spacy
from spaczz.matcher import FuzzyMatcher

#helper functions

def prepare_free_text(input_col: pd.Series) -> pd.DataFrame:
    """Prepares data by renaming, stripping, and cleaning null or empty entries."""
    input_data = pd.DataFrame({
        "ID": range(1, len(input_col) + 1),
        "Original": input_col.fillna("NA").replace("", "NA")
    })
    input_data["Original"] = input_data["Original"].astype(str).str.strip()
    return input_data


def remove_short_words(text: str) -> str:
    return " ".join([word for word in text.split() if len(word) >= 3])


def find_5FU(text: str) -> str:
    pattern = (
        r"5 fu|5fu|5-fu|5_fu|Fluoruracil|flourouracil|5-fluoruuracil|"
        r"5-fluoro-uracil|5-fluoruuracil|5-fluoruracil|floururacil|"
        r"5-fluorounacil|flourouraci|5-fluourouracil"
    )
    return re.sub(pattern, "fluorouracil", text, flags=re.IGNORECASE)


def calciumfolinat_to_folin(text: str) -> str:
    return re.sub(r"\b(Calciumfolinat)\b", "folinsäure", text, flags=re.IGNORECASE)


def find_gemcitabin(text: str) -> str:
    return re.sub(r"Gemcibatin(?:e)?(?: Mono)?", "gemcitabin", text, flags=re.IGNORECASE)


def find_Paclitaxel_nab(text: str) -> str:
    return re.sub(r"\bnab[\s\-]?Paclitaxel\b", "Paclitaxel nab", text, flags=re.IGNORECASE)


#preprocessing using helper functions

def preprocess_data(col_with_free_text: pd.Series) -> pd.DataFrame:
    df = prepare_free_text(col_with_free_text)
    processed = (
        df["Original"]
        .apply(find_5FU)
        .apply(find_gemcitabin)
        .apply(find_Paclitaxel_nab)
        .apply(calciumfolinat_to_folin)
        .apply(remove_short_words)
        .str.strip()
    )
    df["Preprocessed_text"] = processed
    return df


#find matches with FuzzyMatcher from spaczz

def get_matches(preprocessed_data: pd.DataFrame, ref_substance: pd.Series,
                threshold:float = 0.85, max_per_match_id:int = 2,
                only_first_match:bool = False) -> pd.DataFrame:
   
    nlp = spacy.blank("en")
    matcher = FuzzyMatcher(nlp.vocab)

    for sub in ref_substance.dropna().astype(str):
        matcher.add(sub, [nlp(sub)])

    results = []

    for _, row in preprocessed_data.iterrows():
        text = row["Preprocessed_text"]
        original = row["Original"]
        doc = nlp(text)
        matches = matcher(doc)

        matches_filtered = [m for m in matches if m[3] >= threshold * 100]
        matches_sorted = sorted(matches_filtered, key=lambda x: x[3], reverse=True)

        result_row = {"Original": original}
        result_row["Preprocessed"] = text
        match_id_counts = {}
        match_idx = 1

        for match_id, start, end, ratio, _ in matches_sorted:
            count = match_id_counts.get(match_id, 0)
            if count >= max_per_match_id:
                continue

            result_row[f"Hit{match_idx}"] = match_id
            result_row[f"Mapped_to{match_idx}"] = doc[start:end].text
            result_row[f"Similarity{match_idx}"] = ratio

            match_id_counts[match_id] = count + 1
            match_idx += 1

        results.append(result_row)
    
    out = pd.DataFrame(results)

    if only_first_match:
        cols_to_keep = ["Original", "Preprocessed", "Hit1", "Mapped_to1", "Similarity1"]
        available_columns = [col for col in cols_to_keep if col in out.columns]
        dta_col_selected = out[available_columns]
        dta_col_selected.columns = [re.sub(r"\d+$", "", col) for col in dta_col_selected.columns]        
        return(dta_col_selected)
        
    return out

