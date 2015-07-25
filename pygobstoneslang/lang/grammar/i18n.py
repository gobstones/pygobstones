class BNFLanguage:
    def __init__(self, dictionary):
        self.dictionary = dictionary    
    def translate(self, bnf_string):
        output_bnf = ""        
        
        for line in iter(bnf_string.splitlines()):
            line = line + "\n"
            if not line.startswith("#"):
                parts = line.split("@")
                for key in self.dictionary:
                    parts[0] = parts[0].replace(" "+key+" ", " "+self.dictionary[key]+" ")
                    parts[0] = parts[0].replace(" "+key+"\n", " "+self.dictionary[key]+"\n")
                output_bnf += "@".join(parts) + "\n"
            else:
                output_bnf += line
        return output_bnf
    
ES = {
  'interactive': 'interactivo',
  'program': 'programa',
  
  'procedure': 'procedimiento',
  'function': 'funcion',
  'return': 'retornar',
  'not': 'no',
  
  'repeat': 'repetir',
  'repeatWith': 'repetirCon',
  'in': 'en',
  
  'if': 'si',
  'else': 'sino',
  'while': 'mientras',
  'case': 'caso',
  'of': 'de',
  
  'from': 'desde',
  'import': 'importar',
  
  'Skip': 'Saltear',
}

EN = {}

translate = BNFLanguage(EN).translate