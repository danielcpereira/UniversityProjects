# Relatório final do Projeto Googol

## 1. Arquitetura do projeto Web

A aplicação Googol utiliza uma arquitetura MVC, inteiramente desenvolvida com Spring Boot, para produzir as páginas Web 
e satisfazer as requisições HTTP. Nesse contexto, o servidor Web atua como cliente RMI, estabelecendo comunicações com o
servidor de indexação e armazenamento construído na Meta 1.

Na parte do Front End todas as páginas HTML foram construidas usando Thymeleaf. A maioria dos estilos foram armazenados 
em style.css permitindo uma fácil personalização do layout da aplicação. Cada template recebe um Model preenchido pelos 
controllers, que lhe passam tanto dados simples - i.e., dados de pesquisa - como dados mais complexos - i.e.,
informação em tempo real das estatísticas.
Na camada de controlo agrupa-se um conjunto de classes anotadas com @Controller e @RestController, cada uma responsavel 
por um conjunto de endpoints HTTP:
1. **IndexController**: apresenta a página inicial e orienta o fluxo do utilizador
2. **SearchController**: trata das pesquisas de termos, recebe o parâmetro q, chama o serviço RMI e entrega os resultados ao 
template search.html.
3. **StatsController e StatsViewController**: chamam, respetivamente, endpoints REST para obter estatísticas e uma página 
dinâmica que se atualiza via WebSocket (StatsWebSocketController).
4. **LinksController, BarrelsController e HackerNewsController**: gerem páginas específicas de links, barrels e notícias
do HackerNews.

O GatewayService centraliza toda a comunicação RMI.

A camada de domínio é composta pelas entidades e interfaces definidas na Meta 1 — i.e., Barrel.java , Downloader.java, 
URLQueue.java - que são partilhadas entre cliente e servidor stubs RMI.

Este modelo MVC, reforçado pela integração RMI e pelos WebSockets para comunicação em tempo real, assegura uma clara 
separação de responsabilidades, promovendo modularidade e escalabilidade.

## 2. Integração de Spring Boot com o servidor RMI

A integração do Spring Boot com o servidor RMI começa com a definição das configurações de host e porta no 
application.properties. O bean GatewayService (@Service), lê esses valores com @Value e, no método @PostConstruct, define
o URL da forma rmi://host:port/Gateway, executa o Naming.lookup() e guarda o stub da interface GatewayHeader.
Nos controllers de pesquisa, estatísticas ou indexação, o serviço é utilizado para invocar métodos remotos, isolando a 
lógica de comunicação RMI.

## 3. Integração de WebSockets com Spring Boot RMI

A comunicação em tempo real entre o cliente e o servidor é implementada por WebSockets.
Esses são configurados em WebSocketConfig.java para expor o endpoint /ws.
São utilizados pelos controllers BarrelsWebSocketController e StatsWebSocketController para publicar as informações 
vindas do backend, enviando-as aos tópicos /topic/barrels e /topic/stats, onde o cliente recebe os dados e atualiza a 
interface automaticamente.

## 4. Integração de REST WebServices no projeto

Foram integrados dois serviços REST externos :

Hacker News:
Usa a API pública para obter as top stories e stories de um determinado usuário. Implementado em HackerNewsService.java
e acionado via HackerNewsController nos endpoints /hn/index-top e /hn/index-user.

Ollama: 
Integração via API REST com o servidor local Ollama. Em OllamaChatService.java, é usado RestTemplate para enviar requisições
POST ao endpoint configurado em ollama.api.url com o modelo definido em ollama.model. A resposta é mostrada em search.html.

## 5. Testes de software

| Caso de Teste             | Descrição                                        | Resultado Esperado                  | Status |
|---------------------------|--------------------------------------------------|-------------------------------------|--------|
| Indexação via Web         | Submeter URL no browser                          | URL processado e indexado           | ✅ Pass |
| Pesquisa várias palavras  | Pesquisar termos e receber lista                 | Retorna URLs relevantes             | ✅ Pass |
| Página de Links           | Clicar em “Links para URL”                       | Lista correta de páginas            | ✅ Pass |
| Integração AI             | Gerar análise após pesquisa                      | Texto de análise apresentado        | ✅ Pass |
| Integração HackerNews     | Botões “Indexar Top Stories” e "Indexar Perfil"  | URLs do HN indexados                | ✅ Pass |
| Atualização em Tempo Real | Estatísticas atualizadas na web em tempo real    | Informações atualizadas sem refresh | ✅ Pass |


## 6. Distribuição de tarefas

Mais uma vez, procuramos realizar todas as funcionalidades em conjunto presencialmente e/ou virtualmente para que houvesse uma 
distribuição equitativa, não havendo uma partição clara das tarefas.

## 7. Conclusão

O projeto Googol permitiu consolidar conhecimentos em Spring Boot, RMI, WebSockets e integração com APIs REST. 
A aplicação resultante é funcional, estável e responde em tempo real às interações do utilizador.
O trabalho colaborativo foi essencial para o sucesso do projeto, garantindo uma partilha equilibrada de tarefas e aprendizagens. 


Daniel Coelho Pereira 2021237092
Eduardo Luís Pereira Marques 2022231584
