# Gamebras Alfa

Engine de jogos 2.5D. Abra index.html. O projeto, recursos e dependências estão incorporados.

Build: python montar-gamebras.py gamebras-base.html.

Créditos e licenças no bundle interno (_runtime/ e _tools/). Código do PixelBras sujeito à autorização dos titulares.

Prévia local: python -m http.server 8796 --bind 127.0.0.1

Publicação somente após validação e aprovação. Não publicar gravações privadas.

## Plantão de diabetes

Em `index.html`, use **Plantão** para abrir a aula e os casos ou aborde os personagens no cenário. As decisões avançam o relógio compartilhado. O prontuário mostra achados registrados e o caderno PBL oferece sete etapas de raciocínio por pessoa.

Para reconstruir sem rede a partir da tag v6.4.1 e desta árvore, execute `python tools/build-diabetes.py --output-dir ../gamebras-diabetes-build`. Para conferir a distribuição versionada, use `python tools/build-diabetes.py --check` e `node --test tests/*.test.cjs`.

O ZIP isolado do módulo é importável pela interface. O visualizador de fluxos permite inspecionar os grafos. A execução usa as regras do JSON do módulo. Os casos e modelos são educacionais e passam por validação técnica; a revisão clínica humana e a avaliação pedagógica continuam pendentes.
