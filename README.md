# Creating a service variable for the free text field substances

## The problem

In cancer registries in Germany substances are reported in a free text field, e.g., "Interferon alpha-2a weekly i.v."
For analysis, it is helpful to have substances reported in a harmonized way. Also, reported substances may have typos.

## Suggested solution

The codes uses the FuzzyMatcher from spaczz and spacy to scan each free text for potential matches.

## Implementation

The data should be provided as a column of a pandasDataFrame with free text records in each row.
The substances that we want to find in the free text field should provided as a column of a pandasDataFrame as well.
First, the code finds all possible matches. The threshold parameter defines the accuracy. The lower the more matches but higher
values lead to more accurate matches. For the input "Interferon alpha-2a weekly i.v.", the FuzzyMatcher might return two substances
"Interferon alpha-2a" and "Interferon alpha-2b" (assuming they are both on the reference list). The code will select the best match,
defined as follows:
1. The matched substance is equal to the free text substance name, "Interferon alpha-2a" == "Interferon alpha-2a"
2. The matches substance can be string detected in the free text field, "Interferon alpha-2a." is in "Interferon alpha-2a"
3. We use the match with the smalles Levenshtein distance, "Interpheron alpha-2a" has a smaller distance to "Interferon alpha-2a" than to "Interferon alpha-2b"

Sometimes, it makes sense to select more than one match because a free text field may contain more than one substance,
e.g., "Interferon alpha-2a, 5-FU und Carboplatin". This is why there is the option to set a regex for splitting. By default we split
when there is:, ; + und oder. We dont split by default when there is a whitespace in the input string. In this example, the three substances will be collapsed into one row separated by semicolon "Interferon alpha-2a; 5-FU; Carboplatin". Accordingly, the output has the same number of rows as the input, making it possible to left join the found substances on the original input column.

## pylint testing
Score is > 9

## To do
The code runs with the sample dataset but an extensive test with a large dataset is still pending.

