# Gamebras — requisitos e normas de desenvolvimento

## 1. O que é o projeto
Gamebras é uma engine 2.5D de autoria de jogos e simulações interativas, com editor de recursos PixelBras, documentos, cenários e campanhas. Gamebras Médico é sua aplicação educacional experimental para aprendizagem baseada em problemas (PBL), não um sistema de decisão clínica real. O objetivo de pesquisa é investigar a aprendizagem, a tomada de decisão e a interação com pacientes simulados; eficácia pedagógica ainda não demonstrada.

## 2. Requisitos obrigatórios
- Engine independente do domínio: renderização, câmera, toque, inventário, interação, relógio, eventos, variáveis, avaliação, documentos, voz, animação e execução de grafos são capacidades genéricas. Nenhuma regra específica de doença ou identificação de paciente deve permanecer no núcleo após M6.
- Módulos autocontidos, importáveis, editáveis, validáveis e exportáveis; JSON versionado como fonte de verdade. Assets, glossário, referências, textos, perfis de voz, cenários, fisiologia, intervenções e avaliação pertencem ao módulo. Preservar compatibilidade com campanhas não médicas.
- Dois tipos de grafos executáveis: atendimento e comportamento. A facilitadora tem grafo próprio. SVG interativo representa o JSON; permitir edição, navegação, análise de referências, alcance, ciclos e execução limitada. Ciclos de reavaliação são legítimos; não permitir execução infinita. Não executar JavaScript arbitrário de módulos.
- Estado clínico compartilhado, evolução em tempo simulado, observações separadas do estado oculto, intervenções com efeitos e histórico auditável. Encaminhamento, alta, erro e evolução posterior são distintos. Não confundir presença física com resolução clínica.
- PBL: esclarecer termos, definir problema, formular hipóteses, organizar explicações, definir objetivos, estudar autonomamente, sintetizar/reavaliar. Registrar raciocínio por paciente; oferecer pistas graduais, feedback imediato e evolutivo, sem entregar respostas indiscriminadamente.
- Glossário e biblioteca clínica disponíveis offline, termos clicáveis, definições curtas e documentos Markdown editáveis no visualizador existente. Links externos oficiais complementares, com edição/data verificadas; revisão clínica humana antes de alegar validade.
- Personagens individualizados: ID estável, sprite, avatar, voz, história, exame e comportamento coerentes. Narração de todos os textos clínicos, controles de pausa/repetição; voz offline depende do dispositivo ou áudio incorporado. Animações refletem estado clínico, incluindo postura, marcha e repouso.
- Interface móvel em retrato e paisagem, janelas expansíveis, arrastáveis e recolhíveis; leitura e decisões acessíveis sem sobreposição com joystick, mochila, recentralização ou botões de ação. Ferramentas de jogo primeiro, desenvolvimento/status depois. Pinça, pan e recentralização. Preservar desempenho.
- Exportação autocontida HTML/ZIP, recursos locais, editor de documentos e assets; edição da própria fonte apenas em cópia, sem execução automática ou publicação implícita. Preservar créditos e licenças.

## 3. Objetivos e critérios de aceitação
M6: carregar engine sem diabetes; carregar segundo módulo sem alterar núcleo; dois grafos executáveis por módulo; validar referências e assets; preservar campanhas antigas; regressões clínicas e de interface. Diabetes: Paulo (hipoglicemia) pode receber alta após recuperação e reavaliação adequadas, quando não houver fatores de risco que exijam encaminhamento; Marina (CAD) exige avaliação urgente e transferência apropriada; Rosa (DM2) requer avaliação individual. Não usar glicemia isolada para diagnosticar CAD. Modelos são simplificações educativas, não prescrições. Validar cenários de erro, atraso, recorrência, contraindicações e reavaliação. Revisar visualmente cada sprite e mapa; não confundir hash ou dimensão com inspeção visual.

## 4. Organização pretendida (ainda não implementada integralmente)
`modules/<id>/module.json`, `scenario.json`, `patients.json`, `physiology.json`, `treatments.json`, `assessment.json`, `glossary.json`, `flows/clinical/`, `flows/behavior/`, `flows/facilitator/`, `docs/`, `assets/`. Manifesto com versão de esquema, dependências e entradas. Definir migração de formatos antigos, validação e limites de recursos. O empacotamento deve preservar o funcionamento offline e o formato legado quando possível.

## 5. Roadmap e estado de referência
- M0–M1: editor, relógio, inventário, documentos, navegação. Checkpoint 6af59be informado; testes do relógio aprovados.
- M2–M3: simulação clínica inicial e campanha diabetes; b97a8d0 publicado na branch experimental.
- M4: janelas, controles, triagem e biblioteca local; 69ab842 publicado na branch experimental, quatro testes aprovados antes da consolidação. Deploy na main/site não confirmado independentemente.
- M5: PBL, glossário, facilitadora, narração e visualização SVG experimental. Fonte atual recebida; branch experiment/pbl-m5, HEAD 69ab84294086726e7bb5453e81e6639f37495c04, HTMLs modificados, diagnostico-m4.html não rastreado (auditoria recebida). Persistem erros relatados de avatar, encaminhamento de Paulo e sobreposição. Grafos ainda não executam a campanha.
- M6.0: auditoria e recebimento da fonte atual concluídos; migração pendente. M6.1: contrato de módulo e executor genérico, testes isolados. M6.2: migrar conteúdo clínico e pedagógico, eliminar acoplamentos específicos. M6.3: separar campanhas e assets, revisar casos, sprites e cenário UBS. M6.4: integração gráfica dos dois grafos, testes de execução e interface. M6.5: segundo módulo demonstrativo e validação de portabilidade.
- M7: ampliar cenários e módulos, melhorar acessibilidade, áudio e instrumentos de avaliação; estudo piloto com revisão ética e metodológica quando aplicável.

## 6. Processo de desenvolvimento
1. Confirmar repositório, caminho, branch, HEAD, estado local, ambiente, documentação e testes. Não presumir que versões enviadas correspondem ao checkout. Registrar hipóteses e critérios de aceitação antes de editar.
2. Preservar trabalho local e versão pública. Usar branch/worktree experimental e checkpoints temáticos; alterações pequenas, reversíveis, sem refatoração incidental. Reutilizar componentes. Não sobrescrever AGENTS.md existente sem conciliar seu conteúdo.
3. Instaladores Python/Bash completos, idempotentes, com dry-run, âncoras ou hashes, backup e falha explícita. Verificar todos os alvos antes de escrever; não esconder erros. Não alterar bundles ou assets não relacionados. Usar /sdcard/Download e nomes efetivamente verificados no Termux.
4. Testar sintaxe, regressões, integração, integridade ZIP, compatibilidade de módulos, segurança do interpretador e interface real em retrato/paisagem. Medir desempenho antes/depois quando pertinente. Distinguir teste unitário, integração e validação visual; não declarar testes não executados.
5. Entregar arquivos, comandos completos, resultados, limitações e reversão. Diagnósticos extensos em arquivo. Não incluir arquivos temporários em commits. Não fazer push, merge, reset, deploy ou operação destrutiva sem autorização explícita; autorização de documentação não autoriza publicação de código experimental.
6. Atualizar este documento e roadmap nos checkpoints. Preservar autoria, créditos, licenças e dados privados. Não incorporar dados reais de pacientes; pesquisa com participantes requer governança adequada.

## 7. Ambiente e publicação
Repositório informado: git@github.com:livredopodervil/gamebras.git. Worktree experimental informado: ~/gamebras-med-experiment; estável: ~/gamebras-med-dev. Teste local: `~/abrir-gamebras.sh` (porta 8801; verificar identidade do servidor). Gates: `git diff --check` e `node --test tests/*.test.cjs`. Página pública: https://rogerioduarte.org/gamebras/. Publicar somente checkpoint aprovado, preservando metadados, imagem social e outros arquivos do site. Confirmar deploy efetivo. Não assumir que a versão pública é a última experimental.

## Identidade e continuidade portátil (M6)
Cada distribuição deve incorporar manifesto gamebras.lineage/1, SHA-256 do HTML sem o manifesto, hashes dos arquivos de desenvolvimento e identificador SHA-256 do manifesto canônico sem version_id. Pais são IDs completos; merges registram todos os pais. Branch e Git HEAD são metadados, não identidade. O HEAD registrado é a base de trabalho, não o commit futuro do próprio HTML. Preserve snapshots ancestrais para reconstruir o DAG. Não inclua segredos. Execute o verificador antes de distribuir. M6.1: selagem e verificação; M6.2: interface de exportação; M6.3–M6.7: executor, migração diabetes, editor, segundo módulo e continuidade independente. Não declare essas etapas concluídas antes dos testes.

## M6.2–M6.3 (incremento experimental)
Contexto portátil: manifesto e arquivos exportáveis pela interface. Executor declarativo genérico isolado: condições, efeitos e limite de transições. Ainda não conectado aos fluxos clínicos; M6.4 pendente. Downloads Android: localizar pelo SHA-256, não pelo nome.

## M6.4 — contrato clínico declarativo
A engine lê `clinicalModule` da fase (schema `gamebras.clinical/1`); regras, fluxos de seleção, evolução, triagem, observações, feedback, facilitador e referências ficam no módulo. Não incluir condições específicas de doenças no JavaScript genérico. A pasta `modules/diabetes/` contém a campanha isolada; o HTML distribuído incorpora sua configuração no JSON do bundle. A edição do fluxograma nesta versão é uma prévia de sessão, não altera automaticamente regras clínicas. M6.5: edição executável persistente; M6.6: segundo cenário completo e validação visual.

## M6.4.1 — distribuição enxuta
Pais imediatos e URLs de commits; tag de distribuição permanente. Não incorporar arquivos binários novamente no contexto quando disponíveis no bundle. Preservar fonte de terceiros no repositório e avisos de licença. Verificar ambos os HTMLs antes de publicar.

## Expansão PBL de diabetes sobre v6.4.1

Branch experimental iniciada no commit 854a2d926315948dd8b0e746b87c72a64914567d. As decisões clínicas, variáveis, pacientes, tutoria e aula são dados do módulo. O painel de atendimento aceita o mesmo contrato declarativo para outros módulos e a interface anterior serve campanhas sem o painel. Os ramos de urgência simulam reconhecimento, suporte inicial e destino. O tratamento hospitalar, a validação clínica humana e a avaliação de eficácia pedagógica ainda exigem trabalho próprio. Regenerar e verificar a distribuição com `python tools/build-diabetes.py --output-dir ../gamebras-diabetes-build` e `python tools/build-diabetes.py --check`. Execute os testes antes da integração.
