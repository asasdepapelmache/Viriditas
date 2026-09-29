<h1 align="center">Viriditas</h1>

<p align="center">
  <em>Preenche o gráfico de contribuições do GitHub com commits retroativos — de 1969 até hoje.</em>
</p>

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="Sem dependências" src="https://img.shields.io/badge/depend%C3%AAncias-nenhuma-success">
  <img alt="Licença: MIT" src="https://img.shields.io/badge/licen%C3%A7a-MIT-green">
  <img alt="Plataformas" src="https://img.shields.io/badge/plataforma-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey">
</p>

<p align="center"><a href="README.md">🇬🇧 Read in English</a></p>

---

```
Range:    1969-12-31 to 2026-09-29  (offset -0300)
Days:     20,727
Commits:  113,495
Done in 5.2s

     J    F   M   A   M    J   J   A    S   O    N   D
Sun   ░▒░░░▒░▒▒░░▒░▒░▒▒▒▒░▒░▒░▒▒░▒░▒▒░▒▒░▒░░▒▒░▒░▒▒░▒░░░░░
Mon   ▒▒▒▒▒▒░▓▒░▓▒▒▓▒▓▒░▒▒░▒▒▒▒▒▒▒░▒▒▒▒▒░▒▒▒▒▒▒▒░▒▒▒▒▒▓░▒░
Tue   ▒▒▒░▒▒▒▓▒▒▒▒▒░░▒░▒░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░▒▒▒▒▒▒▒▒▒▒░▓▒░░░
Wed   ▒▒░▒▒▒░▒▓▒▒▓▒░░▒░░▒▒░▒▒▒▒░▒░▒▒░▒░▒▒░▒░░░▓░▒▒░░░▒▒▒░▒
Thu  ▒░▒▒▒▒▒▒▒░▒▒▓░▒▒▒▒░░▒░▒▒▒░▒▒░▒▒▒░▒▒▒▒▒▒▒▒▒▒▒▒░▒▒░▒▒▒▒
Fri  ▓▒▒▒▒░░▒▒▒▒▒░░░▒▒▒▒▒░▒▒░▒▓▓▒░▒▒░▒░▒▒▒▒▒░▒▒▒▒▒░▒▒▒▒▒░
Sat  ░▒▒░░▒▒▒░░▒░▒▒▒░▒░▒▒░▒▒░░░▒░░▒░░░░░▒░░░░▒▒▒▒░▒░░░▒▒░
     less ·░▒▓█ more
```

> A interface e as mensagens da ferramenta são em inglês. Este documento é a
> tradução do README.

## O que faz

O Viriditas gera um repositório Git cujo histórico se espalha por todos os dias
de um intervalo que você escolhe — por padrão de **1969-12-31** até hoje, cerca
de 2.000 commits por ano — e publica como repositório privado, deixando seu
gráfico de contribuições inteiramente preenchido.

É um brinquedo estético. Não falsifica code review, pull request, nem nada que
alguém possa confundir com trabalho real. O repositório gerado diz o que é no
próprio README, e um único comando desfaz tudo.

**Por que é rápido:** o histórico é escrito via `git fast-import`, não num laço
de `git commit`. Cerca de 113.000 commits levam por volta de **5 segundos** e
produzem um pack de 41 MB. O mesmo trabalho com `git commit` levaria horas.

## Recursos

| | |
|---|---|
| 🗓️ **Alcança 1969** | O dia mais antigo que o Git consegue expressar, via fuso negativo. Veja [o truque do 1969](#o-truque-do-1969). |
| 🎲 **Determinístico** | A mesma seed sempre produz o mesmo gráfico. Troque a seed, mude a textura. |
| 📊 **Heatmap no terminal** | Pré-visualize qualquer ano numa grade estilo GitHub antes de escrever nada. |
| 🧮 **Densidade modelável** | Alvo anual com folga de 5%, piso e teto por dia, fins de semana mais leves. |
| 🔍 **Dry run** | `plan` não escreve nada, e `--json` deixa o cronograma legível por máquina. |
| 🙈 **Esconder** | `undo --hide` tira o gráfico do perfil sem apagar absolutamente nada. |
| 🧹 **Limpar** | `clean` remove o build local; `undo --delete` remove o remoto também, com confirmação digitada. |
| ♻️ **Completar** | `topup` preenche os dias que passaram desde a última execução. |
| 🛡️ **Salvaguardas** | Recusa destino não vazio, recusa forks, e só toca no repositório declarado no seu config. |
| 📦 **Zero dependências** | Só biblioteca padrão, em Linux, macOS e Windows. |

## Requisitos

- **Python 3.11+** (usa `tomllib`, da biblioteca padrão)
- **git**
- **[GitHub CLI](https://cli.github.com)** (`gh`), autenticado

```sh
gh auth login
```

O Viriditas nunca lê, grava ou guarda token: toda chamada de API é delegada ao
`gh`.

## Instalação

```sh
git clone https://github.com/<você>/Viriditas.git
cd Viriditas
python -m viriditas --help
```

Ou instale para ter o comando no PATH:

```sh
pip install .
viriditas --help
```

## Começando

```sh
viriditas init      # escreve o viriditas.toml
viriditas check     # confere git, gh, login e config
viriditas plan      # dry run: totais, estimativa, heatmap
viriditas run       # generate + push, com confirmação
```

Depois, **se o repositório for privado**, ative as contribuições privadas — não
existe API para isso, então a ferramenta só consegue lembrar você:

1. Abra <https://github.com/settings/profile>
2. Em **Contributions**, marque **"Include private contributions on my profile"**

A indexação é assíncrona e leva alguns minutos. O gráfico aparece vazio até ela
terminar; isso é normal. **Não faça outro push enquanto espera** — veja abaixo.

## Comandos

| Comando | O que faz |
|---|---|
| `viriditas init` | Escreve um `viriditas.toml` inicial (`--force` sobrescreve) |
| `viriditas check` | Confere Python, `git`, `gh`, autenticação e o config |
| `viriditas plan` | Dry run: totais por ano, estimativa de tempo, heatmap ASCII (`--year 1987`, `--json`) |
| `viriditas generate` | Monta o repositório local via `git fast-import` (`--force` refaz) |
| `viriditas push` | Cria o repositório e faz push (recusa destino não vazio) |
| `viriditas run` | `check` → `plan` → confirmação → `generate` → `push` |
| `viriditas status` | Estado local e remoto, mais os lembretes que se aplicam |
| `viriditas topup` | Gera e envia só os dias que faltam desde o último commit |
| `viriditas clean` | Apaga a pasta de build local; o remoto não é tocado |
| `viriditas undo --hide` | Mostra como desaparecer do gráfico sem apagar nada |
| `viriditas undo --delete` | Apaga o repositório remoto e a pasta local, com confirmação digitada |

Todos aceitam `--config caminho/para/viriditas.toml`.

## Configuração

```toml
[github]
repo_name = "contribution-canvas"  # PRECISA estar vazio ou não existir ainda
private = true
name = "auto"                      # "auto" = a conta autenticada
email = "auto"                      # "auto" = o endereço noreply dessa conta

[range]
start = "1969-12-31"
end = "today"

[density]
target_per_year = 2000   # commits por ano completo, com folga de 5%
min_per_day = 1          # todo dia recebe pelo menos isso
max_per_day = 14
weekend_factor = 0.75    # fins de semana um pouco mais leves
seed = 42                # mesma seed, mesmo gráfico, sempre
timezone = "-0300"       # fuso gravado em cada commit

[commit]
messages = ["update", "tweak", "sync", "wip", "chore", "fix", "notes"]
file = "activity.log"    # o único arquivo que cada commit reescreve
add_readme = true        # explica o repositório no README dele mesmo

[local]
workdir = "./build/contribution-canvas"
```

`workdir` precisa ser um caminho nativo. No Windows use `./build/...` ou
`C:/...`; caminho estilo MSYS como `/c/Users/...` não resolve.

## ⚠️ O repositório de destino precisa estar vazio

Esta é a única coisa que arruína o resultado em silêncio, e o GitHub não
documenta em lugar nenhum.

**O GitHub só indexa o histórico inteiro no primeiro push de um repositório
recém-criado.** Push por cima de histórico existente é indexado parcialmente, ou
nem é — mesmo com `--force`, mesmo o push dando sucesso e todos os commits
estando comprovadamente no remoto.

Medido em seis execuções, lendo o gráfico de volta pela API GraphQL:

| Commits enviados | Estado do repositório | Contados no gráfico |
|---|---|---|
| 5 | primeiro push, repo novo | **5** ✅ |
| 1.500 | primeiro push, repo novo | **1.500** ✅ |
| 113.495 | primeiro push, repo novo | **113.495** ✅ |
| 1.500 (em 3 pushes de 500) | histórico existente | 500 |
| 20.000 (um push) | histórico existente | 0 |
| 113.495 (`--force`) | histórico existente (23 commits) | 1.000 |

O que decorre disso:

- **O volume não é o limite.** 113.495 commits num único push contaram todos, e o
  push levou 8,5 segundos.
- **Pushar em lotes piora.** Três pushes de 500 contaram 500, não 1.500. Só o
  primeiro entrou. Por isso o Viriditas faz um push só e nunca divide.
- **A indexação atrasa minutos.** Cerca de seis nos testes. Zero no gráfico logo
  depois do push significa "ainda não", não "falhou". Republicar te joga no
  caminho que não é confiável.
- **Então o `push` recusa destino não vazio.** O `--force` ignora a checagem e
  avisa, mas o gráfico provavelmente vai ficar incompleto.

Se você já empurrou para um repositório sujo, aponte o `repo_name` para um novo —
ou apague e recrie — e envie de novo como o primeiro push dele.

## Como o GitHub conta contribuições

O Viriditas respeita todas estas regras, e o `check`/`status` mostram as que ele
não consegue impor:

- O commit precisa estar na **branch padrão** do repositório (`main`).
- O e-mail do autor precisa estar **vinculado à conta**. Com `email = "auto"` a
  ferramenta usa `<id>+<login>@users.noreply.github.com`, lido de
  `gh api user`, que sempre está.
- O repositório **não pode ser fork**. O `push` recusa forks de saída.
- Repositório privado exige **"Include private contributions on my profile"**.
- O dia em que o commit cai é calculado pelo **fuso gravado no próprio commit**,
  não por UTC.

## O truque do 1969

O Git guarda datas como timestamp Unix, então `1970-01-01 00:00 UTC` é o piso.
Para aparecer **1969** no gráfico, grava-se um commit logo depois da época com
fuso negativo: o instante é pós-época, mas a data *local* do commit é 1969-12-31.

| timestamp | fuso | data local do commit |
|---|---|---|
| `3600` | `-0300` | `1969-12-31 22:00:00` |

O `git fast-import --date-format=raw` aceita isso sem reclamar. O objeto grava
literalmente `author ... 3600 -0300`, o `git fsck` passa limpo e o `git clone`
transfere normalmente. O timestamp `0` é evitado de propósito — algumas
ferramentas leem como "sem data" — então o piso usado é `1`.

Com fuso `-0300`, o dia 1969-12-31 só existe entre os timestamps `1` e `10799`,
ou seja das 21:00 às 23:59 no horário local. A função `day_window()` corta a
janela de cada dia nesse piso automaticamente, e é por isso que perfis desse tipo
mostram 1969 com um único dia.

### Efeito colateral: o `git log` local não formata essa data

Qualquer `git log` que *formate* a data aborta nesse commit:

```console
$ git log -1 --date=iso
fatal: Timestamp before Unix epoch: 3600 -300
```

É limitação apenas do renderizador local do `git` — não do objeto, e não do
GitHub. Para inspecionar, use `--date=raw`:

```sh
git log --reverse --date=raw --format='%ad %s' | head -3
```

O Viriditas faz exatamente isso internamente (`generator.raw_bounds`) e converte
para data legível em Python (`generator.raw_to_display`).

## Como desfazer

Dois caminhos, do mais leve ao definitivo:

```sh
viriditas undo --hide     # não muda nada; ensina a sumir do gráfico
viriditas clean           # apaga só o build local
viriditas undo --delete   # apaga o repositório remoto e a pasta local
```

- **`--hide`** não toca em nada. Imprime como desmarcar *"Include private
  contributions on my profile"*, o que devolve o gráfico à atividade pública e é
  reversível quando você quiser.
- **`--delete`** é permanente. Exige o escopo `delete_repo`
  (`gh auth refresh -h github.com -s delete_repo`), mostra o repositório e a
  contagem de commits, e só prossegue quando você **digita o nome do
  repositório**. Salvaguarda: só apaga o repositório declarado no seu config.

## Estrutura

```
viriditas/
  cli.py          # argparse, comandos, saída
  config.py       # carrega e valida o TOML
  schedule.py     # quantos commits por dia (determinístico, puro)
  preview.py      # heatmap ASCII com fallback para terminal legado
  generator.py    # o stream do fast-import e o repositório local
  publisher.py    # cria o repositório e faz push
  undo.py         # esconder, limpar, apagar
  github.py       # wrappers finos sobre git e gh
tests/
  test_schedule.py
```

## Testes

```sh
python tests/test_schedule.py    # não precisa de pytest
python -m pytest                 # se você tiver
```

Cobrem determinismo por seed, piso e teto por dia, totais anuais com folga de 5%,
ano bissexto e não bissexto, nenhum dia faltando, ano parcial proporcional, fins
de semana mais leves, independência do ano em relação ao intervalo, os caminhos
de rejeição do config, geometria do heatmap e o fallback de terminal legado, além
da aritmética de timestamp — incluindo a janela do 1969 e a garantia de que todo
timestamp gerado cai no dia a que se destina.

## Perguntas frequentes

**Isso me dá ban?**
Nada aqui viola os Termos de Serviço do GitHub: são commits comuns, no seu
próprio repositório, com você como autor. É estético, e quem abrir o repositório
vê imediatamente o que é. Não apresente como trabalho real.

**As pessoas vão ver o repositório?**
Não, se ele for privado. O gráfico mostra a *contagem*, e contribuição privada
aparece como quadradinho preenchido sem link. Deixar público colocaria um
repositório de 113.000 commits sem sentido no seu perfil — o `private = true` é
padrão por um motivo.

**Posso mudar o formato?**
Mude `seed` para outra textura, `target_per_year` para a intensidade geral,
`min_per_day` / `max_per_day` para o contraste, e `weekend_factor` para o ritmo
semanal. Rode `viriditas plan --year <ano>` para ver antes de gerar.

**Por que esse nome?**
*Viriditas* é a palavra de Hildegard von Bingen para a força de verdejar das
coisas vivas. Pareceu certo para uma ferramenta cuja saída inteira é
quadradinhos verdes.

## Licença

MIT — veja o [LICENSE](LICENSE).
