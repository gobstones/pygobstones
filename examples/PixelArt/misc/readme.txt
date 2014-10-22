generator.py es un script para generar programas Gobstones que dibujen una matriz de pixeles.

Uso:

generator.py fuente.pixels       # CSV de pixeles RGBA
generator.py fuente.pixels --hex # CSV de pixeles HEX
generator.py fuente.png --image  # Imagen


Requisitos:

Es necesario instalar el paquete "Pillow".

- pip install Pillow

###########################
## FORMATOS en Texto Plano
###########################

El script acepta dos formatos distintos en texto plano:

## CSV de Pixeles RGBA:

Ejemplo de grilla blanco-negro de 2x2.

0,0,0,255|255,255,255,0
255,255,255,0|0,0,0,255


## CSV de Pixeles Hexadecimales

Ejemplo de grilla blanco-negro de 2x2.

000000FF|FFFFFF00
FFFFFF00|000000FF