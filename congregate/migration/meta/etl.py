from pathlib import Path
import json
import pandas as pd
from congregate.helpers.base_class import BaseClass
from congregate.helpers.misc_utils import safe_list_index_lookup

class WaveSpreadsheetHandler(BaseClass):
    def __init__(self, file_path, columns_to_use=None):
        super(WaveSpreadsheetHandler, self).__init__()
        self.file_path = file_path
        self.columns_to_use = self.map_columns(columns_to_use)
        self.file_type = self.__determine_file_type()

    def __determine_file_type(self):
        """
            Private method to determne if provided wave spreadsheet is a valid spreadsheet file format

            Supported file types: .xls, .xlsx, .xlsm, .xlsb, .odf, .ods, .odt, .csv
        """
        excel_types = ['.xls', '.xlsx', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']
        extension = Path(self.file_path).suffix
        if extension in excel_types:
            return "excel"
        elif extension == ".csv":
            return "csv"
        else:
            raise ValueError(f"{self.file_path} is an invalid file type for extraction and transformation")

    def read_file_as_dataframe(self, df_filter=None):
        """
            Reads wave spreadsheet data into memory as a Pandas DataFrame, Pandas primary data structure

            See here: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html for more information regarding DataFrames
        """
        if self.file_type == "excel":
            r = pd.read_excel(self.file_path)
        elif self.file_type == "csv":
            r = pd.read_csv(self.file_path)
        df = pd.DataFrame(r, columns=self.columns_to_use)
        if df_filter:
            return self.filter_data(df, df_filter[0], df_filter[1])
        return df

    def read_file_as_json(self, df_filter=None):
        """
            Reads wave spreadsheet data into memory and converts it to JSON where each object is a single column of data

            See here: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_json.html for more information regarding `to_json`
        """
        return json.loads(self.read_file_as_dataframe(df_filter=df_filter).to_json(orient='records'))
    
    def filter_data(self, df, column, value):
        """
            Return a filtered subset of a dataframe where the filter is a specific value in a specific column

            See here: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.filter.html for more information regarding filtering
        """
        return df.loc[df[column] == value]

    def map_columns(self, columns_to_use):
        """
            Returns a corrected list of columns to use based on the wave_spreadsheet_column_mapping
        """
        if (mapping := self.config.wave_spreadsheet_column_mapping) and columns_to_use:
            for k, v in mapping.items():
                if (ind := columns_to_use.index(v) if v in columns_to_use else None):
                    columns_to_use[ind] = k
        return columns_to_use
        