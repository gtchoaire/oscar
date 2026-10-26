# MASBAL — baseline visual da comparação

**Data:** 2026-10-26  
**Escopo:** interface comparativa e seus gráficos; sem mudanças nos dados científicos.

## Confirmado pelo usuário (captura de tela)

- A grade de **quatro colunas** foi aprovada visualmente na tela de distribuição acumulada.
- Cartões agrupados e centralizados como conjunto, em vez de espalhados por toda a janela.
- O formato de gráfico com `box_aspect` próximo de **0,46** foi aprovado.
- A paleta já escolhida deve ser mantida; não alterar cores, ordem das séries, cálculos, rótulos ou escalas por motivos estéticos.
- Tipografia solicitada para interface Qt, gráficos e exportações: **Times New Roman**.

## Localização dos parâmetros

| Responsabilidade | Módulo | Configuração |
|---|---|---|
| Quantidade de colunas, alturas e larguras Qt | `masbal/config.py` | `COMPARISON_GRID_COLUMNS` e constantes de geometria existentes |
| Distribuição e centralização dos cartões | `masbal/comparison.py` | `chart_grid` / `chart_row`; sem mudança no incremento 4.4 |
| Proporção dos eixos e margens do canvas Qt | `masbal/plot_style.py` | `COMPARISON_AXIS_BOX_ASPECT`, `COMPARISON_CANVAS_MARGINS` |
| Desenho das curvas e escalas MASBAL | `masbal/comparison_plot.py` | `draw_comparison_axis()` |
| Canvas dentro da tela Qt | `masbal/charts.py` | `ComparisonCanvas.redraw()` |
| Tipografia central | `masbal/typography.py` | `FONT_FAMILY`, `COMPARISON_TYPOGRAPHY` |
| Composição multipágina e dimensões da figura de relatório | `masbal/comparison_export.py` | independente da grade Qt |

## Contratos preservados pelo incremento 4.4

- A ferramenta de integração **lê os valores atuais do repositório**, em vez de restaurar números de uma versão antiga.
- Somente substitui os dois literais já existentes por nomes de constantes; o aspecto e as margens resultantes não mudam.
- As exportações continuam com a composição própria; **quatro colunas na interface não significam quatro colunas em cada página exportada**.
- Não modifica `comparison.py`, `comparison_export.py`, dados, limites, valores ou mapa de cores.

## Validação pendente

1. Confirmar visualmente os mesmos cenários depois da centralização das constantes.
2. Testar **Ampliar → Reduzir**, filtros, e controles de zoom tipográfico A−/A+.
3. Verificar exportação comparativa em PNG 300 dpi, PDF multipágina, SVG e EPS e a exportação individual.
4. Verificar Times New Roman efetivamente disponível no sistema (`fc-match`) e para Matplotlib (`installed_plot_font()`).
5. Verificar interface em janela menor; com cartões de largura fixa, a grade pode exigir rolagem horizontal. Layout responsivo é um **incremento futuro**, não parte desta consolidação.

**Status:** baseline visual aprovado por imagem; consolidação do código e testes dependem da execução no repositório do usuário.
