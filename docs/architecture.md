# ModelTrace - Arquitetura

Guia completo de consumo da API: [`api.md`](api.md)

Documentacao completa do software: [`documentacao-software.md`](documentacao-software.md)

Manual funcional da interface: [`manual-funcionalidades.md`](manual-funcionalidades.md)

Melhorias para produto real: [`melhorias-produto-real.md`](melhorias-produto-real.md)

O ModelTrace foi implementado como uma aplicacao web separada em back-end FastAPI e front-end Next.js.

## Componentes

- **FastAPI:** validacao, autenticacao, ingestao, feedback, auditoria e consultas.
- **DocumentStore:** camada de persistencia com dois adaptadores.
- **MongoDocumentStore:** usa MongoDB real quando `MONGODB_URL` esta configurado.
- **JsonDocumentStore:** modo local sem Docker, persistindo documentos em arquivo JSON.
- **Next.js:** interface de produto com dashboards, Workbench, Governanca, command palette e Docs.

## Fluxo principal

1. Usuario registra conta.
2. Usuario cria projeto.
3. Usuario cria modelo e versao.
4. Usuario gera API key com escopos e expiracao.
5. Sistema externo envia predicao com escopo `predictions:write` ou lote com `predictions:batch`.
6. Back-end valida payload e idempotencia.
7. Predicao e salva como documento.
8. Feedback posterior atualiza a predicao por usuario autenticado ou API key com `feedback:write`.
9. Snapshot de metricas e recalculado.
10. Dashboard consome agregados.

## Documentacao No Produto

A aba `Docs` no front-end funciona como manual de usuario. Ela explica o que cada area faz, como usar, o que entrega e topicos relacionados. A documentacao tecnica completa permanece nesta pasta `docs/`.

## Observacao sobre Docker

O repositorio contem `docker-compose.yml`, mas o ambiente local usado no desenvolvimento nao possui Docker instalado. Por isso o back-end tambem roda em modo documental local usando arquivo JSON. Para a disciplina, recomenda-se configurar `MONGODB_URL` com MongoDB Atlas ou usar Docker em uma maquina com Docker instalado.
