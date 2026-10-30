# CREAM

**Color Replacement & Export Automation Manager**

Plugin para Substance 3D Painter no Windows: nomes e cores de uma planilha,
exportação de texturas para Trackmania 2020, conversão DDS e um ZIP por backer.

Leia [LEIA-ME.md](LEIA-ME.md) para instalação e uso. Referência: Painter 12.1.3;
API utilizada disponível a partir de 11.0, ainda sem validação real nessa versão mínima.

Ao carregar uma planilha CSV ou XLSX, selecione qual coluna contém o nome, cada cor,
ID, nome do ZIP e indicador de linha ativa. Há uma amostra dos dados; somente a coluna
do nome é obrigatória. O último mapeamento é lembrado para cabeçalhos idênticos.

## Atualizações privadas

A versão 1.1.0 deve ser instalada uma vez com `Instalar.cmd`, com o Painter fechado.
Depois, o plugin consulta o GitHub ao abrir, sem bloquear a interface.
Em **Configurar acesso privado**, informe um fine-grained personal access token criado
em https://github.com/settings/personal-access-tokens/new, limitado ao repositório
`tatauna-doesnt-code/cream`, com **Contents: Read-only**. Não compartilhe o token.
Ele fica criptografado pelo Windows para o usuário atual; nunca integra o pacote.

**Atualizar CREAM** baixa a versão estável, verifica o SHA-256 publicado pelo GitHub
e os arquivos do manifesto, e prepara a instalação. Salve e reinicie o Painter.
Na próxima inicialização, a instalação anterior é guardada em `python/cream-backups`.
Se a substituição falhar, a versão anterior é restaurada. Sem internet, o exportador
continua disponível. O botão manual permite repetir a consulta.

## Normals

O CREAM solicita `Normal_OpenGL` ao Painter antes de exportar a textura e a converte
para DDS BC5, preservando o canal verde. Não há inversão posterior. A saída virtual
usada pelo plugin é ajustada mesmo se o TM2020 salvo ainda usar `Normal_DirectX`.

Os DDS gerados usam os identificadores legados `BC5U` (R/N) e `BC4U` (CoatR/DirtMask),
conforme a skin validada no jogo. Somente os aliases de cabeçalho ATI2/ATI1 são
substituídos após a conversão; os dados comprimidos permanecem iguais.
Para upload no jogo, copie os ZIPs diretamente para `CarSport`, fora de subpastas.

Para os exports manuais, abra **File → Export Textures → Output Templates → TM2020**.
Na saída `$textureSet_N`, arraste **Converted maps → Normal OpenGL** para RGB.
Preserve os demais mapas e configurações. Faça um teste no jogo para confirmar o relevo.
A API pública não altera o template `.spexp` salvo: essa edição é feita pela interface.
O preset incluído no pacote continua sendo a referência original do usuário.

## Desenvolvimento

`python -m unittest discover -s tests -p "test_*.py"` (Pillow nos testes de DDS).
`python scripts/build_release.py` cria `dist/CREAM-plugin.zip`.
Publique esse arquivo como asset de uma release estável `vX.Y.Z` após atualizar
`kr7_batch/version.py`. O repositório permanece privado, sem licença open source.
O texconv incluído mantém sua licença Microsoft/MIT em `kr7_batch/bin`.

Documentação da API de releases: https://docs.github.com/en/rest/releases/assets
