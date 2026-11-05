# Fairy Mouse — instruções para Claude Code

## Projeto e comunicação

Ferramenta Python para Fedora com Sway padrão: rastro de fada e brilho no botão esquerdo físico, em segundo plano. O visual foi aprovado; preserve-o. Priorize efeitos simples, estruturas limitadas e animação suspensa em repouso.

Converse e documente em português do Brasil. O início do README deve ser compreensível para leigos, com passos claros para instalar, liberar o mouse, iniciar e habilitar o serviço. Distinga estado observado, teste simulado e validação real.

## Contexto carregado na sessão

@.claude/contexto.md

O histórico detalhado é consultado sob demanda, sem importá-lo inteiro. Para implementação, leia `docs/INTEGRACAO.md`; para instalar, `docs/INSTALACAO.md` e `docs/ACESSO_MOUSE.md`. O histórico está em `docs/PROCESSO.md` e `docs/HISTORICO_CONTEXTO.md`.

## Estrutura

- `fairy_mouse/`: CLI, GUI, protocolo de cursor, clique, simulação e desenho.
- `tests/`: unittest, dispositivos/compositor simulados e testes de instalação.
- `tools/`: instalação por usuário, regra de acesso e eventos sintéticos.
- `packaging/`: unidade systemd e regra udev genérica para mouses (regra antiga do Logitech em `legacy/`).
- `instalar.sh` / `desinstalar.sh`: instalação completa em um comando, para leigos.
- `main.py`: entrada alternativa à execução do módulo.
- `.claude/rules/`: orientações por área, selecionadas pelos caminhos editados.

## Comandos de desenvolvimento

Use `/usr/bin/python3`: o Python do PATH pode pertencer a outro projeto. Não use `.venv` como prova de dependências disponíveis no sistema.

```bash
/usr/bin/python3 -m fairy_mouse --diagnose
/usr/bin/python3 -m fairy_mouse --demo
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q fairy_mouse main.py tests tools
```

Mudanças em regra udev: `udevadm verify packaging/udev/71-fairy-mouse.rules`. Mudanças nos instaladores shell: `bash -n instalar.sh desinstalar.sh tools/install-mouse-access.sh`.

Execute os testes relevantes a mudanças de comportamento e os verificadores afetados. Para documentação, confira comandos e links; não repita toda a suíte sem necessidade. Relate testes ignorados e limitações de ambiente.

## Trabalho e continuidade

Use quatro espaços em Python, snake_case para funções e variáveis e PascalCase para classes. Não há formatter/linter ou meta de cobertura configurados. Separe a simulação da GUI; mantenha GTK na thread principal.

Atualize `.claude/contexto.md` ao mudar o estado vigente e registre trabalho em `docs/PROCESSO.md`. Mantenha comandos públicos coerentes entre README e documentos técnicos. Não trate planos antigos como pendências atuais.

Antes de operações Git, confira o estado e o remoto reais. O histórico Git não estava acessível na sessão anterior; não há convenção verificada. Use assuntos imperativos e descreva comportamento e validação em PRs. Não afirme publicação no GitHub sem confirmação do remoto.

Não crie permissões automáticas, hooks, serviços ou integrações do Claude apenas para migrar documentação. Respeite as permissões disponíveis no ambiente da sessão atual; limitações da sessão anterior não são restrições permanentes do projeto.
