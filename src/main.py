"""
Uses the test dataset provided by Stefan Meisegeier with fake clin data
Functions are imported from utils and data is read in with pandas
"""

import sqlite3
import pandas as pd
from utils import preprocess_data, get_matches

# get data from here:
# https://gitlab.opencode.de/robert-koch-institut/zentrum-fuer-krebsregisterdaten/cancerdata-generator/-/tree/main/assets?ref_type=heads
sqlite_con = sqlite3.connect("./local/fake_clin_data.db")
free_text_data = pd.read_sql_query(
    "SELECT distinct Bezeichnung FROM Substanz", sqlite_con
)
sqlite_con.close()

col_with_substances_ZfKD_fake_data = free_text_data["Bezeichnung"]

URL_LINK = "https://gitlab.opencode.de/robert-koch-institut/zentrum-fuer-krebsregisterdaten/cancerdata-references/-/raw/main/data/v2/Klassifikationen/substanz.csv?ref_type=heads"
reference_list = pd.read_csv(URL_LINK, sep=";")
col_with_ref_substances_ZfKD = reference_list["substanz"]


def create_substance_service_var(
    col_with_substances: pd.Series,
    col_with_ref_substances: pd.Series,
    threshold: float = 0.85,
    max_per_match_id: int = 2,
    only_first_match: bool = False,
) -> pd.DataFrame:
    """
    This is the pipeline for creating the service variable
    for substances using ZfKD data.
    The functions are described in detail in utils.py.
    In short, the functions takes a pandasDataFrame column
    as an input and preprocesses its entries first.
    This results in a pandasDataFrame with the original
    input in one column and the preprocessed text in another one.
    The fuzzy matching relies on FuzzyMatcher from spaczz.
    It uses the preprocessed input and a reference list that
    the uses needs to provide. The reference list must be 
    a pandasDataFrame column (pd.Series) with substance names.
    The output is a pandasDataFrame with the original input,
    the preprocessed text and all possible matches with similary score.
    Use parameters to control output and sensitivity of the matcher. 
    """
    preprocessed_out = preprocess_data(col_with_substances)

    final_output = get_matches(
        preprocessed_out,
        col_with_ref_substances,
        threshold=threshold,
        max_per_match_id=max_per_match_id,
        only_first_match=only_first_match,
    )

    return final_output


results_atomic = create_substance_service_var(
    col_with_substances=col_with_substances_ZfKD_fake_data,
    col_with_ref_substances=col_with_ref_substances_ZfKD,
    only_first_match=True,
)

results_multiple_hits = create_substance_service_var(
    col_with_substances=col_with_substances_ZfKD_fake_data,
    col_with_ref_substances=col_with_ref_substances_ZfKD,
    only_first_match=False,
)

results_atomic.to_csv(".local/results_atomic.csv", index=False)
results_multiple_hits.to_csv(".local/results_multiple_hits.csv", index=False)
