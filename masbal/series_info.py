"""Documentação interpretativa das categorias MASBAL exibida na interface.

Referência: MEMW User's Manual v15.2. A tabela da seção 5.5 descreve
um output .DTO com oito categorias; os arquivos .masbal.log analisados
contêm onze. A equivalência detalhada entre formatos não está documentada.
"""

from html import escape

from .config import SERIES_CONFIG

# (Significado, interpretação/ressalva, referência no manual MEMW v15.2)
SERIES_INFO: dict[str, tuple[str, str, str]] = {
    "surface": (
        "Massa de óleo indicada pelo OSCAR como presente na superfície do mar, "
        "sujeita a deslocamento, espalhamento e processos de intemperismo.",
        "Não equivale à área coberta ou à espessura da mancha; também não se "
        "deve interpretar automaticamente como massa total de emulsão incluindo água.",
        "§§ 5.5 e 22.4.3 (pp. 59 e 209).",
    ),
    "stranded": (
        "Massa associada ao óleo retido ou depositado na costa após interação "
        "da mancha com os segmentos de litoral.",
        "Não indica, por si só, retenção permanente: o OSCAR também representa "
        "remoção natural da costa (wash-off), influenciada pelo tipo de litoral.",
        "§ 22.4.11 (p. 213).",
    ),
    "droplet": (
        "Massa identificada no MASBAL como gotículas de óleo na coluna d'água, "
        "distinta da fração dissolvida.",
        "As gotículas podem ser formadas por dispersão/entranhamento ou por "
        "liberação submersa e estão sujeitas a transporte e ressurgência. A categoria "
        "'Submerged' do arquivo .DTO é mais genérica; o manual não confirma "
        "equivalência numérica direta com 'droplet'.",
        "§§ 1.2.3, 5.5 e 22.4.5 (pp. 6, 59 e 210).",
    ),
    "atmos-evap": (
        "Massa indicada como transferida para a atmosfera por evaporação de "
        "componentes do óleo.",
        "Evaporação depende das propriedades e da composição dos componentes; "
        "não deve ser confundida com gás liberado na atmosfera (atmos-gas).",
        "§ 22.4.4 (pp. 209–210).",
    ),
    "decayed": (
        "Massa classificada pelo arquivo como biodegradada ou transformada "
        "pelos processos de biodegradação modelados.",
        "Ressalva importante: o manual esclarece que, para os pseudocomponentes "
        "padrão do OSCAR, as taxas representam a transformação inicial, "
        "NÃO necessariamente a mineralização completa em CO₂. Portanto, "
        "'decayed' não significa automaticamente substância eliminada sem resíduos.",
        "§ 22.4.10 (p. 212).",
    ),
    "dissolved": (
        "Massa reportada como dissolvida na coluna d'água, ou seja, "
        "componentes transferidos da fase líquida/óleo para a água.",
        "Diferencia-se de 'droplet', que representa gotículas. Embora o "
        "Gastrack também modele dissolução de gás, o manual não especifica "
        "se nem como gás dissolvido é agregado a esta coluna particular do MASBAL.",
        "§§ 16.2.1 e 22.4.9 (pp. 159–161 e 211–212).",
    ),
    "atmos-gas": (
        "Massa reportada como gás que alcançou a atmosfera, associada ao "
        "tratamento de liberações gasosas pelo Gastrack.",
        "É distinta de 'atmos-evap' (evaporação de óleo). O manual documenta "
        "gás liberado na atmosfera nos logs de balanço de massa do Gastrack, "
        "mas não detalha a correspondência exata desta coluna em .masbal.log.",
        "§§ 16.1 e 16.3 (pp. 157 e 162–163).",
    ),
    "gasbubbles": (
        "Massa identificada como bolhas de gás na coluna d'água, transportadas "
        "e sujeitas a subida e dissolução.",
        "A modelagem explícita das bolhas depende do recurso Gastrack e de "
        "sua ativação/licença. Uma série zerada não prova erro de simulação "
        "nem permite concluir, isoladamente, que não houve gás na liberação.",
        "§§ 16.1–16.3 (pp. 157–163).",
    ),
    "sediment": (
        "Massa reportada como associada ao sedimento/fundo marinho, "
        "incluindo processos que levam componentes do óleo ao leito.",
        "A interpretação depende do tipo de execução. Nas simulações "
        "estocásticas descritas no manual, a sedimentação de óleo é omitida: "
        "a massa que seria depositada é classificada em 'outside'. Assim, "
        "não se pode comparar 'sediment' entre modos sem essa ressalva.",
        "§§ 8.1 e 22.4.6 (pp. 87 e 210–211).",
    ),
    "cleaned": (
        "Massa contabilizada na categoria de remoção/limpeza do balanço de "
        "massa fornecido pelo OSCAR.",
        "O manual descreve sistemas de resposta e recuperação mecânica com "
        "registros específicos de massa recuperada, mas não define de forma "
        "exaustiva quais operações alimentam 'cleaned' no arquivo .masbal.log. "
        "Não equiparar automaticamente esta coluna à eficiência de uma operação.",
        "§§ 5.5 e 6.3 (pp. 59 e 68–69).",
    ),
    "outside": (
        "Massa registrada na categoria 'outside' do balanço de massa. "
        "Em geral, é associada a material não mantido nos compartimentos "
        "representados dentro da área modelada.",
        "Ressalva fundamental: nas simulações estocásticas descritas no "
        "capítulo 8, a massa que seria sedimentada também é atribuída a "
        "'outside'. Portanto, esta série NÃO representa necessariamente "
        "apenas óleo fisicamente transportado além do limite do domínio.",
        "§§ 5.5 e 8.1 (pp. 59 e 87).",
    ),
}


def series_help_html() -> str:
    """Cria texto HTML de consulta, na ordem e com os nomes de config.py."""
    sections = []
    for item in SERIES_CONFIG:
        column = item["column"]
        meaning, caveat, reference = SERIES_INFO[column]
        sections.append(
            f"<h3>{escape(item['label'])} — <code>{escape(column)}</code></h3>"
            f"<p>{escape(meaning)}</p>"
            f"<p><b>Interpretação e limites:</b> {escape(caveat)}</p>"
            f"<p><i>Fonte: MEMW User's Manual, v15.2, {escape(reference)}</i></p>"
        )

    introduction = (
        "<h2>Entenda as 11 categorias MASBAL</h2>"
        "<p>Os valores (mt, toneladas métricas) são fornecidos pelo OSCAR no "
        "arquivo <code>.masbal.log</code>; esta janela apenas documenta seu significado. "
        "Uma categoria pode permanecer zerada conforme o cenário e os modelos ativados.</p>"
        "<p><b>Importante sobre as fontes:</b> a tabela da seção 5.5 do manual "
        "MEMW v15.2 descreve oito categorias no arquivo <code>.DTO</code>, "
        "enquanto os arquivos <code>.masbal.log</code> analisados apresentam "
        "onze categorias. Os textos abaixo combinam nomes observados no "
        "MASBAL e descrições físicas documentadas no manual, mas não constituem "
        "uma especificação oficial coluna a coluna do formato MASBAL.</p>"
    )
    return introduction + "<hr>" + "<hr>".join(sections)
