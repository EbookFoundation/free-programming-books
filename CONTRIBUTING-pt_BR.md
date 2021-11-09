*Leia em outros idiomas: [Deutsch](CONTRIBUTING-de.md), [Français](CONTRIBUTING-fr.md), [Español](CONTRIBUTING-es.md), [Indonesia](CONTRIBUTING-id.md),[简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md), [한국어](CONTRIBUTING-ko.md).*

## Acordo de Licença do Contribuidor
Ao contribuir você concorda com a [LICENSE](https://github.com/EbookFoundation/free-programming-books/blob/master/LICENSE) deste repositório.

## Código de Conduta do Contribuidor
Ao contribuir você concorda em respeitar o [Código de Conduta](https://github.com/EbookFoundation/free-programming-books/blob/master/CODE_OF_CONDUCT-pt_BR.md) deste repositório.

## Em poucas palavras
1. "Um _link_ para baixar um livro facilmente" nem sempre é um _link_ para um livro *gratuito*. Por favor contribua apenas com conteúdo gratuito. Certifique-se de que é grátis. Não são aceitos _links_ para páginas que *requerem* um endereço de email para obter livros, mas aceitamos listas que requerem.

2. Não é necessário saber Git: se você encontrou algo interessante que *não está presente neste repositório*, por favor abra uma [Issue](https://github.com/EbookFoundation/free-programming-books/issues) com todas as propostas de _links_.
    - Se você sabe Git, faça um _Fork_ do repositório e mande um _pull request_.

3. Possuimos 5 tipos de listas. Escolha a mais adequada:
    - *Livros*: PDF, HTML, ePub, sites baseados no gitbook.io, um repositório Git, etc.
    - *Cursos*: Um curso é um material didático que não é um livro. [Isso é um curso](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutoriais Interativos*: Um site interativo que permite ao usuário digitar código ou comandos e computa o resulta (por "computar" não queremos dizer "avaliar"). Por exemplo: [Try Haskell](http://tryhaskell.org), [Try Github](http://try.github.io).
    - *Podcasts e Screencasts* : Podcasts e screencasts.
    - *Conjuntos de Problemas e Programação Competitiva* : Um site ou software que permite avaliar suas habilidades de programação através da resolução de problemas simples ou complexos, com ou sem revisão de código, com ou sem comparação de resultados com outros usuários.

4. Certifique-se de seguir as [diretrizes abaixo](#diretrizes) e respeitar a [formatação de Markdown](#formatação) dos arquivos.

5. GitHub Actions executará testes para assegurar que suas listas estão em ordem alfabética e seguem as regras de formatação. Cerfique-se de que suas alterações passaram pelos testes.

### Diretrizes
- certifique-se de que o livro é gratuito. Verifique múltiplas vezes se necessário. Comentar no PR por quê você acha que o livro é gratuito ajuda os administradores.
- não aceitamos arquivos hospedados no Google Drive, Dropbox, Mega, Scribd, Issuu e outras plataformas similares de _upload_ de arquivos.
- insira seus _links_ em ordem alfabética. Se vir um _link_ fora de ordem, por favor reordene-o e crie um PR.
- use o _link_ com a fonte mais oficial (isso significa que o site do próprio autor é melhor que o site da editora, que é melhor que sites de terceiros)
    + sem serviços de hospedagem de arquivos (isso inclui (mas não se limita a) _links_ do Dropbox e Google Drive)
- sempre prefira um _link_ `https` em vez de `http` -- desde que estejam no mesmo domínio e sirvam o mesmo conteúdo.
- em domínios raiz, remova a barra final: `http://exemplo.com` ao invés de `http://exemplo.com/`
- sempre prefira o _link_ mais curto: `http://exemplo.com/dir/` é melhor que `http://exemplo.com/dir/index.html`
    + sem _links_ vindos de encurtadores de _links_
- prefira o _link_ "_current_" ao invés de _"version"_: `http://exemplo.com/dir/book/current/` é melhor que `http://exemplo.com/dir/book/v1.0.0/index.html`
- se um _link_ possui um certificado expirado/autoassinado/problema de SSL de qualquer outro tipo:
  1. *substitua-o* por seu equivalente `http` se possível (pois aceitar exceções pode ser complicado em dispositivos móveis).
  2. *mantenha-o* se não houver versão `http` disponível, mas o _link_ continua acessível através de `https` adicionando uma exceção ao browser ou ignorando o aviso.
  3. *remova-o* caso contrário.
- se o _link_ existir em múltiplos formatos, adicione um _link_ separado com uma observação sobre cada formato.
- se o material existe em diferentes lugares na Internet
    + use o _link_ com a fonte mais oficial (isso significa que o site do autor é melhor que o site da editora que é melhor que sites de terceiros)
    + se eles referenciam diferentes edições, e você julgar que essas edições são diferentes o bastante para mantê-las, adicione um _link_ separado com uma observação para cada edição (veja [Issue #2353](https://github.com/EbookFoundation/free-programming-books/issues/2353) para contribuir com a discussão sobre formatação).
- prefira _commits_ atômicos (um _commit_ para cada adição/deleção/modificação) ao invés de _commits_ maiores. Não é necessário fazer o _squash_ de seus _commits_ antes de submeter um PR. Nunca iremos impor esta regra dado que é apenas uma questão de conveniência para os mantenedores).
- se o livro for mais antigo, inclua a data de publicação no título.
- inclua o(s) nome(s) do(s) autor(es) onde for apropriado. Você pode encurtar a lista de autores com "et al".
- se o livro não estiver completo, e ainda está sendo escrito, adicione a notação "em processo", como descrito [abaixo.](#em_processo)
- se um endereço de email ou configuração de conta for solicitado antes que o _download_ seja habilitado, adicione uma observação no idioma apropriado e entre parênteses. Por exemplo: `(endereço de email é *pedido*, não obrigatório)`.

### Formatação
- Todas as listas são arquivos `.md`. Tente aprender a sintaxe de  [Markdown](https://guides.github.com/features/mastering-markdown/). É simples!
- Todas as listas começam com um Índice. A ideia é listar e "_linkar_" todas as seções e subseções lá. Mantenha-o em ordem alfabética.
- Seções são títulos de nível 3 (`###`), e subseções são títulos de nível 4 (`####`).

A ideia é ter:
- `2` linhas em branco entre o último _link_ e a nova seção.
- `1` linha em branco entre o título e o primeiro _link_ da seção.
- `0` linhas em branco entre dois _links_.
- `1` linha em branco ao final de cada arquivo `.md`.

Exemplo:

    [...]
    * [Um Livro Incrível](http://exemplo.com/exemplo.html)
                                    (linha em branco)
                                    (linha em branco)
    ### Exemplo
                                    (linha em branco)
    * [Outro Livro Incrível](http://exemplo.com/livro.html)
    * [Outro Livro Qualquer](http://exemplo.com/outro.html)

- Não coloque espaços entre `]` e `(`:

```
RUIM : * [Outro Livro Incrível] (http://exemplo.com/livro.html)
BOM  : * [Outro Livro Incrível](http://exemplo.com/livro.html)
```

- Se incluir o autor, use ` - ` (um traço envolto por espaços simples):

```
RUIM : * [Outro Livro Incrível](http://exemplo.com/livro.html)- Fulano de Tal
BOM  : * [Outro Livro Incrível](http://exemplo.com/livro.html) - Fulano de Tal
```

- Coloque um espaço simples entre o _link_ e seu formato:

```
RUIM : * [Um Livro Muito Incrível](https://exemplo.org/livro.pdf)(PDF)
BOM  : * [Um Livro Muito Incrível](https://exemplo.org/livro.pdf) (PDF)
```

- Autor vem antes do formato:

```
RUIM : * [Um Livro Muito Incrível](https://exemplo.org/livro.pdf)- (PDF) Fulana de Tal
BOM  : * [Um Livro Muito Incrível](https://exemplo.org/livro.pdf) - Fulana de Tal (PDF)
```

- Múltiplos formatos:

```
RUIM : * [Outro Livro Incrível](http://exemplo.com/)- Fulano de Tal (HTML)
RUIM : * [Outro Livro Incrível](https://downloads.exemplo.org/livro.html)- Fulano de Tal (download site)
BOM  : * [Outro Livro Incrível](http://exemplo.com/) - Fulano de Tal (HTML) [(PDF, EPUB)](https://downloads.exemplo.org/livro.html)
```

- Inclua o ano de publicação no título de livros antigos:

```
RUIM : * [Um Livro Muito Incrível](https://exemplo.org/livro.html) - Fulana de Tal - 1970
BOM  : * [Um Livro Muito Incrível (1970)](https://exemplo.org/livro.html) - Fulana de Tal
```

<a name="em_processo"></a>
- Livros em processo:

```
BOM  : * [Será Um Livro Incrível Em Breve](http://exemplo.com/livro2.html) - Fulano de Tal (HTML) (:construction: *em processo*)
```

### Observações

As noções básicas são relativamente simples, mas há uma grande diversidade de materiais que listamos. Aqui estão algumas observações sobre como tratamos essa diversidade.

#### Metadados

Nossas listas fornecem um conjunto mínimo de metadados: títulos, URLs, criadores, plataformas e notas de acesso.

##### Títulos

- Sem títulos inventados. Tentamos utilizar os títulos dos próprios materiais; contribuidores são aconselhados a não inventar títulos ou usá-los editorialmente se possível evitar. Uma exceção é para trabalhos antigos; se forem primariamente de interesse histórico, o ano entre parênteses adicionado ao título ajuda os usuários a saber se é de seu interesse.
- Sem título EM CAIXA ALTA. Normalmente "_title case_" é apropriado. Em caso de dúvida, use a capitalização da fonte.

##### URLs

- Não permitimos encurtadores de URLs.
- Códigos de rastreamento devem ser removidos da URL.
- URLs internacionais devem ser escapadas. Barras de endereço dos navegadores normalmente renderizam eles em Unicode, mas use copiar e colar, por favor.
- URLs seguras (https) sempre são preferidas no lugar de URLs não-seguras (http) quando https estiver disponível.
- Não gostamos de URLs que apontam para páginas que não hospedam o material listado, mas apontam para outro lugar.

##### Criadores

- Queremos creditar os criadores do material gratuito apropriadamente, incluindo tradutores!
- Para trabalhos traduzidos, o autor original deve ser creditado.
- Não permitimos _links_ para Criadores.
- Para compilações ou trabalhos remixados, o "criador" pode precisar de uma descrição. Por exemplo, os livros "GoalKicker" são creditados como "Compilado da documento do StackOverflow"

##### Plataforma e Notas de Acesso

- Cursos. Especificamente para nossa lista de cursos, a plataforma é uma parte importante da descrição do material. Isso acontece pois plataformas de cursos possuem _affordances_ e modelos de acesso diferentes. Normalmente não listamos um livro que requer um cadastro, muitas plataformas de cursos possuem _affordances_ que não funcionam sem algum tipo de conta. Exemplos de plataformas de cursos incluem Coursera, EdX, Udacity, e Udemy. Quando o curso depende da plataforma, o nome da plataforma deve ser listado em parênteses.
- YouTube. Temos muitos cursos que consistem em _playlists_ do YouTube. Não listamos YouTube como uma plataforma, tentamos listar o criador no YouTube, que normalmente é uma subplataforma.
- Vídeos do YouTube. Normalmente não usamos vídeos do YouTube individuais a não ser que tenham mais de uma hora e sejam estruturados como um curso ou tutorial.
- Leanpub. Leanpub hospeda livros com uma variedade de modelos de acesso. Algumas vezes, um livro pode ser lido sem necessidade de registro; algumas vezes um livro requer uma conta Leanpub para acesso gratuito. Dada a qualidade dos livros e a mistura e fluidez dos modelos de acesso do Leanpub, permitimos a listagem deste com uma observação de acesso *(Conta Leanpub ou email válido solicitado)*

#### Gêneros

A primeira regra ao decidir a qual lista um material pertence é ver como o próprio material se descreve. Se diz que é um livro, então talvez seja um livro.

##### Gêneros não listados

Dada a vastidão da Internet, não incluimos em nossas listas:

- blogs
- posts de blog
- artigos
- sites (exceto aquela que hospedam MUITOS dos items que listamos).
- vídeos que não são cursos ou screencasts.
- capítulos de livros.
- amostras de livros
- IRC ou canais do Telegram
- Slacks ou listas de email

Nossas listas de programação competitiva não são tão estritas quanto a essas exclusões. O escopo do repositório é determinado pela comunidade; se deseja sugerir uma mudança ou adição ao escopo, por favor use uma _issue_ para fazer a sugestão.


##### Livros vs. Outras Coisas

Não somos tão exigentes quanto a definição de "livro". Aqui estão alguns atributos que significam que um material é um livro:

- possui um ISBN (_International Standard Book Number_)
- possui um sumário
- uma versão baixável é oferecida, especialmente arquivos ePub
- possui edições
- não depende de conteúdo interativo ou vídeos
- tenta cobrir um tópico de forma abrangente
- é autocontido

Há diversos livros que listamos que não possuem esses atributos; pode depender do contexto.


##### Livros vs. Cursos

Algumas vezes pode ser difícil de distinguir!

Cursos normalmente possuem manuais associados, que listaríamos em nossas listas de livros. Cursos possuem aulas, exercícios, provas, anotações ou outros materiais didáticos. Uma única aula ou vídeo por si só não é um curso. Um Powerpoint não é um curso.


##### Tutoriais Interativos vs. Outras coisas

Se você pode capturar a tela ou imprimí-la e reter sua essência, então não é um Tutorial Interativo.


### Automação

- Aplicação das regras de formatação é automatizada via [GitHub Actions](https://github.com/features/actions) usando [fpb-lint](https://github.com/vhf/free-programming-books-lint) (veja [.github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- Validação de URL usa [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Para ativar a validação de URL, dê _push_ num _commit_ que inclua uma mensagem de _commit_ contendo `check_urls=file_to_check`:

```
check_urls=free-programming-books.md free-programming-books-pt_BR.md
```

- Você pode especificar mais de um arquivo para checagem, usando um espaço simples para separar cada entrada.
- Se você especificar mais de um arquivo, os resultados de _build_ serão baseados no resultado do último arquivo verificado. Você deve se atentar para o fato de que pode obter um _build_ com verde de sucesso devido a isso. Então, certifique-se de inspecionar o _build log_ ao final de cada _pull request_ clicando em "Show all checks" -> "Details".
