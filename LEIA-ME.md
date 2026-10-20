# CREAM 1.1.2

Plugin Python para Adobe Substance 3D Painter 12.1.3, Windows x64.
Converte uma planilha de backers em skins ZIP, usando o projeto aberto e um ZIP base.

## Instalação

1. Extraia o pacote inteiro em uma pasta.
2. Salve seu trabalho e feche o Painter.
3. Execute **Instalar.cmd**. Não precisa executar como administrador.
4. Abra o Painter e ative **Python → kr7_batch**.
5. Para reabrir a janela, use **Window → CREAM — Batch Exporter**.

O instalador copia `kr7_batch` para a pasta de plugins Python do Painter nos seus Documentos.
Se houver uma instalação anterior, guarda uma cópia em `kr7_plugin_backups`.
O preset TM2020 incluído é uma cópia do seu preset; só é instalado se ainda não existir.
O texconv oficial da Microsoft está incluído: não é preciso instalar Python, Pillow ou Excel.

Instalação manual: copie a pasta `kr7_batch` inteira para
`%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins`.

## Preparar o projeto

- Abra e salve seu `.spp` antes de começar. O plugin não salva nem cria projetos por backer.
- Use efeitos Fill de máscara chamados exatamente `PLAYER_NAME`, com uma fonte no canal Grayscale.
- Pode haver vários `PLAYER_NAME` dentro de grupos e máscaras. Todos são atualizados fora de Glass.
- Use Fill Layers `PLAYER_COLOR1`, `PLAYER_COLOR2` e/ou `PLAYER_COLOR3` com uma cor sólida no Base Color.
- O Base Color deve estar configurado individualmente; um material procedural que controla todos os canais precisa ser preparado como Fill de cor antes do lote.
- As outras propriedades dos Fill Layers, anchors, cores dos textos, projeções, fontes e tamanhos não são alterados.
- `Glass` não recebe personalização. Suas texturas ainda podem ser selecionadas para exportar.
- Os sets suportados na interface são `Details`, `Glass`, `Skin` e `Wheels`, sem UDIM ou material layering.
- O preset de saída deve se chamar exatamente `TM2020`, com mapas `$textureSet_B`, `_R`, `_I`, `_N`, `_CoatR`, `_DirtMask` e `_AO`.

## Planilha

Use `modelo_backers.csv` como exemplo. CSV deve ser UTF-8; aceita vírgula, ponto e vírgula ou tabulação.
Também é possível abrir o CSV no Excel e salvar como XLSX. Para XLSX, use a aba **Backers** ou a primeira aba.
Não use fórmulas nas células dessa aba: o plugin as rejeita para evitar valores de cache desatualizados.

| Coluna | Conteúdo |
|---|---|
| ativo | `sim` ou `não`; vazio conta como ativo |
| id | Identificador único da linha. Pode ficar vazio; será usado o número da linha |
| nome_player | Texto da skin, preservando maiúsculas e minúsculas; máximo 20 caracteres |
| nome_arquivo | Opcional. Nome para o ZIP quando o nick contém caracteres inválidos em arquivos |
| cor_1 | `#RRGGBB`, ou vazio para a cor original de PLAYER_COLOR1 |
| cor_2 | Mesmo formato para PLAYER_COLOR2 |
| cor_3 | Mesmo formato para PLAYER_COLOR3 |

Nomes acima de 20 caracteres são cortados e registrados como aviso. A contagem usa caracteres Unicode
após normalização NFC; emojis compostos podem ocupar mais de um caractere. Códigos de formatação
Trackmania comuns são rejeitados. Nomes vazios e caracteres de controle são rejeitados.

Nomes repetidos são permitidos; IDs explícitos repetidos não. A numeração do ZIP não muda o texto da skin:
`KR7 - Joseph.zip`, `KR7 - Joseph 2.zip`, `KR7 - Joseph 3.zip`.
Arquivos já existentes nunca são sobrescritos. Caracteres inválidos de arquivo viram `_`.

## Usar

1. Escolha a planilha e clique **Carregar planilha**.
2. Selecione o ZIP base da skin KR7. O ZIP de referência BIBLIOTECHA serviu para analisar o formato; ele não foi definido como base automaticamente.
3. Confira a pasta de saída. O padrão é `%USERPROFILE%\Documents\Trackmania\Skins\Models\CarSport\KR7BACKERS`.
4. Na aba **Texturas**, marque as saídas que variam entre backers e escolha a resolução de cada uma.
5. Clique **Validar configuração**. A aba Registro mostra os alvos encontrados.
6. Selecione um backer e clique **Prévia do backer selecionado** para conferir no modelo. Depois clique **Restaurar nomes e cores**.
7. Marque apenas um ou dois backers para o primeiro teste e clique **Exportar backers marcados**.
8. Confira esses ZIPs no Trackmania antes de executar as ~200 linhas.

Todas as texturas começam desmarcadas. A configuração é lembrada entre sessões.
As seleções e resoluções se aplicam igualmente a todos os backers do lote.
O ZIP base precisa ter seus arquivos diretamente na raiz e sem entradas duplicadas.
Arquivos selecionados substituem as entradas correspondentes; os demais são preservados.
Os novos ZIPs contêm apenas o conteúdo base e as texturas, sem relatórios ou arquivos temporários.

## Texturas

| Saída | DDS | Tratamento |
|---|---|---|
| B | BC1 | RGB, alpha forçado a opaco |
| R | BC5 | Canais do preset TM2020 preservados |
| I | BC3 | RGB e alpha preservados, inclusive RGB onde alpha é zero |
| N | BC5 | Normal OpenGL gerada pelo Painter; verde preservado na conversão |
| CoatR | BC4 | Canal único |
| DirtMask | BC4 | Canal único |
| AO | BC1 | RGB, alpha forçado a opaco |

Todos são DDS com cabeçalho legado e um único nível (sem mipmaps adicionais), como a referência.
PNG intermediário de 8 bits é exportado pelo Painter e removido depois da conversão.
A inversão de normal se aplica somente aos `_N` gerados; normals preservadas do ZIP base não mudam.
O CREAM usa Normal OpenGL no preset virtual de exportação, inclusive se o TM2020 salvo ainda usar DirectX.
Para exports manuais: File → Export Textures → Output Templates → TM2020; na saída `$textureSet_N`,
use RGB de Converted maps → Normal OpenGL. A alteração do template salvo é feita pela interface do Painter.

Details, Glass e Skin: 1024×1024, 2048×2048 ou 4096×4096.
Wheels: 256×1024, 512×2048 ou 1024×4096 para todas as texturas, incluindo DirtMask.

## Cancelar, retomar e recuperar

**Cancelar com segurança** interrompe a sequência na próxima etapa segura. Uma exportação síncrona do
Painter pode precisar terminar primeiro. Durante um freeze, o botão pode demorar a responder.
A conversão externa pode ser encerrada; arquivos intermediários não são publicados como skins.

Cada ZIP é montado em um arquivo `.partial`, lido novamente para verificar CRC, fechado e somente
então renomeado para o nome final. O ZIP base e ZIPs anteriores não são alterados.
Um fechamento abrupto pode deixar um `.partial`; ele não é uma skin concluída.

As linhas concluídas são desmarcadas. Para retomar depois de reabrir o plugin, carregue a mesma planilha,
restaure as mesmas opções e use **Retomar de relatório…** com o JSON de `_KR7_reports` na pasta de saída.
Só serão desmarcadas linhas registradas como concluídas cujo ZIP ainda existe. Confira o jogo antes de
retomar se você mudou manualmente o conteúdo do projeto: o relatório não compara toda a cena do `.spp`.
Se encerrar o aplicativo exatamente entre a publicação do ZIP e a gravação do relatório, confira esse
último ZIP manualmente para evitar uma cópia numerada ao retomar.

Erros isolados de exportação/conversão são registrados e o lote continua com o próximo backer.
Uma falha na restauração do projeto encerra o lote e mantém o registro de recuperação.

Nomes e cores originais são restaurados ao final, inclusive após cancelamento. Uma cópia pequena dos
valores é salva antes da primeira alteração em `%LOCALAPPDATA%\KR7BatchExporter\recover-*.json`.
Se o Painter fechar inesperadamente, reabra o mesmo `.spp` e use **Restaurar nomes e cores**.
Para essa recuperação, a hierarquia, os nomes dos layers e os recursos de fonte precisam continuar iguais.
O plugin não salva o `.spp` após restaurar; você decide quando salvá-lo.

O plugin espera o Painter ficar disponível e não usa temporizações fixas para supor que uma exportação
terminou. Mantém o autosave ligado. Um autosave pode registrar o backer atual; o registro de recuperação
guarda os originais. Não edite o projeto durante o lote. A janela de progresso bloqueia as interações
usuais até finalizar ou cancelar.

## Verificação desta entrega

- Conversão real com texconv: sete tipos de saída, dimensões e cabeçalhos DDS conferidos.
- Normal: canal verde preservado na conversão para BC5; OpenGL solicitado ao Painter antes da exportação.
- Emissivo: RGB preservado com alpha zero.
- Testes de CSV/XLSX, nomes repetidos, arquivo existente, cancelamento na montagem e ZIP base intacto.
- Testes do adaptador com API simulada: quatro fontes de máscara, Glass ignorado, restauração de cores,
  propriedades de texto preservadas e recusa de uma hierarquia alterada.
- Interface instanciada e renderizada com o Python 3.13 / PySide6 da instalação local do Painter.
- Fluxo do controlador testado com export do Painter simulado e conversor/ZIP reais: espera de ocupado,
  dois Joseph com cores diferentes, cancelamento no segundo backer e restauração final.

**Ainda requer teste dentro do seu projeto real e no Trackmania.** Os testes simulados não substituem
a validação do export do Painter com sua fonte customizada, anchors, canais e preset.

## Componentes

Código do plugin: `kr7_batch/core.py`, `painter.py`, `ui.py`, `__init__.py`.
Conversor: Microsoft DirectXTex texconv, release `may2026`, com licença MIT em `bin/LICENSE-DirectXTex.txt`.
SHA-256 do executável: `dcfdec10244e02cf5037fba089c55fb7e1326b1c8181742d77d15fa5cb5eef06`.
Origem: https://github.com/microsoft/DirectXTex/releases/tag/may2026

Para desinstalar, desative o plugin, feche o Painter e remova somente a pasta `python\plugins\kr7_batch`.
Isso não remove os ZIPs, o preset nem seus projetos. Preserve os registros de recuperação pendentes.
