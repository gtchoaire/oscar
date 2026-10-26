# Visualizador MASBAL — estado do projeto

Este repositório contém um visualizador independente de resultados de balanço de massa MASBAL, desenvolvido em PySide6 e Matplotlib. A interface usa a linguagem visual do CANNES como preparação para uma integração futura, **mas ainda não é um módulo instalado no CANNES**. O projeto de referência foi fornecido no arquivo `ApplicationSoftware-main.zip`.

## Como executar

No Linux/WSL, a partir da raiz deste repositório:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

Sem argumento, abre a tela de seleção. Também é possível abrir diretamente um arquivo:

```bash
python3 main.py include/Tutorial.masbal.log
```

Para exportar uma imagem sem abrir a janela:

```bash
python3 main.py include/Tutorial.masbal.log --save painel.png --no-show
```

`python3 post.py` continua funcionando com os mesmos argumentos, como entrada de compatibilidade.

O seletor de arquivos aceita `.masbal.log`, `.log` e `.txt`. No WSL, unidades do Windows geralmente aparecem em `/mnt/c`, `/mnt/d` etc.; o seletor Qt não nativo foi escolhido para facilitar essa navegação. O arquivo precisa conter cabeçalho e colunas numéricas separadas por vírgula, com tempo na primeira coluna. O exemplo em `include/Tutorial.masbal.log` é um ponto de partida.

## O que está pronto

- Tela inicial com seleção de um resultado ou de múltiplos resultados; a visualização substitui o conteúdo **na mesma janela**.
- Resultado individual com quatro gráficos: evolução temporal, distribuição acumulada, composição atual e participação no total; seleção de séries, escala linear/logarítmica, animação temporal, avanço/recuo, início/fim, ampliação de um gráfico, retorno ao mosaico, redefinição e exportação de imagem.
- Aba “Distribuição acumulada” para comparar múltiplos arquivos, em grade de duas colunas, com legenda fixa durante a rolagem, escalas comuns, ampliação de um gráfico e ajuste de fontes.
- Filtros reutilizáveis na seleção e na comparação: óleo, tipo de tratamento, tratamento/intensidade, semestre, critério e busca por nome. Cada menu aceita várias opções: dentro da categoria vale **OU**; entre categorias vale **E**. Somente os resultados visíveis na seleção são carregados para comparação. Na tela de gráficos, filtros reordenam os cartões e recalculam uma escala comum para os visíveis; para incluir arquivos não carregados, é preciso voltar à seleção.
- Títulos legíveis derivados dos nomes das simulações, incluindo óleo, tratamento SSMD, semestre e critério AS/MM quando o arquivo segue o padrão reconhecido.
- Interface em português brasileiro, tempo com vírgula decimal e opções de aumento/redução da tipografia.
- Série de cores colorblind definida em `SERIES_CONFIG`; essas cores não seguem o tema CANNES de propósito, para preservar a distinção dos dados.
- Identidade visual inspirada no CANNES: grafite `#212B33`, verde `#2C423F`, azul-acinzentado `#3D505F`, cinzas `#C3C3C3`/`#E0E2DB` e laranja `#F98600`, com gradientes discretos em superfícies e botões.
- No resultado individual, a legenda usa retângulos coloridos à direita do gráfico acumulado quando há largura e altura suficientes. Em telas menores, volta à posição superior; os eixos do gráfico mantêm suas dimensões.

## Como funcionam os filtros

O nome reconhecido segue `<óleo>_<semestre 1|2>_<AS|MM>_<tratamento>.masbal.log`. Nomes fora desse padrão continuam utilizáveis e aparecem como “Não identificado” nas facetas que não puderem ser lidas. `45`, `50` e `55` são classificados como SSMD; `Untreated` e a grafia `Untrated`, como “Sem tratamento”. No conjunto de arquivos atual, `Corexit` e `Finasol` foram agrupados em **SSDI por convenção de nomenclatura**; confirme se isso corresponde à classificação científica desejada antes de usar esse grupo em análises finais. A regra pode ser alterada em `masbal/data.py`, na função `_treatment_name`.

“Limpar filtros” volta a mostrar todos os arquivos adicionados; “Limpar lista” remove os arquivos da seleção. Para testar as regras:

```bash
python3 -m unittest discover -s tests -v
```

## Onde alterar cada parte

`main.py` é a entrada principal; `post.py` apenas preserva o comando antigo. O restante está separado por responsabilidade:

| Necessidade | Local |
| --- | --- |
| Ordem, nomes e cores das séries; fontes; geometria | `masbal/config.py` |
| Cores, gradientes e tipografia dos widgets | `masbal/theme.py` |
| Leitura de tabelas e metadados dos arquivos | `masbal/data.py` |
| Facetas e lógica de filtros reutilizáveis | `masbal/filters.py` |
| Desenho dos gráficos individuais e comparativos | `masbal/charts.py` |
| Menu lateral, cabeçalho e player individual | `masbal/individual.py` |
| Grade e ações da comparação | `masbal/comparison.py` |
| Seleção de arquivos e troca de páginas | `masbal/launcher.py` |
| Inicialização e argumentos do terminal | `main.py` |

`A−`/`A+` ajustam as fontes do Qt e do Matplotlib. A largura dos setores não deve mudar drasticamente com esse ajuste. Os gráficos inferiores devem manter a ordem da configuração das séries; o mapa de participação mantém a barra de cores próxima ao lado direito. O eixo X temporal acompanha a evolução, enquanto a ordem das categorias no eixo Y permanece fixa.

## Trajetória resumida

1. Leitura de resultados MASBAL e criação dos quatro gráficos individuais.
2. Inclusão de seleção de séries, animação, marcador de tempo, botões de transporte, exportação e ampliação dos gráficos.
3. Migração dos menus para PySide6 e ajustes de tipografia, responsividade, alinhamento, legendas, rótulos e unidades em português brasileiro.
4. Criação da tela inicial para abrir arquivos na própria janela e da comparação de múltiplos resultados em matriz 2×2 por rolagem.
5. Padronização dos nomes das simulações e da paleta de séries para leitura colorblind; inclusão de zoom também na comparação.
6. Estudo do projeto CANNES enviado em ZIP; unificação da lateral individual em um menu com “Séries” e “Ajustes”, seguida da aplicação das cores, tonalidades e gradientes do CANNES ao restante da interface.
7. Inclusão condicional da legenda retangular à direita da distribuição acumulada, sem reduzir o gráfico.
8. Separação do antigo `post.py` em módulos e criação de filtros de simulação reutilizáveis nas duas etapas da comparação.

## Ponto atual e próximos passos

O visualizador continua autônomo. A integração com o CANNES é uma **etapa futura**. O ZIP de referência já possui aplicação PySide6, navegação própria e telas de balanço de massa individual e coletivo. O código agora está modularizado; o próximo passo da integração é definir como o CANNES fornecerá os caminhos/objetos de resultado ao módulo, evitando duplicar fluxos existentes. Também vale confirmar a classificação SSDI de Corexit/Finasol com o responsável pelos dados.

Não alterar as posições dos gráficos ou a ordem das séries apenas para acomodar mudanças de cor. Validar visualmente as três telas, a legenda nas larguras maior e menor, o zoom/retorno do mosaico, a barra de cores e a exportação antes de integrar.
