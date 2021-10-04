*Lisez ceci dans d'autres langues: [English](CONTRIBUTING.md), [Español](CONTRIBUTING-es.md), [简体中文](CONTRIBUTING-zh.md), [繁體中文](CONTRIBUTING-zh_TW.md), [فارسی](CONTRIBUTING-fa_IR.md), [Tiếng Việt](CONTRIBUTING-vn.md), [Русский](CONTRIBUTING-ru.md).*

## Contrat de Licence des Contributeurs
En contribuant, vous acceptez la [LICENCE](https://github.com/ElivreFoundation/free-programming-livres/blob/master/LICENSE) de ce repositoire.

## Code de conduite des contributeurs
En contribuant, vous acceptez de respecter le [Code de Contrat](https://github.com/ElivreFoundation/free-programming-livres/blob/master/CODE_OF_CONDUCT.md) de ce repositoire.

## En bref

1. "Un lien pour télécharger facilement un livre" n'est pas toujours un lien vers un livre *gratuit*. Merci de ne contribuer qu'à du contenu gratuit. Assurez-vous que c'est gratuit. Nous n'acceptons pas les liens vers des pages qui *nécessitent* des adresses e-mail valides pour obtenir des livres, mais nous accueillons les annonces qui en font la demande.

2. Vous n'êtes pas obligé de connaître Git : si vous avez trouvé quelque chose d'intéressant qui n'est *pas déjà dans ce repositoire*, veuillez ouvrir un [Problème](https://github.com/ElivreFoundation/free-programming-livres/issues) avec vos propositions de liens.
    - Si vous savez Git, Forkez le repo et envoyez vos pull requests.
3. Nous avons 5 types de listes. Choisissez le bon:

    - *Livres* : PDF, HTML, ePub, un site basé sur gitlivre.io, un repositoire Git, etc.
    - *Cours* : Un cours est un matériel d'apprentissage qui n'est pas un livre. [Ceci est un cours](http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/6-006-introduction-to-algorithms-fall-2011/).
    - *Tutoriels interactifs* : Un site Web interactif qui permet à l'utilisateur de saisir du code ou des commandes et d'évaluer le résultat (par "évaluer" nous ne voulons pas dire "noter"). par exemple : [Essayez Haskell](http://tryhaskell.org), [Essayez Github](http://try.github.io).
    - *Podcasts et Screencasts* : Podcasts et screencasts.
    - *Ensembles de Problèmes et Programmation Compétitive* : Un site Web ou un logiciel qui vous permet d'évaluer vos compétences en programmation en résolvant des problèmes simples ou complexes, avec ou sans revue de code, avec ou sans comparaison des résultats avec d'autres utilisateurs.

4. Assurez-vous de suivre les [directives ci-dessous](#directrices) et de respecter [la format Markdown](#formatage) des fichers.

5. Github Actions exécutera des tests pour s'assurer que vos listes sont classées par ordre alphabétique et que les règles de formatage sont respectées. Assurez-vous de vérifier que vos modifications passent les tests.

### Directrices
- assurez-vous qu'un livre est gratuit. Vérifiez si nécessaire. Cela aide les administrateurs si vous commentez dans le PR pourquoi vous pensez que le livre est gratuit.
- nous n'acceptons pas les fichiers hébergés sur google drive, dropbox, mega, scribd, issuu et autres plateformes de téléchargement de fichiers similaires.
- insérez vos liens par ordre alphabétique. Si vous voyez un lien égaré, veuillez le réorganiser et soumettre un PR
- utiliser le lien avec la source la plus autoritaire (c'est-à-dire que le site de l'auteur est meilleur que le site de l'éditeur, qui est meilleur qu'un site tiers)
    + pas de services d'hébergement de fichiers (cela inclut (mais n'est pas limité à) les liens Dropbox et Google Drive)
- préférez toujours un lien `https` à un `http` - tant qu'ils sont sur le même domaine et servent le même contenu
- sur les domaines root, supprimez la barre oblique finale: `http://exemple.com` au lieu de `http://exemple.com/`
- préférez toujours le lien le plus court : `http://exemple.com/dir/` est préférable à `http://exemple.com/dir/index.html`
    + pas de liens de raccourcissement d'URL
- préférez généralement le lien "actuel" à celui de "version": `http://exemple.com/dir/livre/current/` est meilleur que `http://exemple.com/dir/livre/v1.0.0 /index.html`
- si un lien a un certificat expiré/certificat auto-signé/problème SSL de toute autre nature:
  1. *remplacez-le* par son équivalent `http` si possible (car accepter les exceptions peut être compliqué sur les appareils mobiles)
  2. *laissez-le* si aucune version `http` n'est disponible mais que le lien est toujours accessible via `https` en ajoutant une exception au navigateur ou en ignorant l'avertissement.
  3. *supprimez-le* sinon.
- si un lien existe dans plusieurs formats, ajoutez un lien séparé avec une note sur chaque format
- si une ressource existe à différents endroits sur Internet
    + utiliser le lien avec la source la plus autoritaire (c'est-à-dire que le site de l'auteur est meilleur que le site de l'éditeur, qui est meilleur qu'un site tiers)
    + s'ils renvoient à des éditions différentes et que vous jugez que ces éditions sont suffisamment différentes pour qu'elles valent la peine d'être conservées, ajoutez un lien séparé avec une note sur chaque édition (voir [Problème #2353](https://github.com/ElivreFoundation/free-programming-livres/issues/2353) pour contribuer à la discussion sur le formatage.))
- préférer les commits atomiques (un commit par ajout/suppression/modification) aux plus gros commits. Pas besoin d'écraser vos commits avant de soumettre un PR. (Nous n'appliquerons jamais cette règle car c'est juste une question de commodité pour les responsables)
- si le livre est plus ancien, indiquez la date de parution avec le titre.
- incluez le ou les noms de l'auteur, le cas échéant. Vous pouvez raccourcir les listes d'auteurs avec "et al."
- si le livre n'est pas terminé, et est toujours en cours de travail, ajoutez la notation "en cours", comme décrit [ci-dessous.](#in_process)
- si une adresse e-mail ou la configuration d'un compte est demandée avant l'activation du téléchargement, ajoutez des notes adaptées à la langue entre parenthèses, par exemple: `(adresse e-mail *demandée*, non obligatoire)`

### Formatage
- Toutes les listes sont des fichiers `.md`. Essayez d'apprendre la syntaxe [Markdown](https://guides.github.com/features/mastering-markdown/). C'est simple!
- Toutes les listes commencent par un Index. L'idée est d'y lister et de lier toutes les sections et sous-sections. Gardez-le par ordre alphabétique.
- Les sections utilisent des titres de niveau 3 (`###`) et les sous-sections sont des titres de niveau 4 (`####`).

l'idée est d'avoir:
- `2` lignes vides entre le dernier lien et la nouvelle section
- `1` ligne vide entre le titre et le premier lien de sa section
- `0` ligne vide entre deux liens
- `1` ligne vide à la fin de chaque fichier `.md`

Exemple:

    [...]
    * [Un Livre Génial](http://exemple.com/exemple.html)
                                    (ligne blanche)
                                    (ligne blanche)
    ### Exemple
                                    (ligne blanche)
    * [Un Autre Livre Génial](http://exemple.com/livre.html)
    * [Un Autre Livre](http://exemple.com/autre.html)

- Mettez pas des espaces entre `]` et `(`:

```
MAUVAIS : * [Un Autre Livre Génial] (http://exemple.com/livre.html)
BIEN    : * [Un Autre Livre Génial](http://exemple.com/livre.html)
```

- Si vous incluez l'auteur, utilisez ` - ` (un tiret entouré d'un espaces):

```
MAUVAIS : * [Un Autre Livre Génial](http://exemple.com/livre.html)- John Doe
BIEN    : * [Un Autre Livre Génial](http://exemple.com/livre.html) - John Doe
```

- Mettez un seul espace entre le lien et son format:

```
MAUVAIS : * [Un Autre Livre Génial](https://exemple.org/livre.pdf)(PDF)
BIEN    : * [Un Autre Livre Génial](https://exemple.org/livre.pdf) (PDF)
```

- L'auteur vient avant le format:

```
MAUVAIS : * [Un Autre Livre Génial](https://exemple.org/livre.pdf)- (PDF) Jane Roe
BIEN    : * [Un Autre Livre Génial](https://exemple.org/livre.pdf) - Jane Roe (PDF)
```

- Formats multiples:

```
MAUVAIS : * [Un Autre Livre Génial](http://exemple.com/)- John Doe (HTML)
MAUVAIS : * [Un Autre Livre Génial](https://downloads.exemple.org/livre.html)- John Doe (site de téléchargement)
BIEN    : * [Un Autre Livre Génial](http://exemple.com/) - John Doe (HTML) [(PDF, EPUB)](https://downloads.exemple.org/livre.html)
```

- Inclure l'année de publication dans le titre pour les livres plus anciens :

```
MAUVAIS : * [Un Autre Livre Génial](https://exemple.org/livre.html) - Jane Roe - 1970
BIEN    : * [Un Autre Livre Génial (1970)](https://exemple.org/livre.html) - Jane Roe
```

<a name="in_process"></a>
- Livres en cours :

```
BIEN    : * [Sera bientôt un livre génial](http://exemple.com/livre2.html) - John Doe (HTML) (:construction: *in process*)
```

### Remarques

Bien que les bases soient relativement simples, il existe une grande diversité dans les ressources que nous répertorions. Voici quelques notes sur la façon dont nous gérons cette diversité.

#### Métadonnées

Nos listes fournissent un ensemble minimal de métadonnées : titres, URL, créateurs, plateformes et notes d'accès.

##### Titres

- Pas de titres inventés. Nous essayons de prendre les titres des ressources elles-mêmes ; les contributeurs sont avertis de ne pas inventer de titres ou de ne pas les utiliser éditorialement si cela peut être évité. Une exception est pour les œuvres plus anciennes; s'ils présentent principalement un intérêt historique, une année entre parenthèses ajoutée au titre aide les utilisateurs à savoir s'ils présentent un intérêt.
- Pas de titres TOUTES EN MAJUSCULES. Habituellement, la casse du titre est appropriée, mais en cas de doute, utilisez la majuscule de la source

##### URLs

- Nous n'autorisons pas les URL raccourcies.
- Les codes de suivi doivent être supprimés de l'URL.
- Les URL internationales doivent être échappées. Les barres du navigateur les rendent généralement en Unicode, mais utilisez le copier-coller, s'il vous plaît.
- Les URL sécurisées (https) sont toujours préférées aux URL non sécurisées (http) où https a été implémenté.
- Nous n'aimons pas les URL qui pointent vers des pages Web qui n'hébergent pas la ressource répertoriée, mais pointent plutôt ailleurs.

##### Créateurs

- Nous voulons créditer les créateurs de ressources gratuites le cas échéant, y compris les traducteurs !
- Pour les œuvres traduites, l'auteur original doit être crédité.
- Nous n'autorisons pas les liens pour les créateurs.
- Pour les compilations ou les travaux remixés, le "créateur" peut avoir besoin d'une description. Par exemple, les livres "GoalKicker" sont crédités comme "Compilé à partir de la documentation StackOverflow"

##### Plateformes et notes d'accès

- Cours. Surtout pour nos listes de cours, la plateforme est une partie importante de la description de la ressource. En effet, les plates-formes de cours ont des options et des modèles d'accès différents. Bien que nous ne répertoriions généralement pas un livre nécessitant une inscription, de nombreuses plateformes de cours ont des options qui ne fonctionnent pas sans une sorte de compte. Des exemples de plates-formes de cours incluent Coursera, EdX, Udacity et Udemy. Lorsqu'un cours dépend d'une plateforme, le nom de la plate-forme doit être indiqué entre parenthèses.
- Youtube. Nous avons de nombreux cours qui se composent de listes de lecture YouTube. Nous ne répertorions pas Youtube comme plateforme, nous essayons de répertorier le créateur Youtube, qui est souvent une sous-plateforme.
- Vidéos youtube. Nous ne créons généralement pas de liens vers des vidéos YouTube individuelles, sauf si elles durent plus d'une heure et sont structurées comme un cours ou un didacticiel.
- Leanpub. Leanpub héberge des livres avec une variété de modèles d'accès. Parfois, un livre peut être lu sans inscription ; parfois un livre nécessite un compte Leanpub pour un accès gratuit. Compte tenu de la qualité des livres et du mélange et de la fluidité des modèles d'accès Leanpub, nous autorisons l'inscription de ces derniers avec la note d'accès *(compte Leanpub ou email valide demandé)*

#### Genres

La première règle pour décider à quelle liste appartient une ressource est de voir comment la ressource se décrit. S'il s'appelle un livre, alors c'est peut-être un livre.

##### Genres que nous ne listons pas

Parce qu'Internet est vaste, nous n'incluons pas dans nos listes:

- les blogs
- articles de blog
- des articles
- des sites Web (à l'exception de ceux qui hébergent BEAUCOUP d'articles que nous répertorions.)
- des vidéos qui ne sont pas des cours ou des screencasts.
- les chapitres du livre
- échantillons teaser de livres
- Canaux IRC ou Telegram
- Slacks ou listes de diffusion

Nos listes de programmation compétitive ne sont pas aussi strictes sur ces exclusions. La portée du repo est déterminée par la communauté ; si vous souhaitez suggérer un changement ou un ajout à la portée, veuillez utiliser un issue pour faire la suggestion.

##### Livres vs. autres choses

Nous ne sommes pas si pointilleux sur la livreté. Voici quelques attributs qui signifient qu'une ressource est un livre :

- il a un ISBN (International Standard Book Number)
- il a une table des matières
- une version téléchargée, notamment ePub, est proposée
- il a des éditions
- cela ne dépend pas du contenu interactif ou des vidéos
- il essaie de couvrir un sujet de manière exhaustive
- il est autonome

Il y a beaucoup de livres que nous listons qui n'ont pas ces attributs ; cela peut dépendre du contexte.


##### Livres vs. cours

Parfois, ceux-ci peuvent être difficiles à distinguer!

Les cours ont souvent des livres de texte associés, que nous énumérerions dans nos listes de livres. Les cours comportent des exposés, des exercices, des tests, des notes ou d'autres supports didactiques. Une seule conférence ou vidéo en soi n'est pas un cours. Un powerpoint n'est pas un cours.


##### Tutoriels interactifs vs. autres trucs

Si vous pouvez l'imprimer et conserver son essence, ce n'est pas un didacticiel interactif.


### Automatisation

- L'application des règles de formatage est automatisée via [Github Actions](https://docs.github.com/en/actions) en utilisant [fpb-lint](https://github.com/vhf/free-programming-livres-lint) (voir [ .github/workflows/fpb-lint.yml](.github/workflows/fpb-lint.yml))
- La validation d'URL utilise [awesome_bot](https://github.com/dkhamsing/awesome_bot)
- Pour déclencher la validation d'URL, poussez un commit qui inclut un message de commit contenant `check_urls=file_to_check` :

```
check_urls=free-programming-livres.md free-programming-livres-en.md
```

- Vous pouvez spécifier plus d'un fichier à vérifier, en utilisant un seul espace pour séparer chaque entrée
- Si vous spécifiez plus d'un fichier, les résultats de la construction sont basés sur le résultat du dernier fichier vérifié. Vous devez savoir que vous pouvez obtenir des versions vertes de réussite à cause de cela, alors assurez-vous d'inspecter le journal de construction à la fin de la demande d'extraction en cliquant sur "Show all checks" -> "Details".
