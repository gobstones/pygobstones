import xml.etree.ElementTree as ET


class ParseXML():
    def getDictFromXML(self, clothing):
        tree = ET.parse(clothing)
        root = tree.getroot()

        iterator = root.iter()
        self.dict = {}

        for item in iterator:
            if item.tag == 'Blue':
                self.blue = item.text
            elif item.tag == 'Black':
                self.black = item.text
            elif item.tag == 'Red':
                self.red = item.text
            elif item.tag == 'Green':
                self.green = item.text
            elif item.tag == 'Image':
                self.image = item.text
                self.dict[(self.blue, self.black, self.red, self.green)] = self.image

        return self.dict





