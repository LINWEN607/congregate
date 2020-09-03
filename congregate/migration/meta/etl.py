from pathlib import Path
import json
import pandas as pd
from congregate.helpers.base_class import BaseClass

class WaveSpreadsheetHandler(BaseClass):
    def __init__(self, file_path, columns_to_use=None):
        super(WaveSpreadsheetHandler, self).__init__()
        self.file_path = file_path
        self.columns_to_use = self.map_columns(columns_to_use)
        self.file_type = self.__determine_file_type()

    def __determine_file_type(self):
        excel_types = ['.xls', '.xlsx', '.xlsm', '.xlsb', '.odf', '.ods', '.odt']
        extension = Path(self.file_path).suffix
        if extension in excel_types:
            return "excel"
        elif extension == ".csv":
            return "csv"
        else:
            raise ValueError(f"{self.file_path} is an invalid file type for extraction and transformation")

    def read_file_as_dataframe(self, df_filter=None):
        if self.file_type == "excel":
            r = pd.read_excel(self.file_path)
        elif self.file_type == "csv":
            r = pd.read_csv(self.file_path)
        df = pd.DataFrame(r, columns=self.columns_to_use)
        if df_filter:
            return self.filter_data(df, df_filter[0], df_filter[1])
        return df

    def read_file_as_json(self, df_filter=None):
        return json.loads(self.read_file_as_dataframe(df_filter=df_filter).to_json(orient='records'))
    
    def filter_data(self, df, column, value):
        return df.loc[df[column] == value]

    def map_columns(self, columns_to_use):
        mapping = self.config.wave_spreadsheet_column_mapping
        if mapping:
            for k, v in mapping.items():
                ind = columns_to_use.index(v)
                columns_to_use[ind] = k
        return columns_to_use
        