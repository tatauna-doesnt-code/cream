# CREAM

**Color Replacement & Export Automation Manager**

Plugin para Substance 3D Painter no Windows: nomes e cores de uma planilha,
exportação de texturas para Trackmania 2020, conversão DDS e um ZIP por backer.

Leia [LEIA-ME.md](LEIA-ME.md) para instalação e uso. Referência: Painter 12.1.3;
API utilizada disponível a partir de 11.0, ainda sem validação real nessa versão mínima.

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

A textura é convertida para DDS BC5 primeiro. Depois, somente o bloco verde é
invertido, incluindo seus índices de interpolação. Não há segunda compressão;
o canal vermelho e o cabeçalho permanecem idênticos. A interpolação inteira do
decodificador pode causar diferença de até 1 unidade em 255.

## Desenvolvimento

`python -m unittest discover -s tests -p "test_*.py"` (Pillow nos testes de DDS).
`python scripts/build_release.py` cria `dist/CREAM-plugin.zip`.
Publique esse arquivo como asset de uma release estável `vX.Y.Z` após atualizar
`kr7_batch/version.py`. O repositório permanece privado, sem licença open source.
O texconv incluído mantém sua licença Microsoft/MIT em `kr7_batch/bin`.

Documentação da API de releases: https://docs.github.com/en/rest/releases/assets
