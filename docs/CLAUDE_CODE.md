# Continuidade no Claude Code

## Documentação migrada

A documentação do projeto está preparada para o Claude Code. Não é necessário renomear os guias do aplicativo nem copiá-los para a memória pessoal do Claude.

| Antes | Equivalente utilizado |
| --- | --- |
| Instruções de contribuição para o agente (AGENTS.md, ausente na migração) | [CLAUDE.md](../CLAUDE.md) na raiz |
| Contexto longo em CONTEXTO.md | [Resumo vigente](../.claude/contexto.md), importado pelo CLAUDE.md |
| Cuidados de implementação e instalação espalhados no histórico | Regras por caminhos em [.claude/rules](../.claude/rules/) |
| Histórico de contexto acumulado | [Arquivo integral](HISTORICO_CONTEXTO.md), consultado sob demanda |
| Guias de uso e instalação | README e docs mantidos como documentação pública |

O arquivo [CONTEXTO.md](../CONTEXTO.md) permanece como índice para links antigos. O conteúdo original foi preservado integralmente em HISTORICO_CONTEXTO.md. Não existe configuração útil de projeto em `.codex/` ou `.agents/` visível nesta sessão; esses diretórios protegidos do ambiente não foram alterados. Não foram inventadas permissões, credenciais, hooks ou integrações equivalentes.

## Começar uma sessão

Abra o Claude Code na raiz deste repositório. O ponto de entrada é CLAUDE.md, que importa somente o resumo atual com `@.claude/contexto.md`; o histórico integral não é importado. As regras de `.claude/rules/` usam caminhos para orientar trabalho nas áreas correspondentes.

No Claude Code, use `/memory` para inspecionar as instruções carregadas. Para retomar, uma solicitação possível é:

> Leia o CLAUDE.md e o contexto do projeto. Preserve os efeitos aprovados. Confira a situação do GitHub antes de retomar a publicação pendente de fairy-mouse-effects. Não execute medições nem exija teste após reboot nesta etapa, pois foram adiados.

A migração não transfere a conversa da interface, autenticação GitHub, memória privada global ou permissões do ambiente anterior. As informações necessárias à continuidade estão nos arquivos versionáveis do projeto. A publicação no GitHub continua pendente, sem criação/push confirmado.

## Manter a documentação

Atualize o resumo em `.claude/contexto.md` com decisões e validações novas. Registre as etapas em PROCESSO.md; não acrescente versões conflitantes do estado atual ao resumo. Mantenha CLAUDE.md curto, com orientações estáveis e comandos reais. Acrescente regras específicas apenas às áreas que precisem delas. Não duplique o histórico integral nas regras.

O README continua priorizando usuários iniciantes. Mantenha instruções privadas em CLAUDE.local.md e ajustes pessoais em `.claude/settings.local.json`, ignorados pelo Git. Não grave tokens na documentação.

## Validação da migração

Foram conferidos imports, caminhos de regras, links locais e preservação integral do contexto anterior. Nenhum código executável, serviço ou permissão de mouse foi alterado. O carregamento no cliente Claude Code precisa ser confirmado ao abrir o projeto; não foi executado aqui.

Referência: [documentação oficial de memória do Claude Code](https://code.claude.com/docs/en/memory).
