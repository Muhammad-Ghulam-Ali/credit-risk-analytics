import numpy as np

# Outlier Detection
def outlier_detection(df, column_name):
    Q1 = df[column_name].quantile(0.25)
    Q3 = df[column_name].quantile(0.75)

    IQR = Q3 - Q1

    lower_bound = Q1 - IQR * 1.5
    upper_bound = Q3 + IQR * 1.5

    df[column_name + '_OUTLIER'] = np.where((df[column_name] > upper_bound) | (df[column_name] < lower_bound), 'Outlier', 'Normal')

    return df[column_name + '_OUTLIER'].value_counts(normalize=True).round(2)

# Skewness test
def skewness_test(df, column_name):
    skewness = float(df[column_name].skew().round(2))
    return skewness

# Kurtosis test
def kurtosis_test(df, column_name):
    kurtosis = df[column_name].kurtosis().round(2)
    return kurtosis