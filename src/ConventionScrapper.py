


import pdfplumber
import json
import uuid

class ConventionScrapper():
    
    _pdf = None
    _bad_keys = [
        "6- Salari\u00e9s non cadres et cadres int\u00e9gr\u00e9s",
        "4- LA REDUCTION DU TEMPS DE TRAVAIL",
        "SOUS FORME DE JOURS DE REPOS SUR L\u2019ANNEE"
    ]    
    _bad_key_words = [
        "On ne peut employer"
    ]

    def __init__(self):
        ...

    def parse_fonction_table(self,_output_json_path:str=None)->dict:
        with pdfplumber.open(ConventionScrapper._pdf) as pdf:
            # Go through each page
            last_headers = None
            data_table = {}
            for page in pdf.pages:
                # Get tables from the current page
                tables = page.extract_table()
                # Print the table data
                if tables is None:
                    continue
                parsed = self.parse_table(tables,last_headers)
                if len(parsed["headers"])>0:
                    last_headers = parsed["headers"]
                    headers_key = "_".join(last_headers)
                if headers_key not in data_table.keys():
                    data_table[headers_key] = []
                for entry in parsed["entries"]:
                    data_table[headers_key] .append(entry)
            f_table = self.parse_function_table(data_table)
            clean_table = self.conform_function_table(f_table)
            with open(output_json_path,"w") as file:
                file.write(json.dumps(clean_table))


    def check_key(self,_key:str)->bool:
            if _key == "":
                return False
            if _key in ConventionScrapper._bad_keys:
                return False
            for bkw in ConventionScrapper._bad_key_words:
                if bkw in _key:
                    return False
            return True

    def conform_function_table(self,_table:dict)->dict:
        clean_talbe = {}
        for key,value in _table.items():
            if self.check_key(key) == False:
                continue
            value["id"] = str(uuid.uuid4())[-8:]
            clean_talbe[key] = value
        return clean_talbe

    def is_header(self,_list:list):
        none_values_count = 0
        known_header_keywords = ["Fonction","FONCTION","Catégorie","CATÉGORIE","Définition","Evénements","Durée"]
        has_kw = False
        clean_keys = [value for value in _list if value is not None and value != ""]
        for key in clean_keys:
            for kw in known_header_keywords:
                if kw not in key and kw.upper() not in key:
                    continue
                return True
        return False


    def filter_key(self,_key):
        if 'AU 1ER MARS' in _key:
            return 'salaire_brut'
        if 'FONCTION' in _key or "Fonction" in _key:
            return "fonction"    
        if 'Catégorie' in _key or  "CATÉGORIE" in _key:
            return "category"   
        if 'Définition' in _key :
            return "definition"
        return _key

    def filter_headers(self,_list)->list:
        filtered = []
        for el in _list:
            if el is None:
                continue
            if el in filtered:
                continue
            if el == "":
                continue
            fem_split = el.split("(")
            if  len(fem_split)>1 :
                filtered.append( self.filter_key(fem_split[0]))
                filtered.append("version féminisée")
                continue
            key = self.filter_key(el)
            filtered.append(key)
        return filtered

    def parse_entry(self,_headers,_row): 
        entry = {}
        row = _row
        if len(_headers)!=len(_row):
            row = [value for value in row if value is not None]
        values = []
        for value in row:
            if value is None:
                values.append("")
                continue
            values.append(value)
        index = 0
        last_key = None
        for key in _headers:
            if index > len(values)-1:
                break
            if last_key == "version féminisée" and key =="Catégorie" and value is not None and len(value)>4:
                key = 'Définition de fonction'
            if last_key == "FONCTION" and key =="Catégorie" and value is not None and "€" in value :
                key = 'salaire brut'
            entry[key] = values[index]
            index+=1
            last_key = key
        if len(entry.keys())==0:
            return None
        return entry

    def validate_entry(self,_entry):
        count = 0
        for key,value in _entry.items():
            if value=="":
                count+=1
        return count < 3


    def parse_table(self,_table,_last_header=None)->dict:
        headers = _last_header or []
        entries = []
        for row in _table:
            if self.is_header(row):
                headers = self.filter_headers(row)
                continue
            entry = self.parse_entry(headers,row)
            if entry is None:
                continue        
            if self.validate_entry(entry)==False:
                continue
            
            entries.append(entry)    
        return {
            "headers":headers,
            "entries":entries
        }

    # Open the PDF file


    def parse_function_table(self,_data_table):
        table = {}
        for key,datas in _data_table.items():
            print(key)
            for data in datas:
                function_data = {}
                if "fonction" not in data.keys():
                    continue
                function_name = data["fonction"].replace("\n"," ")
                if function_name not in table.keys():
                    table[function_name] = {}
                for key,value in data.items():

                    if value == "":
                        continue

                    if "€" in value and len(value)>4:
                        key = "salaire_brut_mensuel"
                        value = self.parse_salary(value)
                    if key == "salaire_brut":
                        key = "salaire_brut_journalier"
                        value = self.parse_salary(value)
                    table[function_name][key] = value
                table[function_name]["fonction"] = function_name
        return table

    def parse_salary(self,_string):
        clean = _string.replace(",",".").replace("€","").replace(" ","")
        return float(clean)

