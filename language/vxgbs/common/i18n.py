# coding:utf-8:
#
# Copyright (C) 2011, 2012 Pablo Barenbaum <foones@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from common.utils import hsv

#### Provides translations of all kinds of messages found in the source.

## Spanish
ES = {

# lexer errors
  'Malformed input - unrecognized symbol: "%s"':
    'Entrada mal formada - símbolo no reconocido: "%s"',
  'Malformed input - unrecognized symbol':
    'Entrada mal formada - símbolo no reconocido',
  'Found: %s\nMaybe should be: %s':
    'Se encontró: %s\nSeguramente debería ser: %s',

# smart lexer errors
  'Repeated symbol: %s':
    'Símbolo repetido: %s',
  '%s cannot be followed by %s':
    '%s no puede estar seguido por %s',
  'return is only valid inside functions or the Main procedure':
    'Sólo se admite return dentro de funciones o en el procedimiento Main.',
  'return must be followed by "("':
    'return tiene que estar seguido por "("\n' +
    'Por ejemplo: return (nroBolitas(Rojo))\n' +
    '             return (42, True)',
  'return from function "%s" must return something':
    'El return de la función "%s" tiene que devolver algo\n' +
    'Por ejemplo: return (nroBolitas(Rojo))\n' +
    '             return (42, True)',
  'Program entrypoint should only return variables':
    'El return del punto de entrada del programa sólo puede devolver variables',
  'procedure name should be an uppercase identifier':
    'El nombre de un procedimiento tiene que ser un identificador con mayúscula.\nPor ejemplo: LlenarTablero',
  'function name should be a lowercase identifier':
    'El nombre de una función tiene que ser un identificador con minúscula.\nPor ejemplo: colorCeldaVecina',
  'Unterminated string': 'Cadena sin terminar',
  'Found closing ")" with no matching open paren':
    'Se encontró un ")" pero no había un paréntesis abierto',
  'Found closing "}" with no matching open brace':
    'Se encontró una "}" pero no había una llave abierta',
  'Found open "(" with no matching closing paren':
    'Se encontró un paréntesis "(" pero nunca se cierra',
  'Found open "{" with no matching closing brace':
    'Se encontró una llave "{" pero nunca se cierra',
  'Maybe there is an extra "%s" at %s':
    'Quizás sobra un "%s" en %s',
  'Found end of file but there are open parens yet':
    'Se llegó al final del archivo pero todavía hay paréntesis abiertos',
  'Found end of file but there are open braces yet':
    'Se llegó al final del archivo pero todavía hay llaves abiertas',

# parser errors
  'Syntax error':
    'Error de sintaxis',
  'Found: %s':
    'Se encontró: %s',
  'Found: %s\nExpected: %s':
    'Se encontró: %s\nSe esperaba: %s',
  'Found: %s\nExpected one of the following tokens:':
    'Se encontró: %s\nSe esperaba alguna de las siguientes palabras:',
  'Procedure name "%s" is missing a "("':
    'Falta un "(" después del nombre del procedimiento "%s".',

  'Conflictive rule for: ("%s", "%s")\n':
    'Regla conflictiva para: ("%s", "%s")\n',
  'Will choose first production:\n':
    'Se elige la primera producción:\n',

# smart parser errors
  'Cannot call a function here':
    'No se puede invocar a una función en este punto del programa.',
  'Cannot call a procedure here':
    'No se puede invocar a un procedimiento en este punto del programa.',
  'Premature end of input':
     'Se llegó al final del archivo y había que seguir.\nRevisá si te faltó algo.',
  'Strings can only be used in a THROW_ERROR command':
    'Las cadenas sólo se pueden usar en un comando THROW_ERROR.\nPor ejemplo: THROW_ERROR("rompiste todo")',
  'THROW_ERROR can only accept a string':
    'El comando THROW_ERROR sólo acepta cadenas.\nPor ejemplo: THROW_ERROR("rompiste todo")',

# lint errors
  'Semantic error':
    'Error en el programa',
  'Empty program':
    'El programa está vacío.',
  'The Main procedure should be the last definition':
    'La definición del procedimiento Main debe ser la última del programa.',
  'There should be an entry point (Main procedure or program block).':
    'El programa debería tener un punto de entrada (procedimiento Main o bloque program).',
  # Records
    'Repeated assignment for field "%s".':
        'Asignación repetida para el campo "%s".',
    'the given value has type %s':
        'el valor dado es de tipo %s',
    'Error while building type %s':
        'Error al construir el tipo %s',
  # Variants
    'Variant body should only contain case declarations.':
        'El cuerpo de un tipo variante solo debe contener declaraciones \'case\'.',
  # cannot define
  'Cannot define type "%s"': 'No se puede definir el tipo "%s"',
  'Cannot define procedure "%s"': 'No se puede definir el procedimiento "%s"',
  'Cannot define function "%s"': 'No se puede definir la función "%s"',
  'Cannot define constant "%s"': 'No se puede definir la constante "%s"',
  'Cannot define variable "%s"': 'No se puede definir la variable "%s"',
  'Cannot define parameter "%s"': 'No se puede definir el parámetro "%s"',
  'Cannot define index "%s"': 'No se puede definir el índice "%s"',
  # already defined
  'type "%s" already defined %s': 'El tipo "%s" ya está definido %s',
  'procedure "%s" already defined %s': 'El procedimiento "%s" ya está definido %s',
  'function "%s" already defined %s': 'La función "%s" ya está definida %s',
  'constant "%s" already defined %s': 'La constante "%s" ya está definida %s',
  'variable "%s" already defined %s': 'La variable "%s" ya está definida %s',
  'parameter "%s" already defined %s': 'El parámetro "%s" ya está definido %s',
  'index "%s" already defined %s': 'El índice "%s" ya está definido %s',
  # is too similar
  '"%s" is too similar to type "%s", defined %s': '"%s" se parece al tipo "%s"\nya definido %s',
  '"%s" is too similar to procedure "%s", defined %s': '"%s" se parece al procedimiento "%s"\nya definido %s',
  '"%s" is too similar to function "%s", defined %s': '"%s" se parece a la función "%s"\nya definida %s',
  '"%s" is too similar to constant "%s", defined %s': '"%s" se parece a la constante "%s"\nya definida %s',
  '"%s" is too similar to variable "%s", defined %s': '"%s" se parece a la variable "%s"\nya definida %s',
  '"%s" is too similar to parameter "%s", defined %s': '"%s" se parece al parámetro "%s"\nya definido %s',
  '"%s" is too similar to index "%s", defined %s': '"%s" se parece al índice "%s"\nya definido %s',
  # is not a
  '"%s" is not a procedure': '"%s" no es un procedimiento',
  '"%s" is not a function': '"%s" no es una función',
  '"%s" is not a constant': '"%s" no es una constante',
  '"%s" is not a variable': '"%s" no es una variable',
  '"%s" is not a parameter': '"%s" no es un parámetro',
  '"%s" is a parameter': '"%s" es un parámetro',
  '"%s" is not a index': '"%s" no es un índice',
  '"%s" is an index': '"%s" es un índice',
  # defined at...
  'procedure "%s" defined %s': 'El procedimiento "%s" está definido %s',
  'function "%s" defined %s': 'La función "%s" está definida %s',
  'constant "%s" defined %s': 'La constante "%s" está definida %s',
  'variable "%s" defined %s': 'La variable "%s" está definida %s',
  'parameter "%s" defined %s': 'El parámetro "%s" está definido %s',
  'index "%s" defined %s': 'El índice "%s" está definido %s',
  # is not defined
  'type or callable "%s" is not defined': 'El tipo o rutina %s no está definido',
  'type "%s" is not defined': 'El tipo %s no está definido',
  'procedure "%s" is not defined': 'El procedimiento "%s" no está definido',
  'function "%s" is not defined': 'La función "%s" no está definida',
  'constant "%s" is not defined': 'La constante "%s" no está definida',
  'variable "%s" is not defined': 'La variable "%s" no está definida',
  'parameter "%s" is not defined': 'El parámetro "%s" no está definido',
  'index "%s" is not defined': 'El índice "%s" no está definido',
  #
  'as a built-in': 'por Gobstones',
  'at %s': 'en:\n%s',
  # repeated parameter
  'procedure "%s" has a repeated parameter: "%s"':
    'El procedimiento "%s" tiene un parámetro repetido: "%s"',
  'function "%s" has a repeated parameter: "%s"':
    'La función "%s" tiene un parámetro repetido: "%s"',
  # arity checks
 'Too many arguments for procedure "%s".\nExpected %i (%s), received %i':
   'Demasiados argumentos para el procedimiento "%s".\n' +
   'Esperaba %i argumentos (%s)\nRecibió %i',
 'Too few arguments for procedure "%s".\nExpected %i (%s), received %i':
   'Faltan argumentos para el procedimiento "%s".\n' +
   'Esperaba %i argumentos (%s)\nRecibió %i',
 'Too many arguments for function "%s".\nExpected %i (%s), received %i':
   'Demasiados argumentos para la función "%s".\n' +
   'Esperaba %i argumentos (%s)\nRecibió %i',
 'Too few arguments for function "%s".\nExpected %i (%s), received %i':
   'Faltan argumentos para la función "%s".\n' +
   'Esperaba %i argumentos (%s)\nRecibió %i',
  # return arity
 'Function "%s" returns one value':
   'La función "%s" devuelve un solo valor',
 'Function "%s" returns %i values':
   'La función "%s" devuelve %i valores',
 'One value is expected':
   'Se espera recibir un solo valor',
 '%i values are expected':
   'Se espera recibir %i valores',
  #
  'Repeated variable in assignment: "%s"':
    'La variable "%s" está repetida en la asignación',
  'Literals in a switch should be disjoint':
    'No puede haber literales repetidos en un case',
  'Constructors in a match should be disjoint':
    'No puede haber constructores repetidos en un match',
  '\'match\' expression can only be used with a Variant-type value.':
    'La expresión \'match\' solo puede ser utilizada con valores de tipo variante.',
  #
  'Index of a foreach/repeatWith/repeat cannot be a variable: "%s"':
    'El índice de un foreach/repeatWith/repeat no puede ser una variable: "%s"',
  'Index of a foreach/repeatWith/repeat cannot be a parameter: "%s"':
    'El índice de un foreach/repeatWith/repeat no puede ser un parámetro: "%s"',
  #
  'Cannot modify "%s": %s is immutable':
    'No se puede modificar "%s": %s es inmutable',
  'Cannot modify "%s": index of a foreach/repeatWith/repeat is immutable':
    'No se puede modificar "%s": es el índice de un foreach/repeatWith/repeat',

  'Nested foreach/repeatWith/repeat\'s cannot have the same index: "%s"':
    'foreach/repeatWith/repeat anidados no pueden tener el mismo índice: "%s"',
  #
  'function body of "%s" cannot be empty':
    'El cuerpo de la función "%s" no puede estar vacío\nDebe tener un return',
  'function "%s" should have a return':
    'La función "%s" debería tener un return',
  'procedure "%s" should not have a return':
    'El procedimiento "%s" no debería tener un return',
  'procedure "%s" should not have a procedure variable':
    'El procedimiento "%s" no debería tener una variable de procedimiento',
  'Can not use passing by reference when using the implicit board.':
    'No se puede utilizar pasaje por referencia cuanto se está utilizando el tablero implícito.',
  'procedure "%s" should have a procedure variable':
    'El procedimiento "%s" debería tener una variable de procedimiento',
  'Unknown command: %s': 'Comando no reconocido: %s',
  'Unknown expression: %s': 'Expresión no reconocida: %s',

# modules
  'Module %s cannot be found': 'No se encuentra el módulo %s',
  'Recursive modules': 'Módulos recursivos',
  'function %s was already imported': 'La función "%s" ya fue importada',
  'procedure %s was already imported': 'El procedimiento "%s" ya fue importado',
  'Error parsing module %s': 'Error de sintaxis al cargar el módulo "%s"',
  'Error linting module %s': 'Error al cargar el módulo "%s"',
  'Error typechecking module %s': 'Error de tipos al cargar el módulo "%s"',
  'Error compiling module %s': 'Error de compilación al cargar el módulo "%s"',

# liveness errors
  'Liveness analysis': 'Advertencia en el uso de las variables',
  'Variable "%s" possibly uninitialized':
    'La variable "%s" podría no tener asignado ningún valor\n' +
    'en este punto del programa',
  'Variable "%s" defined but not used':
    'La variable "%s" se asigna pero no se usa más',
  'Variables "(%s)" defined but not used':
    'Las variables "(%s)" se asignan pero ninguna se vuelve a usar',

# type inference errors
  'Type error': 'Error de tipos',
  'Types do not unify: %s %s':
    'No coinciden los tipos:\n%s\n%s',
  '"%s" has type: %s\nRight hand side has type: %s':
    '"%s" tiene tipo: %s\nEl lado derecho tiene tipo: %s',
  'procedure "%s" should take: %s\nBut takes: %s':
     'El procedimiento "%s" debería poder recibir: %s\nPero recibe: %s',
  'function "%s" should take: %s and return: %s\nBut takes: %s and returns: %s':
     'La función "%s" debería poder recibir: %s y devolver: %s\nPero recibe: %s y devuelve: %s',
  'Expression should have type: %s\nBut has type: %s':
    'La expresión debería tener tipo: %s\nPero tiene tipo: %s',
  'Literal should have type: %s\nBut has type: %s':
    'El literal debería tener tipo: %s\nPero tiene tipo: %s',
  'Expression can\'t have type: %s':
    'La expresión no puede tener el tipo: %s',
  'function "%s" is receiving: %s\nBut should receive: %s':
    'La función "%s" está recibiendo: %s\nPero debería recibir: %s',
  'constructor "%s" is receiving: %s\nBut should receive: %s':
    'El constructor "%s" está recibiendo: %s\nPero debería recibir: %s',
  'function "%s" is called as if it returned: %s\nBut returns: %s':
    'La función "%s" se usa como si devolviera: %s\nPero devuelve: %s',
  'procedure "%s" is receiving: %s\nBut should receive: %s':
    'El procedimiento "%s" está recibiendo: %s\nPero debería recibir: %s',
  '"%s" has type: %s\nFunction "%s" returns: %s':
    '"%s" tiene tipo: %s\nPero la función "%s" devuelve: %s',
  '"%s" is not a valid variant case for "%s" type.':
    '"%s" no es un caso válido para el tipo "%s".',

# type syntax errors
  '"%s" is not a type':
    '"%s" no es un tipo',
  'type "%s" expects %u parameters, but receives %u':
    'El tipo "%s" espera %u parámetros, pero está recibiendo %u',

# virtual machine
    'Runtime error':
        'Error en tiempo de ejecución',
    'Runtime type error':
        'Error de tipos en tiempo de ejecución',
    'Program has no entrypoint':
        'El programa no tiene un punto de entrada (procedimiento Main o bloque program)',
    'Uninitialized variable':
        'Variable no inicializada',
    'Identifier "%s" does not exists.':
        'El identificador %s no existe.',
    'Uninitialized variable: "%s"':
        'Variable no inicializada: "%s"',
    'Self destruction:':
        'Autodestrucción:',
    'Identifier refers to a primitive type and can not be projected.':
        'El identificador denota un tipo primitivo y no puede ser proyectado.',
    'Expression has no matching branch.':
        'La expresión del match no coincide con ninguna rama.',

    # Runtime type errors
    '"%s" field has type %s, but type %s was expected.':
        'El campo "%s" tiene tipo %s, pero se esperaba el tipo %s',

  # builtin runtime errors
    'Division by zero': 'División por cero',
    'Negative exponent': 'Potencia con exponente negativo',
    'Empty list': 'Lista vacía',
    '%s was expected': 'Se esperaba un %s',
    '%s type was expected': 'Se esperaba un tipo %s',
    'Function \'%s\' only applicable on %s':
        'Función \'%s\' aplicable solamente en %s',
    'The record doesn\'t have a field named "%s"\nThe available field names for this record are: %s':
        'El registro no posee un campo llamado "%s"\nLos campos disponibles en este registro son: %s',
    'Concatenation between lists with different inner type.':
        'Concatenación entre listas con diferente tipo interno.',
    '"%s" is not a valid field.':
        '"%s" no es un campo válido.',
    'Cannot apply "." operator to "%s"':
        'No se puede aplicar el operador "." a "%s"',
    '"%s" is not indexable.':
        '"%s" no puede inspeccionarse mediante un indice.',
    'The procedure call variable should be a board.':
        'La variable asociada a la llamada de procedimiento debe ser un tablero.',
    'List cursor does not refers to a valid value.':
        'El cursor de la lista no denota ningún valor.',
    '%s constructor expects %s field(s).':
        'El constructor del tipo %s espera recibir %s campo(s)',
    'Passing by reference is disabled when using implicit board.':
        'El pasaje por referencia está deshabilitado cuando se utiliza el modo de tablero implícito.',

  # dynamic type checking
  'Condition should be a boolean':
    'La condición debería ser un valor booleano',
  'Relational operation between values of different types':
    'Operación relacional entre valores de distintos tipos',
  'Relational operation different from equalities between values of %s are not allowed':
    'No se permiten operaciones relacionales distintas a la igualdad entre valores de %s',
  'Arithmetic operation over non-numeric values':
    'Operación aritmética sobre valores no numéricos',
  'Logical operation over non-boolean values':
    'Operación lógica sobre valores no booleanos',
  'The argument to PutStone should be a color':
    'El argumento de Poner debería ser un color',
  'The argument to TakeStone should be a color':
    'El argumento de Sacar debería ser un color',
  'The argument to Move should be a direction':
    'El argumento de Mover debería ser una dirección',
  'The argument to numStones should be a color':
    'El argumento de nroBolitas debería ser un color',
  'The argument to existStones should be a color':
    'El argumento de hayBolitas debería ser un color',
  'The argument to canMove should be a direction':
    'El argumento de puedeMover debería ser una dirección',
  'The argument to opposite should be a direction or an integer':
    'El argumento de opuesto debería ser una dirección o un entero',

# other errors
  'File %s does not exist': 'El archivo "%s" no existe.',

# getter-setter fields
    #'last': 'ultimo',
    #'head': 'cabeza',
    #'current': 'actual',
    #'tail': 'cola',
    #'init': 'comienzo',

# token names
  'a number': 'un número',
  'a string': 'una cadena',
  'a lowercase identifier': 'un identificador con minúscula',
  'an uppercase identifier': 'un identificador con mayúscula',
  'end of input': 'final del archivo',
  'beggining of input': 'comienzo del archivo',

# AST names
  'function definition': 'definición de función',
  'procedure definition': 'definición de procedimiento',
  'procedure call': 'invocación a procedimiento',
  'function call': 'invocación a función',
  'variable name': 'nombre de variable',
  'variable assignment': 'asignación de variable',
  'relational operator': 'operador relacional',
  'list operator': 'operador de listas',
  'arithmetic operator': 'operador aritmético',
  'logical operator': 'operador lógico',
  'import clause': 'cláusula from..import',

# builtin procedures
  'PutStone': 'Poner',
  'PutStoneN': 'PonerN',
  'TakeStone': 'Sacar',
  'Move': 'Mover',
  'GoToOrigin': 'IrAlOrigen',
  'GoToBoundary': 'IrAlBorde',
  'ClearBoard': 'VaciarTablero',

# list builtin rutines
  'Next': 'Avanzar',
  'GoToStart': 'IrAlInicio',
  'hasNext': 'hayMas',
  'AddFirst': 'AgregarAdelante',
  'Append': 'AgregarAtras',
  'DropFirst': 'SacarPrimero',
  'DropLast': 'SacarUltimo',

# builtin functions
  'numStones': 'nroBolitas',
  'existStones': 'hayBolitas',
  'canMove': 'puedeMover',
  'minBool': 'minBool',
  'maxBool': 'maxBool',
  'minDir': 'minDir',
  'maxDir': 'maxDir',
  'minColor': 'minColor',
  'maxColor': 'maxColor',
  'next': 'siguiente',
  'prev': 'previo',
  'opposite': 'opuesto',

# builtin constants
  'True': 'True',
  'False': 'False',

  'North': 'Norte',
  'South': 'Sur',
  'East': 'Este',
  'West': 'Oeste',

  'Color0': 'Azul',
  'Color1': 'Negro',
  'Color2': 'Rojo',
  'Color3': 'Verde',

# types
  'Color': 'Color',
  'Dir': 'Dir',
  'Bool': 'Bool',
  'Int': 'Int',
  'List': 'List',
  'Array': 'Arreglo',

# boards
  'Cannot show board, max number allowed is %s':
    'No se puede mostrar el tablero.\nEl máximo número permitido es %s',
  'Malformed board':
    'Archivo de tablero mal formado',
  'Loading of html boards not supported':
    'No se pueden cargar tableros en formato HTML',
  'Cannot take stones':
    'No se pueden sacar bolitas',
  'Cannot take stones of color %s':
    'No se puede sacar una bolita de color: %s\nNo hay bolitas de ese color',
  'Cannot move':
    'No se puede mover el cabezal\nLa posición cae afuera del tablero',
  'Cannot move to %s':
    'No se puede mover el cabezal en dirección: %s\nLa posición cae afuera del tablero',
  'Invalid direction':
    'Dirección inválida',

# misc
  'At': 'En',
  'At:': 'En:',
  'Locals:': 'Valores de los identificadores:',
  'to': 'hasta',
  'near': 'cerca de',
  'after': 'después de',
  'line': 'línea',
  'column': 'columna',
  'Prelude': 'Biblioteca',
  
# misc2
  'atomic values': 'valores atómicos',
  'atomic value': 'valor atómico',
  'list type values': 'valores de tipo lista',
  'list type value': 'valor de tipo lista',
  'string type value': 'valor de tipo cadena',

## command line
  'I18N_gbs_usage':
'''Uso: <PROG> entrada.gbs [opciones]
Opciones:
  [--from] tablero.{gbb,gbt,tex}  Ejecuta el programa en el tablero dado
  --to tablero.{gbb,gbt,tex}      Guarda el resultado en el tablero dado
  --size <ancho> <alto>           Tamaño del tablero generado
  --pprint                        Imprime el código fuente
  --print-ast                     Imprime el árbol sintáctico
  --print-asm                     Imprime el código de la máquina virtual
  --asm salida.gbo                Genera código para la máquina virtual
  --lint {lax,strict}             Nivel de la etapa de lint (default: strict)
  --no-typecheck                  No hace inferencia de tipos
  --no-liveness                   No hace análisis de variables vivas
  --no-print-board                No muestra el resultado por pantalla
  --no-print-retvals              No muestra los valores de retorno
  --style <estilo1,...,estiloN>   Formato para la salida del tablero
          compact                   .gbb,.gbbo: Formato compacto
          [no-]head                 .fig: [No] mostrar el cabezal
          [no-]labels               .fig: [No] mostrar etiquetas de filas y columnas
          [no-]colors               .fig: [No] usar colores
          [no-]color-names          .fig: [No] mostrar nombres de colores
  --jit                           Habilitar compilación Just in Time
  --print-jit                     Mostrar instrucciones del JIT
  --print-native                  Mostrar código nativo obtenido por el JIT
  --license                       Muestra la licencia del programa
Otros usos:
  <PROG> tablero_in.{gbb,gbt,tex} [--to tablero_out.{gbb,gbt,tex,html,fig}]
  <PROG> entrada.gbo [opciones]
''',
  'Wrote %s': 'Se escribió el archivo %s',

## GUI

  '&File': '&Archivo',
  '&New': '&Nuevo',
  '&Open': '&Abrir',
  '&Save': '&Guardar',
  'Save &as...': 'Guardar &como...',
  '&Quit': '&Salir',

  '&Edit': '&Editar',
  '&Undo': '&Deshacer',
  '&Redo': '&Rehacer',
  'Cu&t': 'Cor&tar',
  '&Copy': '&Copiar',
  '&Paste': '&Pegar',
  'Select &All': 'Seleccion&ar Todo',
  '&Find': '&Buscar',
  '&Indent region': '&Identar',
  '&Dedent region': '&Desidentar',
  '&Font family': '&Fuente',
  'Font &size': '&Tamaño de la fuente',
  '(&More...)': '(&Más...)',

  '&Gobstones': '&Gobstones',
  '&Run': 'E&jecutar',
  '&Check': '&Chequear',

  '&Board': '&Tablero',
  '&Empty board': '&Vaciar tablero',
  '&Random board': 'Modo aleato&rio',
  '&Random board size': 'Tamaño aleator&io',
  '&Change size': 'Cambiar &tamaño',
  '&Load board': '&Cargar tablero',
  '&Save board': '&Guardar tablero',
  'E&xport TeX': 'E&xportar TeX',
  'I&mport TeX': 'I&mportar TeX',

  '&Help': 'A&yuda',
  '&Version': '&Versión',
  '&License': '&Licencia',

  'File not saved': 'Archivo no guardado',
  'File has not been saved.\nSave it now?':
    'El archivo no fue guardado.\n¿Querés guardarlo ahora?',
  'Source must be saved': 'Hay que guardar el archivo',
  'Source must be saved.\nOk to save?':
    'Hay que guardar el archivo\n¿Querés guardarlo ahora?',

  'Open file': 'Abrir archivo',
  'Save file': 'Guardar archivo',
  'Gobstones source': 'Programa Gobstones',
  'Gobstones board': 'Tablero Gobstones',
  'Gobstones board (old format)': 'Tablero Gobstones (formato antiguo)',
  'TeX/LaTeX file': 'Archivo TeX/LaTeX',
  'HTML file': 'Archivo HTML',
  'All files': 'Todos los archivos',

  'Change board size': 'Cambiar tamaño del tablero',
  'Width:': 'Ancho',
  'Height:': 'Alto',
  'Invalid board size': 'Tamaño de tablero inválido.\nEl ancho y el alto deben ser números entre 1 y 200.',

  'Untitled': 'Sin título',

  'All checks ok': 'El programa está bien formado.\n',

  'Stop': 'Parar',
  'Execution interrupted by the user': 'La ejecución del programa fue interrumpida por el usuario.\nEs posible que el programa se haya colgado debido a un while que no termina.',

  'Gobstones version': 'PyGobstones versión',

# Board viewer
  'Initial board': 'Tablero inicial',
  'Final board': 'Tablero final',
  'Board viewer': 'Visor de tableros',
  'There is no board to save': 'No hay tablero para guardar',

  'I18N_stone_border0': hsv(0.66, .55, .55), # azul
  'I18N_stone_border1': hsv(0,      0, .55), # negro
  'I18N_stone_border2': hsv(0,    .55, .55), # rojo
  'I18N_stone_border3': hsv(0.33, .55, .55), # verde

  'I18N_stone_fill0': hsv(0.66, .55, .95), # azul
  'I18N_stone_fill1': hsv(0,      0, .75), # negro
  'I18N_stone_fill2': hsv(0,    .55, .95), # rojo
  'I18N_stone_fill3': hsv(0.33, .55, .95), # verde

  'I18N_mark0': hsv(0.66, .75, .75), # azul
  'I18N_mark1': hsv(0,      0, .25), # negro
  'I18N_mark2': hsv(0,    .75, .75), # rojo
  'I18N_mark3': hsv(0.33, .75, .75), # verde

# Log messages
  'Parsing.': 'Haciendo análisis sintáctico.',
  'Exploding program macros.': 'Explotando macros del programa.',
  'Performing semantic checks.': 'Haciendo análisis semántico.',
  'Compiling.': 'Compilando.',
  'Starting program execution.': 'Ejecutando el programa.',
  'Program execution finished.': 'Ejecución finalizada.',

# Judge
  '&Problems': 'Pro&blemas',
  '&Solve problem': '&Resolver problema',
  'Solve problem': 'Resolver problema',
  'Problem name:': 'Nombre del problema:',
  'There is no valid @test directive':
    'La herramienta de testeo requiere una directiva @test. Algo como:\n' + \
    '    // @test\n'
    '    procedure PonerVerde()\n',
  'Too many @test directives':
    'Debe haber una sola ocurrencia de la directiva @test.',
  'Problem "%s" does not exist': 'El problema "%s" no existe',
  'Program solving problem "%s" was accepted by judge':
    'La resolución del problema "%s" fue aceptada.\n' + \
    'Pero cuidado:\n' + \
    '"Hacer tests puede mostrar la presencia de errores,\n    nunca su ausencia".\n' + \
    '      [Edsger W. Dijkstra]',
  'Program failed on test case "%s". Debug program and retry.':
    'La resolución del problema no funciona\npara el test "%s".\nCorregí el programa y volvé a probar.',
  'Runtime error. Debug program and retry.':
    'La resolución del problema tiene algún error.\nCorregí el programa y volvé a probar.',
  'Program failed on some test cases. Debug program and retry.':
    'La resolución del problema no funciona\npara alguno de los tests.\nCorregí el programa y volvé a probar.',

# Judge reports
  'Test case "%s" failed': 'Test "%s"',
  'Test case': 'Test',
  'Source code': 'Código fuente',
  'Expected result': 'Esperado',
  'Obtained result': 'Obtenido',
  'Expected final board': 'Tablero final esperado',
  'Obtained final board': 'Tablero final obtenido',
  'Returned variables': 'Variables devueltas',
  'No returned variables': 'Ninguna',
  'No result': 'No se obtuvo un resultado',

# Test driver
  'Starting problem %s': 'Problema %s.',
  'Starting test case %s.': 'Probando tablero inicial: %s',
  'Checking fingerprints': 'Comparando los resultados',

# Version
  'I18N_gbs_version(%s)': 'PyGobstones versión %s\nIntroducción a la programación\nTPI, UNQ, 2011-2012\n',
}

# English
EN = {

  '"%s" is not a index': '"%s" is not an index',

## command line
  'I18N_gbs_usage':
'''Usage: <PROG> source.gbs [options]
Options:
  [--from] board.{gbb,gbt,tex}  Run the program in the given board file
  --to board.{gbb,gbt,tex}      Save the result in the given board file
  --size <width> <height>       Size of the input board when randomized
  --pprint                      Pretty print source code
  --print-ast                   Print the abstract syntax tree
  --print-asm                   Print the code for the virtual machine
  --asm output.gbo              Generate virtual machine code
  --lint {lax,strict}           Strictness of the lint stage (default: strict)
  --no-typecheck                Don't do type inference
  --no-liveness                 Don't do live variable analysis
  --no-print-board              Don't output the result
  --no-print-retvals            Don't output the return values
  --compact                     Use compact format for dumping .gbb and .gbo files
  --jit                         Enable Just in Time compiler
  --print-jit                   Print JIT instructions
  --print-native                Print JIT native code

Other usages:
  <PROG> board_in.{gbb,gbt,tex} [--to board_out.{gbb,gbt,tex,html,fig}]
  <PROG> input.gbo [options]
''',

# builtin constants
  'Color0': 'Cyan',
  'Color1': 'Black',
  'Color2': 'Red',
  'Color3': 'Violet',

# Board viewer
  'I18N_stone_border0': hsv(0.5,  .55, .55),
  'I18N_stone_border1': hsv(0,      0, .55),
  'I18N_stone_border2': hsv(0,    .55, .55),
  'I18N_stone_border3': hsv(0.8,  .55, .55),

  'I18N_stone_fill0': hsv(0.5,  .55, .95),
  'I18N_stone_fill1': hsv(0,      0, .75),
  'I18N_stone_fill2': hsv(0,    .55, .95),
  'I18N_stone_fill3': hsv(0.8,  .55, .95),

  'I18N_mark0': hsv(0.5,  .75, .75),
  'I18N_mark1': hsv(0,      0, .25),
  'I18N_mark2': hsv(0,    .75, .75),
  'I18N_mark3': hsv(0.8,  .75, .75),

# Version
  'I18N_gbs_version(%s)': 'PyGobstones version %s\n',

}

Language = ES

def i18n(s):
  # return the original string if no translation is found
  return Language.get(s, s)

Token_type_descriptions = {
  'EOF': i18n('end of input'),
  'BOF': i18n('beggining of input'),
  'num': i18n('a number'),
  'string': i18n('a string'),
  'lowerid': i18n('a lowercase identifier'),
  'upperid': i18n('an uppercase identifier'),
}

AST_type_descriptions = {
  'function': i18n('function definition'),
  'procedure': i18n('procedure definition'),
  'procCall': i18n('procedure call'),
  'assignVarName': i18n('variable assignment'),
  'varName': i18n('variable name'),
  'funcCall': i18n('function call'),
  'and': i18n('logical operator'),
  'or': i18n('logical operator'),
  'not': i18n('logical operator'),
  'relop': i18n('relational operator'),
  'listop': i18n('list operator'),
  'addsub': i18n('arithmetic operator'),
  'mul': i18n('arithmetic operator'),
  'pow': i18n('arithmetic operator'),
  'divmod': i18n('arithmetic operator'),
  'unaryMinus': i18n('arithmetic operator'),
  'import': i18n('import clause'),
}

