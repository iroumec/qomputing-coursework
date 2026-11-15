## El Hadamard en x3

No es un error, sale de la función `grover`. Para cada qubit auxiliar hace:

```python
for i in ancillas:
    qc.x(i)
    qc.h(i)
```

La X seguida de H lleva el auxiliar de $|0\rangle$ a $|-\rangle$. Ese estado es lo que permite que la `mcx` del oráculo deje una fase $-1$ solo sobre el estado marcado (_phase kickback_), y por eso el oráculo funciona. Si lo sacás, el histograma deja de concentrarse en `011`. En el dibujo se ve una X y una H seguidas sobre $x_3$. Conviene explicarlo en el notebook, porque a un lector le va a parecer raro igual que a vos. Por ejemplo, reemplazando el markdown de la celda 47:

> Este usa un qubit adicional para almacenar el resultado. Dicho qubit se prepara en el estado $|-\rangle$ (compuertas X y H), de modo que, al aplicar la compuerta X multicontrolada, el estado marcado recibe una fase $-1$ por _phase kickback_.

## Revisión del resto

La lógica de fondo está bien. El operador de Grover se verifica contra la matriz, la separación entre qubits de búsqueda y totales funciona, y los resultados coinciden con la teoría. Estos son los puntos que corregiría:

**1. El enlace de Quirk (celda 45) sigue sin coincidir con tu código.** Pone X en $x_1$ y $x_2$, y usa Z en el cuarto cable, mientras que tu código usa X solo en $x_2$ y una `mcx`. Este sería el equivalente a tu oráculo (no abrí el enlace, probalo):

```
https://algassert.com/quirk#circuit={%22cols%22:[[1,1,%22X%22],[%22%E2%80%A2%22,%22%E2%80%A2%22,%22%E2%80%A2%22,%22X%22],[1,1,%22X%22]]}
```

Ojo: en Quirk el cuarto cable arranca en $|0\rangle$. Para ver el efecto como en Qiskit tendrías que prepararlo en $|-\rangle$.

**2. Faltan conclusiones.**

- _Ejercicio 3:_ la consigna pide determinar y justificar el número ideal de iteraciones, y el notebook termina en los histogramas.
- _Ejercicio 2, inciso II:_ no hay texto de conclusión.
- _Ejercicio 1:_ conviene decir qué estado se amplifica en cada inciso.

Como referencia para validar, estas son las probabilidades teóricas de medir el estado marcado:

| Iteraciones | N = 8 (3 qubits) | N = 32 (5 qubits) |
| ----------- | ---------------- | ----------------- |
| 1           | 0.78             | 0.26              |
| 2           | 0.95             | 0.60              |
| 3           | 0.33             | 0.90              |
| 4           | 0.01             | 1.00              |
| 5           | 0.55             | 0.86              |

Tu texto de la celda 41 es correcto. También podrías mencionar que con 4 y 5 iteraciones la probabilidad oscila: con 4 cae casi a cero y con 5 vuelve a subir, porque el algoritmo "se pasa" de rotación.

**3. Fase global del operador de Grover (celda 8 y 13).** Tu circuito implementa $I - 2|s\rangle\langle s|$, que es el negativo del difusor estándar $2|s\rangle\langle s| - I$. Es una fase global, así que no afecta nada acá. Pero si querés que el informe lo aclare, una línea alcanza.

**4. Detalles de estilo y prolijidad.**

- Celda 2: `transpile` se importa dos veces. Podés dejar solo `from qiskit import QuantumCircuit, transpile`.
- Celda 4: `rng` no se usa en ningún lado.
- Celda 8: "la compuerta Z no puede visualizar correctamente" → "no puede visualizarse correctamente".
- Celda 15: la validación `if qubits > total_qubits` conviene moverla antes de calcular `ancillas`, y "Se applica" → "Se aplica".
- Celda 25: el comentario dice "solo sobre los qubits de búsqueda", pero por defecto mide todos. Se aclara con "(o sobre todos, si no se indica)".
- Celda 37: la descripción no menciona el parámetro `measured_qubits`.
- Celda 46: aparece `<qiskit.circuit.instructionset.InstructionSet ...>` como salida. Se evita con `_ = oraculo_3.x(2)` o con `;` al final de esa última línea.
- Celda 50: "Se construyé" → "Se construyó".

Como siempre, no pude ejecutar Qiskit acá. Lo que dije sobre los resultados sale de mi simulación y de las fórmulas teóricas, así que si algún histograma de los tuyos se aleja bastante de esa tabla, mostramelo y lo revisamos.
