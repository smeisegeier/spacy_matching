"""
matching relies on fuzzymatcher from spaczz.matcher,
data wrangling uses pandas
Levenshtein distance to measure similarity between two words
"""
import re
import string
import spacy
from spaczz.matcher import FuzzyMatcher
import pandas as pd
import Levenshtein

def prepare_free_text(input_col: pd.Series) -> pd.DataFrame:
    """prepares data, i.e., correct column names and deals with NA and empty strings

    Args:
        input_col (PandasSeries): column with free text for substances
    """
    input_data = pd.DataFrame(
        {"ID": range(1, len(input_col) + 1), "Original": input_col}
    )
    input_data["Original"] = input_data["Original"].replace({pd.NA: "NA", "": "NA"})

    return input_data


def remove_short_words(text: string) -> string:
    """removes words with less than 3 characters

    Args:
        s (string): string from free text field

    Returns:
        string: input string without short words
    """
    words = [word for word in text.split() if len(word) >= 3]
    out = " ".join(words)
    return out


def remove_unwanted_words(text: string) -> string:
    """removes common words that we dont want for string matching

    Args:
        s string: string from free text field

    Returns:
        string: input string without unwanted words
    """
    unwanted_words_pattern = (
        r"wöchentlich|weekly|woche|allgemein|entsprechend|beendet|zyklus|version|"
        r"bis|mg|kg|m2|bezeichnet|entfällt|o.n.a.|o.n.a|i.v.|i.v"
    )
    text = re.sub(unwanted_words_pattern, "", text, flags=re.IGNORECASE)
    return text


def find_5FU(text: string) -> string:
    """5FU is a common abbreviation for Fluorouracil.
    The functions finds it and replaces it with the full name.

    Args:
        s (string): input string from free text field

    Returns:
        string: Same string or string with 5-FU replaced by full name
    """
    fluorouracil_pattern = (
        r"5 fu|5fu|5-fu|5_fu|Fluoruracil|flourouracil|5-fluoruuracil|"
        r"5-fluoro-uracil|5-fluoruuracil|5-fluoruracil|floururacil|"
        r"5-fluorounacil|flourouraci|5-fluourouracil"
    )
    text = re.sub(fluorouracil_pattern, "fluorouracil", text, flags=re.IGNORECASE)
    return text


def calciumfolinat_to_folin(text: string) -> string:
    """Often it is reported <Folinsaure (Calciumfolinat)>
       to prevent mismatches with calciumfolinat, it is translated
       to folinsaure
    Args:
        s (string): input string from free text field
    """
    calcium_pattern = r"\b(Calciumfolinat)\b"
    text = re.sub(calcium_pattern, "folinsäure", text, flags=re.IGNORECASE)
    return text


def find_gemcitabin(text: string) -> string:
    """To fix common typos for Gemcitabin

    Args:
        s (string): input string from free text field

    Returns:
        string: Same string or string with fixed typo
    """
    gemcitabin_pattern = r"Gemcibatin|Gemcibatine|Gemcibatine Mono|Gemcibatin Mono"
    text = re.sub(gemcitabin_pattern, "gemcitabin", text, flags=re.IGNORECASE)
    return text


def find_Paclitaxel_nab(text: string) -> string:
    """To fix Paclitaxel nab is named as nab-Paclitaxel

    Args:
        s (string): input string from free text field

    Returns:
        string: Same string or string with fixed typo
    """
    Paclitaxel_pattern = r"nab-Paclitaxel|nabPaclitaxel|\b(nab[\s\-]?Paclitaxel)\b"
    text = re.sub(Paclitaxel_pattern, "Paclitaxel nab", text, flags=re.IGNORECASE)
    return text


def remove_special_symbols(text: string) -> string:
    """removes common symbols that hinder matching

    Args:
        s (string): input string from free text field

    Returns:
        string: Same string without symbols
    """
    special_symbols_pattern = (
    r"[\u24C0-\u24FF"
    r"\u2100-\u214F"
    r"\u2200-\u22FF"
    r"\u2300-\u23FF"
    r"\u2600-\u26FF"
    r"\u2700-\u27BF"
    r"\u2B50\u2B06]"
    r"|m²"
    )

    return re.sub(special_symbols_pattern, "", text)


def remove_trailing_leading_characters(text: string) -> string:
    """removes the , and ; if occur at the beginning or end of string

    Args:
        text (string): input string from free text field

    Returns:
        string: Same string without leading and trailing , ;
    """
    remove_trailings = text.rstrip(",").rstrip(";")
    remove_leadings = remove_trailings.lstrip(",").lstrip(";")
    remove_brackets = remove_leadings.replace("(", "").replace(")", "")
    no_whitepace = remove_brackets.strip()

    return no_whitepace


def preprocess_data(col_with_free_text: pd.Series) -> pd.DataFrame:
    """Preprocesses the input text to make finding substances easier

    Args:
        col_with_free_text (pd.Series): input from free text field

    Returns:
        pd.DataFrame: dataframe with three columns,
        ID (row number 1 to n), Original, Preprocessed_text
    """
    df = prepare_free_text(col_with_free_text)
    remove_words_col = df["Original"].apply(remove_unwanted_words)
    find_FU_col = remove_words_col.apply(find_5FU)
    find_gemcitabin_col = find_FU_col.apply(find_gemcitabin)
    find_paclitaxel_col = find_gemcitabin_col.apply(find_Paclitaxel_nab)
    translate_calciumfolinat = find_paclitaxel_col.apply(calciumfolinat_to_folin)
    remove_short_words_col = translate_calciumfolinat.apply(remove_short_words)
    preprocessed_col = remove_short_words_col.apply(remove_special_symbols)
    df["Preprocessed_text"] = preprocessed_col.apply(remove_trailing_leading_characters)

    return df


def get_matches(
    substance_df: pd.DataFrame, ref_substance: pd.Series, threshold_parameter: int = 85
) -> pd.DataFrame:
    """get all matches found with FuzzyMatcher

    Args:
        substance_df (pd.DataFrame): dataframe with columns ID, Original,
        Preprocessed_text, i.e., the output from preprocess_data()
        ref_substance (pd.Series): substances that we want to find in the input text
        threshold_parameter (int, optional): How fuzzy can the match be?
        The higher the more accurate the matches. Defaults to 85.

    Returns:
        pd.DataFrame: returns all matches found,
        column match refers to the word in the text that was matched,
        matched_to is the correct (without typos) word,
        similarity gives the accuracy between match and matched_to
    """
    nlp = spacy.blank("en")
    matcher = FuzzyMatcher(nlp.vocab)
    matcher.add("Substance", [nlp(str(sub)) for sub in ref_substance])

    results = []
    for _, row in substance_df.iterrows():
        text = row["Preprocessed_text"]
        id_num = row["ID"]

        doc = nlp(str(text))
        matches = matcher(doc)

        match_found = False

        for _, start, end, ratio, pattern in matches:
            if ratio > threshold_parameter:
                results.append(
                    {
                        "ID": id_num,
                        "input": text,
                        "match": doc[start:end].text,
                        "matched_to": pattern,
                        "similarity": ratio,
                    }
                )
                match_found = True

        if not match_found:
            results.append(
                {
                    "ID": id_num,
                    "input": text,
                    "match": "",
                    "matched_to": "",
                    "similarity": "",
                }
            )

    results_df = pd.DataFrame(results).sort_values(by="ID", ascending=True)

    return results_df


def select_best_rows(group: pd.DataFrame) -> pd.DataFrame:
    """will be applied to the df in select_matches()
    It defines the hierarchy for found matches:
    exact match > string detect match > smallest Levenshtein distance

    Args:
        group (pd.DataFrame): df to apply

    Returns:
        pd.DataFrame: df output
    """
    exact = group[group["exact_match"] == 1]
    if not exact.empty:
        return exact.iloc[0]

    detected = group[group["detected_match"] == 1]
    if not detected.empty:
        return detected.iloc[0]

    return group.loc[group["LV_distance"].idxmin()]


def select_matches(
    matches_found_df: pd.DataFrame,
    pattern_to_split: string = r"[/,;+]|\bund\b|\boder\b",
) -> pd.DataFrame:
    """selects matches and returns a df with one row per ID.
    Thus, the output can be joined on the input table
    Please refer to the README for more details about the selection process

    Args:
        matches_found_df (pd.DataFrame): The output of get_matches()
        pattern_to_split (string, optional): Defines when more than one match is allowed.
        Defaults to r"[/,;+]|\bund\b|\boder\b".

    Returns:
        pd.DataFrame: final output that is ready to be joined on the input data table
    """
    df_with_pattern = matches_found_df[
        ~matches_found_df["input"].str.contains(
            pattern_to_split, case=False, regex=True, na=False
        )
    ].copy()

    df_with_pattern["match_count"] = df_with_pattern.groupby("ID")["ID"].transform(
        "count"
    )
    select_df = df_with_pattern[df_with_pattern["match_count"] > 1].sort_values(
        by="ID", ascending=True
    )
    select_df["exact_match"] = (
        select_df["input"].astype(str) == select_df["matched_to"].astype(str)
    ).astype(int)

    select_df["detected_match"] = select_df.apply(
        lambda row: str(row["input"]).lower() in str(row["matched_to"]).lower(), axis=1
    ).astype(int)

    select_df["LV_distance"] = select_df.apply(
        lambda row: Levenshtein.distance(str(row["input"]), str(row["matched_to"])),
        axis=1,
    )
    best_matches = (
        select_df.groupby("ID")[select_df.columns.tolist()]
        .apply(select_best_rows, include_groups=True)
        .reset_index(drop=True)
    )
    selected_matches = best_matches[matches_found_df.columns.tolist()].copy()

    subset_df1 = matches_found_df[~matches_found_df["ID"].isin(selected_matches["ID"])]

    results_df = pd.concat([subset_df1, selected_matches], ignore_index=True)

    collapsed_df = (
        results_df.groupby("ID")
        .agg(
            {
                "input": "first",
                "match": lambda x: "; ".join(x.dropna().astype(str)),
                "matched_to": lambda x: "; ".join(
                    dict.fromkeys(x.dropna().astype(str))
                ),
                "similarity": lambda x: "; ".join(
                    dict.fromkeys(x.dropna().astype(str))
                ),
            }
        )
        .reset_index()
    )

    return collapsed_df.sort_values(by="ID", ascending=True)
