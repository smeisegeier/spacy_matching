"""
Uses the test dataset provided by Stefan Meisegeier with fake clin data
Functions are imported from utils and data is read in with pandas
"""
import sqlite3
import pandas as pd
from utils_old import preprocess_data, get_matches, select_matches

# get data from here:
# https://gitlab.opencode.de/robert-koch-institut/zentrum-fuer-krebsregisterdaten/cancerdata-generator/-/tree/main/assets?ref_type=heads
sqlite_con = sqlite3.connect("C:/Substanzen/fake_clin_data.db")
free_text_data = pd.read_sql_query(
    "SELECT distinct Bezeichnung FROM Substanz", sqlite_con
)
sqlite_con.close()

col_with_substances = free_text_data["Bezeichnung"]

URL_LINK = "https://gitlab.opencode.de/robert-koch-institut/zentrum-fuer-krebsregisterdaten/cancerdata-references/-/raw/main/data/v2/Klassifikationen/substanz.csv?ref_type=heads"
reference_list = pd.read_csv(URL_LINK, sep=";")
col_with_ref_substances = reference_list["substanz"]


def create_service_variable(
    col_with_free_text: pd.Series,
    col_with_refs: pd.Series,
    threshold_parameter: int = 85,
    pattern_to_split: str = r"[/,;+]|\bund\b|\boder\b",
) -> pd.DataFrame:
    """applies all the function defined in the utils.py file

    Args:
        col_with_free_text (pd.Series): The column with text which should be scanned for substances
        col_with_refs (pd.Series): The column with substances that we want to search for in the text
        threshold_parameter (int, optional): Defines the accuracy, higher value means more accuracy.
        Defaults to 85.
        pattern_to_split (str, optional): Defines when more than one match is allowed
        Defaults to r"[/,;+]|\bund\b|\boder\b".

    Raises:
        ValueError: checks whether all IDs from input can be found in the output
        ValueError: checks whether the number of rows is the same in in- and output

    Returns:
        pd.DataFrame: processed df with original input text,
        matched substances and the corresponding accuracy score
    """
    preprocessed_data = preprocess_data(col_with_free_text)

    matches_df = get_matches(
        preprocessed_data, col_with_refs, threshold_parameter=threshold_parameter
    )

    selected_matches_df = select_matches(matches_df, pattern_to_split=pattern_to_split)

    if not preprocessed_data["ID"].isin(selected_matches_df["ID"]).all():
        raise ValueError("Not all IDs from input are in output")

    if len(preprocessed_data) != len(selected_matches_df):
        raise ValueError("Length of input and output differs")

    out_df = preprocessed_data.merge(selected_matches_df, on="ID", how="left")

    return out_df


if __name__ == "__main__":
    substances_with_service_variable = create_service_variable(
        col_with_substances, col_with_ref_substances
    )
    substances_with_service_variable.to_csv("output.csv", sep=";", index=False)
    print("output saved as csv")
