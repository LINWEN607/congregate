import csv
from congregate.cli.stage_base import BaseStageClass

class WaveStageCSVGeneratorCLI(BaseStageClass):
    def __init__(self):        
        self.rows = []
        super().__init__()
        self.project_json = self.open_projects_file()

    def __get_nested_value(self, dictionary, path_string, default=None):
        keys = path_string.split('.')
        current = dictionary
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def generate(self, 
                 destination_file="data/generated_wave_file.csv",
                 header_info=None,
                 dry_run=True):
        
        self.log.info(f"Generating wave file with header information: {header_info}")

        if header_info and header_info.get("headers"):
            headers = header_info.get("headers")
        else:
            headers = self.config.wave_spreadsheet_columns
        if header_info and header_info.get("header_map"):
            header_map = header_info.get("header_map")
        else:
            header_map = self.config.wave_spreadsheet_column_to_project_property_mapping

        # Pre-check that headers and map actually make sense against project structure
        # rather than waiting to find an error deep in
        project = self.project_json[0]

        for header in headers:           
            # Get the map values based on the header
            # Yes, this works. str the result, strip it.
            project_property_name = header_map.get(header)
            if project_property_name and str(project_property_name).strip() != "":
                # Now, see if we have the actual property in the project entity
                if not self.__get_nested_value(project, project_property_name):
                    self.log.error(
                        f"Property {project_property_name} does not exist on projects. Header map is {header_map}")
                    return
            # If a header didn't have a map, it just ignores

        headers_done = False
        with open(destination_file, "w") as df:
            csv_writer = csv.writer(df)
            if not headers_done:
                self.log.info(
                    f"CSV Writer appending headers to file {destination_file}: {headers}")
                self.rows.append(headers)
                if not dry_run:
                    csv_writer.writerow(headers)

                headers_done = True            

            # Extract the relevant data from the 
            for project in self.project_json:
                row = []                
                # over the headers                
                for header in headers:
                    # Do the custom processing up front for source and destination parent path

                    # Get the map values based on the header
                    # Yes, this works. str the result, strip it.
                    project_property_name = header_map.get(header)
                    if project_property_name and str(project_property_name).strip() != "":                                                                                    
                        # Now, see if we have the actual property in the project entity
                        project_property_value = str(self.__get_nested_value(project, project_property_name)).strip()                        
                        row.append(project_property_value)
                    else:
                        # No map for that header. Dump empty string
                        row.append("")

                self.rows.append(row)

                self.log.info(
                    f"CSV Writer appending row to file {destination_file}: {row}")

                if not dry_run:
                    csv_writer.writerow(row)

