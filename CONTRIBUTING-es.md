*Lea esto en otros idiomas: [Deutsch](CONTRIBUTING-de.md), [English](CONTRIBUTING.md), [Français](CONTRIBUTING-fr.md), [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [Português Brasileiro](CONTRIBUTING-pt_BR.md), [한국어](CONTRIBUTING-ko.md).*

<a name="contributor-license-agreement"></a>
## Acuerdo de Licencia

Al contribuir, acepta la [LICENCIA][license] de este repositorio.


<a name="contributor-code-of-conduct"></a>
## Código de Conducta como Colaborador

Al contribuir, acepta respetar el [Código de Conducta][coc] presente en el repositorio.


<a name="in-a-nutshell"></a>
## Breve resumen

1. "Un enlace para descargar fácilmente un libro" no siempre es un enlace a un libro *gratuito*. Por favor, contribuya solo con contenido gratuito. Asegúrese de que se ofrezca gratis. No se aceptan enlaces a páginas que *requieran* de direcciones de correo electrónico para la obtención de libros, pero sí damos la bienvenida a aquellos listados que así se soliciten.
2. No es necesario conocer Git: si encontró algo de interés que *no esté ya en este repositorio*, tenga el gusto de abrir una [Issue][issues] con su propuesta de enlaces.
    - Si ya maneja Git, haga un Fork del repositorio y envíe su contribución mediante Pull Request (PR).
3. Dispone de 5 categorías. Seleccione aquel listado que crea conveniente según:

    - *Libros* : PDF, HTML, ePub, un recurso alojado en gitbook.io, un repositorio Git, etc.
    - *Cursos* : Un curso es aquel material de aprendizaje que no es un libro. [Esto es un curso](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutoriales interactivos* : Un sitio web se considera interactivo si permite al usuario escribir código o comandos y evaluar su resultado ("evaluar" no significa "obtener una calificación"). Por ejemplo: [Pruebe Haskell](http://tryhaskell.org), [Pruebe GitHub](http://try.github.io).
    - *Podcasts y Screencasts* : Son aquellas retransmisiones grabadas ya sea en audio y/o en vídeo, respectivamente.
    - *Conjuntos de problemas & Programación competitiva* : Se trata de un sitio web o software que le permita evaluar sus habilidades de programación resolviendo problemas simples o complejos, con o sin revisión de código, con o sin comparar los resultados con otros usuarios.

4. Asegúrese de seguir la [guía de pautas que mostramos a continuación][guidelines] así como de respetar el [formato Markdown][formatting] de los ficheros.

5. GitHub Actions ejecutará pruebas para asegurarse de que las listas esten ordenadas alfabéticamente y de que se siga dicha normalización de formateo. Asegúrese de verificar que sus cambios pasen todas estas comprobaciones de calidad.


<a name="guidelines"></a>
### Pautas

- Revise si el libro es gratuito. Hágalo las veces que sean necesarias. Ayude a los administradores comentando en las Pull Request por qué cree que el libro se ofrece gratis o es valioso.
- No se aceptan ficheros alojados en Google Drive, Dropbox, Mega, Scribd, Issuu u otras plataformas de almacenamiento y/o descarga similares.
- Inserte los enlaces ordenados alfabéticamente. Si se encuentra por casualidad con un enlace fuera de sitio, por favor ordénelo y envíe la correspondiente PR para poder arreglarlo.
- Use el enlace que apunte a la fuente más fidedigna. Esto es, el sitio web del autor es mejor que el del editor y éste a su vez mejor que uno de terceros.
    + No use servicios de almacenamiento en la nube. Esto incluye, aunque sin limitar, enlaces a Dropbox y Google Drive.
- Es siempre preferible el uso de enlaces con protocolo `https` en vez de `http` si ambos se refieren al mismo dominio y sirven el mismo contenido.
- En los dominios raíz, elimine la barra inclinada del final: `http://example.com` en lugar de `http://example.com/`.
- Utilice preferentemente la forma corta de los hipervínculos: `http://example.com/dir/` es mejor que `http://example.com/dir/index.html`.
   + No se admiten acortadores de enlaces URL.
- Por lo general, se prefiere el enlace "actual" sobre el de "versión": `http://example.com/dir/book/current/` es más asequible que `http://example.com/dir/book/v1.0.0/index.html`.
- Si en un enlace se encuentra con algún problema de certificados, ya sea caducado, autofirmado o de cualquier otro tipo:
  1. *Reemplácelo* con su análogo `http` si fuera posible (porque aceptar excepciones puede ser complicado en dispositivos móviles).
  2. *Manténgalo* si no existe versión `http` pero el enlace aún es accesible a través de `https` agregando una excepción al navegador o ignorando la advertencia.
  3. *Elimínelo* en cualquier otro caso.
- Si existe un mismo enlace con varios formatos, anexe enlaces aparte con una nota sobre cada formato.
- Si un recurso existe en diferentes lugares de Internet:
    + Use aquella fuente más fidedigna (lo que significa que el sitio web del propio autor es más asequible que el sitio web del editor y a su vez éste es mejor que una fuente de terceros).
    + Si apuntan a diferentes ediciones y considera que estas ediciones son lo suficientemente dispares como para que valga la pena conservarlas, agregue por separado un nuevo enlace haciendo alusión a cada edición. Diríjase al [Issue \#2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) si desea contribuir en la discusión acerca del formateo que deben seguir dichos registros.
- Es preferible realizar commits atómicos (un commit por cada adición/eliminación/modificación) frente a unos con mayor calado. No es necesario realizar un squash de todos ellos antes de enviar una PR. (Nunca aplicaremos esta regla, ya que solamente es una cuestión de conveniencia para quien mantiene el proyecto).
- Si se trata de un libro más antiguo, incluya su fecha de publicación dentro del título.
- Incluya el nombre o nombres de autor/es cuando corresponda. Puede valerse de "`et al.`" para acortar esa enumeración de autores.
- Si el libro no está terminado y aún se está trabajando en él, agregue la anotación de "`en proceso`", tal y como se describe [a continuación][in_process].
- En el caso de que decida recuperar un recurso usando servicios como [*Internet Archive's Wayback Machine*](https://web.archive.org), anexe la anotación "`archived`" (en consonancia con el idioma) tal y como se describe [a continuación][archived]. Use como mejor versión aquella que sea la más reciente y completa.
- Si se solicita una dirección de correo electrónico o configuración de cuenta antes de habilitar la descarga, agregue entre paréntesis dichas notas y en consonancia con el idioma. Por ejemplo: `(*se solicita* email, no requerido...)`.


<a name="formatting"></a>
### Formato normalizado

- Como podrá observar, los listados tienen `.md` como extensión de fichero. Intente aprender la sintaxis [Markdown][markdown_guide]. ¡Es bastante simple!
- Dichos listados comienzan con una Tabla de Contenidos (TOC). Este índice permite enumerar y vincular todas las secciones y subsecciones en las que se clasifica cada recurso. Manténgalo también en orden alfabético.
- Las secciones utilizan encabezados de nivel 3 (`###`) y las subsecciones de nivel 4 (`####`).

La idea es tener:
- `2` líneas vacías entre el último enlace de una sección y el título de la siguiente sección.
- `1` línea vacía entre la cabecera y el primer enlace de una determinada sección.
- `0` líneas en blanco entre los distintos enlaces.
- `1` línea en blanco al final de cada fichero `.md`.

Ejemplo:

    [...]
    * [Un libro increíble](http://example.com/example.html)
                                    (línea en blanco)
                                    (línea en blanco)
    ### Sección de ejemplo
                                    (línea en blanco)
    * [Otro libro fascinante](http://example.com/book.html)
    * [Otro libro más](http://example.com/other.html)

- Omita los espacios entre `]` y `(`:

   ```
   INCORRECTO : * [Otro libro fascinante] (http://example.com/book.html)
   CORRECTO   : * [Otro libro fascinante](http://example.com/book.html)
   ```

- Si en el registro decide incluir al autor, emplee ` - ` (un guión rodeado de espacios simples) como separador:

   ```
   INCORRECTO : * [Un libro sencillamente fabuloso](http://example.com/book.html)- John Doe
   CORRECTO   : * [Un libro sencillamente fabuloso](http://example.com/book.html) - John Doe
   ```

- Ponga un solo espacio entre el enlace al contenido y su formato:

   ```
   INCORRECTO : * [Un libro muy interesante](https://example.org/book.pdf)(PDF)
   CORRECTO   : * [Un libro muy interesante](https://example.org/book.pdf) (PDF)
   ```

- El autor se antepone al formato:

   ```
   INCORRECTO : * [Un libro muy interesante](https://example.org/book.pdf)- (PDF) Jane Roe
   CORRECTO   : * [Un libro muy interesante](https://example.org/book.pdf) - Jane Roe (PDF)
   ```

- Múltiples formatos:

   ```
   INCORRECTO : * [Otro libro interesante](http://example.com/) - John Doe (HTML)
   INCORRECTO : * [Otro libro interesante](https://downloads.example.org/book.html) - John Doe (sitio de descarga)
   CORRECTO   : * [Otro libro interesante](http://example.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.example.org/book.html)
   ```

- Incluya el año de publicación como parte del título de los libros más antiguos:

   ```
   INCORRECTO : * [Un libro bastante especial](https://example.org/book.html) - Jane Roe - 1970
   CORRECTO   : * [Un libro bastante especial (1970)](https://example.org/book.html) - Jane Roe
   ```

<a name="in_process"></a>
- Libros en proceso / no acabados aún:

   ```
   CORRECTO: * [A punto de ser un libro fascinante](http://example.com/book2.html) - John Doe (HTML) (:construction: *en proceso*)
   ```

<a name="archived"></a>
- Enlaces archivados:

   ```
   CORRECTO: * [Un recurso recuperado a partir de su línea de tiempo](https://web.archive.org/web/20211016123456/http://example.com/) - John Doe (HTML) *(:card_file_box: archivado)*
   ```


<a name="notes"></a>
### Anotaciones

Si bien los conceptos básicos son relativamente simples, existe una gran diversidad entre los recursos que enumeramos. Aquí hay algunas notas sobre cómo nos ocupamos de esta diversidad.

<a name="metadata"></a>
#### Metadatos

Nuestros listados proporcionan un conjunto mínimo de metadatos: títulos, URL, autores, formato, plataformas y notas de acceso.

<a name="titles"></a>
##### Títulos

- Sin títulos inventados: Intentamos tomar el texto de los propios recursos; se advierte a los colaboradores que, si puede evitarse, no inventen títulos ni los utilicen editorialmente. Una excepción es para obras más antiguas: si son principalmente de interés histórico, un año entre paréntesis adjunto al título ayuda a los usuarios a saber si estos son de interés.
- Sin títulos todo en mayúsculas: Por lo general, es apropiado tener cada primera letra de palabra en mayúsculas, pero en caso de duda, use siempre el estilo tal y como viene en la fuente original.

<a name="urls"></a>
##### Direcciones URL

- No se permiten acortadores de URLs para los enlaces.
- Los parámetros de consulta o códigos referentes al seguimiento o campañas de marketing deben eliminarse de la URL.
- Las URL internacionales deben escaparse. Las barras del navegador suelen representar los caracteres en Unicode, pero utilice copiar y pegar, por favor; es la forma más rápida de construir un hipervínculo válido.
- Las URL seguras (https) siempre son mejor opción frente a las no seguras (http) donde se ha implementado el protocolo de comunicación encriptado HTTPS.
- No nos gustan las URL que apuntan a páginas web que no alojen el recurso mencionado, enlazando por el contrario a otra parte.

<a name="creators"></a>
##### Atribuciones

- Queremos dar crédito a los creadores de recursos gratuitos cuando sea apropiado, ¡incluso traductores!
- En el caso de obras traducidas, se debe acreditar también al autor original.
- No permitimos enlaces directos al creador.
- En el caso de recopilaciones u obras remezcladas, el "creador" puede necesitar una descripción. Por ejemplo, los libros de "GoalKicker" o "RIP Tutorial" se acreditan como "`Creado a partir de la documentación de StackOverflow`" (en inglés: "`Compiled from StackOverflow documentation`").

<a name="platforms-and-access-notes"></a>
##### Plataformas y Notas de Acceso

- Cursos. Especialmente para nuestras listas de cursos, la plataforma es una parte importante de la descripción del recurso. Esto se debe a que las plataformas de cursos tienen diferentes prestaciones y modelos de acceso. Si bien generalmente no incluimos un libro que requiere de registro previo, muchas plataformas de cursos tienen la casualidad de no funcionar sin algún tipo de cuenta. Un ejemplo de plataformas de cursos podrían ser: Coursera, EdX, Udacity y Udemy. Cuando un curso depende de una plataforma, el nombre de dicha plataforma debe aparecer entre paréntesis.
- YouTube. Tenemos muchos cursos que consisten en listas de reproducción de YouTube. No incluimos Youtube como plataforma, sino que tratamos de incluir al creador de Youtube, el cuál es a menudo una sub-plataforma en sí.
- Vídeos de YouTube. Por lo general, no vinculamos a vídeos individuales de YouTube a menos que tengan más de una hora de duración y estén estructurados como un curso o un tutorial.
- LeanPub. LeanPub aloja libros con una amplia variedad de modelos de acceso. A veces, un libro se puede leer sin registrarse; en otras, un libro requiere una cuenta LeanPub para tener acceso gratuito. Dada la calidad de los libros y la mezcla y fluidez de los modelos de acceso Leanpub, damos validez a estos últimos anexando la nota de acceso: `*(cuenta Leanpub o email válido requerido)*`.

<a name="genres"></a>
#### Géneros

La primera regla para decidir en qué listado encaja un determinado recurso es ver cómo se describe a sí mismo. Si por ejemplo se retrata a sí mismo como un libro, entonces tal vez es que lo sea.

<a name="genres-we-dont-list"></a>
##### Géneros no aceptados

Ya que en Internet podemos encontrar una variedad infinita de recursos, no incluimos en nuestro registro:

- blogs
- publicaciones de blogs
- artículos
- Sitios web (excepto aquellos que alberguen MUCHOS elementos que podamos incluir en los listados).
- vídeos que no sean cursos o screencasts (retrasmisiones)
- capítulos sueltos a libros
- muestras o introducciones de libros
- Canales/grupos de IRC, Telegram...
- Canales/salas de Slack... o listas de correo

El [listado donde incluimos sitios o software de programación competitiva][programming_playgrounds_list] no es tan restrictivo. El alcance de este repositorio es determinado por la comunidad; si desea sugerir un cambio o extender el alcance, utilice los [issues][issues] para registrar dicha sugerencia.

<a name="books-vs-other-stuff"></a>
##### Libros vs. Otro Material

No somos tan quisquillosos con lo que consideramos como libro. A continuación, se muestran algunas propiedades que un recurso pueda encajar como libro:

- tiene un ISBN
- tiene una Tabla de Contenidos (TOC)
- se ofrece una versión para su descarga electrónica, especialmente ePub.
- tiene diversas ediciones
- no depende de un contenido interactivo extra o vídeos
- trata de abordar un tema de manera integral
- es autosuficiente

Hay muchos libros que enumeramos los cuáles no poseen estos atributos; esto puede depender del contexto.

<a name="books-vs-courses"></a>
##### Libros vs. Cursos

¡A veces distinguir puede ser dificultoso!

Los cursos suelen tener libros de texto asociados, que incluiríamos en nuestras listas de libros. Además, los cursos tienen conferencias, ejercicios, pruebas, apuntes u otras ayudas didácticas. Una sola conferencia o vídeo por sí solo no es un curso. Un presentación de PowerPoint tampoco puede ser catalogado como curso.

<a name="interactive-tutorials-vs-other-stuff"></a>
##### Tutoriales interactivos vs. Otro Material

Si es posible imprimirlo y conservar su esencia, no es un Tutorial Interactivo.


<a name="automation"></a>
### Automatización

- El cumplimiento de las reglas de formateado se automatiza vía [GitHub Actions](https://docs.github.com/en/actions) usando [fpb-lint](https://github.com/vhf/free-programming-books-lint) (ver [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- La validación de URLs se realiza mediante [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Para activar esta validación de URL, envíe un commit que incluya como mensaje de confirmación `check_urls=fichero_a_comprobar`:

    ```
    check_urls=free-programming-books.md free-programming-books-en.md
    ```

- Es posible especificar más de un fichero a comprobar. Simplemente use un espacio para separar cada entrada.
- Si especifica más de un archivo, los resultados obtenidos se basan en el estado del último archivo verificado. Debe tenerlo en cuenta ya que, debido a esto, puede obtener falsos positivos al finalizar el proceso. Así que tras el envío de la pull request asegúrese de inspeccionar el registro de compilación haciendo clic en "Show all checks" -> "Details".


[license]: https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE
[coc]: https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT-es.md
[issues]: https://github.com/EbookFoundation/free-programming-books/issues
[formatting]: #formato-normalizado
[guidelines]: #pautas
[in_process]: #in_process
[archived]: #archived
[markdown_guide]: https://guides.github.com/features/mastering-markdown/
[programming_playgrounds_list]: (https://github.com/EbookFoundation/free-programming-books/blob/master/more/free-programming-playgrounds.md)
