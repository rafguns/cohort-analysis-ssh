import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from collections import defaultdict

# Disciplines in VABB
socsci = ['Psychology', 'Educational sciences', 'Criminology', 'Economics & business',
          'Political sciences', 'Sociology', 'Social sciences general',
          'Social health sciences']
hum = ['Communication studies', 'Law', 'Philosophy', 'Theology', 'Linguistics',
       'Literature', 'History of arts', 'Archaeology', 'History',
       'Humanities general']


def only_pubs_from(df, disciplines):
    '''Filter out publications in df that are not in list of disciplines'''
    return df[df[disciplines].sum(axis=1) > 0]


def load_data(fname='data/data.csv'):
    mt = pd.read_csv('data/data.csv', encoding='utf-8')

    # Make lists of author IDs. If no author ID is available, use empty list
    mt['allauthorids'] = mt.authorids.str.split(';')
    mt['allauthorids'] = mt.allauthorids.apply(
        lambda d: d if isinstance(d, list) else []
    )

    return mt


def author_yearly_feature_counts(mt,
                                 feature,
                                 pubyear='pubyear',
                                 kind='rel'):
    '''Create tidy table of yearly counts per author for a specific feature

    The default is relative counts (percentages). Absolute counts are obtained by
    setting `kind='abs'`. This function adds the columns `n` (counts) and `cohort`
    (cohort the author belongs to). `aloi` is the author identifier.

    '''
    if kind not in ['rel', 'abs']:
        raise ValueError('kind should be either "rel" or "abs"')

    # Make 'wide' dataframe of publications, one column per author
    # based on https://stackoverflow.com/a/45901040/1534017
    tmp = mt[[pubyear, feature]].merge(
        pd.DataFrame((item for item in mt.allauthorids), index=mt.index),
        left_index=True, right_index=True, how='left')

    # Convert to 'long' format with columns:
    # aloi, pubyear, feature, count (n)
    # partially based on https://stackoverflow.com/questions/25973514/
    tmp = (
        tmp
        .set_index([pubyear, feature])
        .stack()
        .reset_index()
        .rename(columns={0: 'aloi'})
        .pivot_table(index=[pubyear, feature, 'aloi'],
                     fill_value=0, aggfunc='size')
        .unstack(level=1)
        .fillna(0)
    )
    if kind == 'rel':
        tmp = tmp.div(tmp.sum(axis=1), axis=0)
    tidy = tmp.reset_index().melt(id_vars=['aloi', pubyear],
                                  value_name='n')

    # Add column with author cohort
    author_cohorts = tidy.groupby('aloi')[pubyear].min()
    tidy_cohort = tidy.merge(author_cohorts.to_frame('cohort'),
                             left_on='aloi', right_index=True)

    return tidy_cohort


def format_year_range(start, end):
    '''Format a year range start-end (e.g., "2000-05")'''
    start, end = str(start), str(end)

    return f'{start}-{end[2:]}' if start[:2] == end[:2] else f'{start}-{end}'


def make_cohorts(first, last, cohort_length, fancy_names=True):
    '''Create dict with the cohort for each year between first and last

    Each cohort consists of `cohort_length` years. In case the length of the
    entire period cannot be exactly divided into cohorts of the given
    length, the last cohort is truncated.

    If `fancy_names` is True, cohorts have names like '2001-05'. Otherwise,
    they are just integers 1, 2, 3...

    '''
    if cohort_length < 1 or cohort_length > last - first:
        raise ValueError

    res = {}
    cohort = 1
    for i, year in enumerate(range(first, last + 1), start=1):
        res[year] = cohort
        if i % cohort_length == 0:
            cohort += 1

    if fancy_names:
        d = defaultdict(set)
        for yr, cohort in res.items():
            d[cohort].add(yr)
        res = {yr: format_year_range(min(d[cohort]), max(d[cohort]))
               for yr, cohort in res.items()}

    return res


def survivors(df, pubyear='Year'):
    '''Get dataframe retaining only survivors

    Survivors are authors that appear in each subsequent time period.
    `pubyear` is the name of the column in `df` containing publication
    year/time period.

    '''
    d = {}

    # Figure out number of authors per cohort and per time unit
    for c in df.cohort.unique():
        df_c = df[df.cohort == c]
        au_c = set(df_c.aloi)
        for y in df_c[pubyear].unique():
            df_cy = df_c[df_c[pubyear] == y]
            au_cy = set(df_cy.aloi)
            au_c &= au_cy
        d[c] = au_c
    
    return df[df.aloi.isin(set.union(*d.values()))].copy()


def chart_from_tidy_df(df, feature, pubyear='Year', kind='rel',
                       only_survivors=False, row=None, **kwargs):
    '''Build a cohort plot from a tidy dataframe

    Different values of `feature` will appear in different columns.
    Splitting out by some variable over multiple rows is also possible by
    supplying the column name of the variable in `row`.

    '''
    if only_survivors:
        df = survivors(df, pubyear)
    
    # Fix labels of axes
    ylabel = 'Mean percentage' if kind == 'rel' else 'Mean of n'
    df.rename(columns={'n': ylabel}, inplace=True)

    # Fix legend
    cohortnames = sorted(df.cohort.unique())
    df['cohort'].replace({years: f'{ch} ({years})' for ch, years in zip('ABCDEF', cohortnames)},
                         inplace=True)
    
    # To get the legend in the right order and make sure the order of panels
    # is consistent across plots
    df.sort_values(by=['cohort', feature], inplace=True)

    g = sns.relplot(data=df, x=pubyear, y=ylabel,
                    col=feature, row=row, kind='line',
                    style='cohort', hue='cohort',
                    markers=True, **kwargs)
    if kind == 'rel':
        plt.ylim((0, 1))

    return g


def overview_chart(mt, feature, pubyear='Year', kind='rel', **kwargs):
    '''Build single-row cohort plot from wide dataframe'''
    df = author_yearly_feature_counts(mt, feature, pubyear,
                                             kind=kind)
    return chart_from_tidy_df(df, feature, pubyear, kind, **kwargs)


def overview_chart_full(mt, feature, pubyear='Year', kind='rel', **kwargs):
    ''''Build multi-row cohort plot from wide dataframe

    This chart has 3 separate rows:
    - all disciplines together,
    - social sciences,
    - humanities.

    '''
    dfs = []
    
    for tmp_mt, label in [(mt, 'SSH'),
                          (only_pubs_from(mt, hum), 'Humanities'),
                          (only_pubs_from(mt, socsci), 'Soc. sciences')]:
        tmp_df = author_yearly_feature_counts(tmp_mt, feature, pubyear,
                                                     kind=kind)
        tmp_df['Discipline'] = label
        dfs.append(tmp_df)
        
    df = pd.concat(dfs, ignore_index=True)
    
    return chart_from_tidy_df(df, feature, pubyear, kind, row='Discipline', **kwargs)
