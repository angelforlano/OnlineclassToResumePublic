# Online class (video) to resume using Chat GPT and Whisper

Este script usa 2 sistemas de inteligencia artificial para generar resúmenes escritos sobre las clases online o videos que le proporciones. Para esto usa primero Whisper que su modelo de inteligencia artificial para transcribir voz (audio) a texto (LINK) luego estos textos transcritos se resumen y analizan usando la api de Chat GPT 3. para lograr esto el código hace lo siguiente:

Coge cualquier archivo de la carpeta “TODO” y lo primero que hace es crear 4 sub carpetas dentro de la carpeta (del mismo nombre del archivo) “DONE”, estas carpetas son “clips”, “transcription”,  “notes” y “resumes”.

esto se hace porque el proceso está dividido en 4 partes principales:

Parte 1: corta el video original en partes de 15 min (los “clips”), ya que whisper aunque sea un sistema muy bueno se confunde con audios muy largos y con archivos de más de 2 horas ya casi no puede procesarlos.

Parte 2: se recogen todos los clips y ahora si se procesan y se transcriben individualmente con whisper (uno por uno), cada transcripción se guarda en la carpeta “transcription” con el nombre del clip. Al finalizar todos los archivos se juntan en 1 solo llamado “all_transcription.txt”

Parte 3: Ahora del archivo “all_transcription.txt” hay que generar “notes”, esto se hace porque no podemos tampoco resumir y analizar un archivo de texto tan gran con chap GPT, por eso se separan en notas más o menos equivalentes a una página de texto, Concretamente se reducen a aproximadamente unas 700 palabras por texto (Esto se puede cambiar a más bajo para tener mejores resúmenes).

Parte 4: Una vez hecho eso, ya si se procede a pedir a Chat GPT un resumen de cada una de las notas y luego se juntan de nuevo en el archivo “all_summarized.txt” si todo ha salido bien deberíamos de tener un resumen bastante decente, un ejemplo seria este:

	""Resumen: Se discutió cómo normalizar, cargar y configurar los datos para mejorar la comprensión de los usuarios. Se recomendó usar gráficos evolutivos, mapas de calor, gráficos de votos y carriles para representar los datos. Se sugirió añadir filtros para mejorar la visualización de los datos. Se aconsejó tener cuidado con los datos que se reciben para asegurarse de que no es azar o casualidad.""

Este es un resumen extraído de una de las notas.

# Como Usar

Para usarlo primero hay que instalar whisper (Link), y todos los requisitos del archivo requirements. tambien hay que crear un archivo llamdao “appsecrets.py” donde pondremos nuestra clave API de Open AI para poder usar el chat gpt, la variable debe llamarse OPENAI_KEY = "KEY-HERE"
