package com.googol.meta1;
import java.io.*;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

public class Gateway extends UnicastRemoteObject implements GatewayHeader {
    private static Map<String, Integer> globalStatisticsMap = Collections.synchronizedMap(new HashMap<>());
    private Map<String, Boolean> barrelStatus = new ConcurrentHashMap<>();
    private final Map<String, Integer> barrelCounts = new ConcurrentHashMap<>();
    private List<String> availableBarrels = Collections.synchronizedList(new ArrayList<>());
    private Random random = new Random();

    private Map<String, ArrayList<String>> index;
    private Map<String, ArrayList<String>> links;
    private static final String INDEX_FILE = "index.txt";
    private static final String LINKS_FILE = "links.txt";

    private ScheduledExecutorService scheduler;

    /**
     * O Construtor do Gateway inicializa os componentes necessários para o funcionamento do sistema.
     * Carrega estatísticas, inicializa as estruturas de dados para o índice e links, identifica
     * Barrels disponíveis e configura o backup periodico dos dados.
     *
     * @throws RemoteException erro na comunicação RMI.
     */
    public Gateway() throws RemoteException {
        super();
        loadStatisticsFromFile("estatisticas.txt");

        this.index = Collections.synchronizedMap(new HashMap<>());
        this.links = Collections.synchronizedMap(new HashMap<>());

        loadDataFromFiles();
        findAvailableBarrels();
        setupPeriodicSaving();
    }

    /**
     * Configuração para guardar periodicamente os dados do índice e links nos respetivos ficheiros.
     */
    private void setupPeriodicSaving() {
        scheduler = Executors.newScheduledThreadPool(1);
        scheduler.scheduleAtFixedRate(() -> {
            try {
                System.out.println("Performing periodic saving of index and links...");
                saveDataToFiles();
            } catch (Exception e) {
                System.err.println("Error during periodic save: " + e.getMessage());
            }
        }, 5, 5, TimeUnit.MINUTES);
    }

    /**
     * Carrega os dados dos ficheiros.
     */
    private void loadDataFromFiles() {
        loadIndexFromFile();
        loadLinksFromFile();
    }

    /**
     * Guarda os dados nos ficheiros.
     */
    private synchronized void saveDataToFiles() {
        saveIndexToFile();
        saveLinksToFile();
    }

    /**
     * Carrega o índice de palavras a partir do respetivo ficheiro.
     */
    @SuppressWarnings("unchecked")
    private synchronized void loadIndexFromFile() {
        File indexFile = new File(INDEX_FILE);

        if (!indexFile.exists()) {
            System.out.println("Index file not found. Starting with empty index.");
            return;
        }

        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(indexFile))) {
            Map<String, ArrayList<String>> loadedIndex = (Map<String, ArrayList<String>>) ois.readObject();
            this.index.putAll(loadedIndex);
            System.out.println("Index loaded successfully: " + this.index.size() + " words");
        } catch (Exception e) {
            System.err.println("Error loading index file: " + e.getMessage());
        }
    }

    /**
     * Carrega os links a partir do respetivo ficheiro.
     */
    @SuppressWarnings("unchecked")
    private synchronized void loadLinksFromFile() {
        File linksFile = new File(LINKS_FILE);

        if (!linksFile.exists()) {
            System.out.println("Links file not found. Starting with empty links.");
            return;
        }

        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(linksFile))) {
            Map<String, ArrayList<String>> loadedLinks = (Map<String, ArrayList<String>>) ois.readObject();
            this.links.putAll(loadedLinks);
            System.out.println("Links loaded successfully: " + this.links.size() + " URLs");
        } catch (Exception e) {
            System.err.println("Error loading links file: " + e.getMessage());
        }
    }

    /**
     * Guarda o índice de palavras no respetivo ficheiro.
     */
    private synchronized void saveIndexToFile() {
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(INDEX_FILE))) {
            oos.writeObject(this.index);
            System.out.println("Index saved successfully: " + this.index.size() + " words");
        } catch (IOException e) {
            System.err.println("Error saving index file: " + e.getMessage());
        }
    }

    /**
     * Guarda os links no respetivo ficheiro.
     */
    private synchronized void saveLinksToFile() {
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(LINKS_FILE))) {
            oos.writeObject(this.links);
            System.out.println("Links saved successfully: " + this.links.size() + " URLs");
        } catch (IOException e) {
            System.err.println("Error saving links file: " + e.getMessage());
        }
    }

    /**
     * Adiciona ao ArrayList<String>> index
     *
     * @param url O URL a ser indexada.
     * @param title O título da página.
     * @param description A descrição da página.
     * @param words Lista de palavras encontradas na página.
     * @param pageLinks Lista de links encontrados na página.
     * @throws RemoteException erro na comunicação RMI.
     */
    @Override
    public synchronized void addToIndex(String url, String title, String description, List<String> words, List<String> pageLinks) throws RemoteException {
        //HackerNews Control
        if (this.links.containsKey(url)) {
            System.out.println("URL already indexed, skip: " + url);
            return;
        }

        for (String word : words) {
            word = word.toLowerCase();
            index.putIfAbsent(word, new ArrayList<>());
            if (!index.get(word).contains(url)) {
                index.get(word).add(url);
            }
        }

        this.links.put(url, new ArrayList<>());
        this.links.get(url).add(title);
        this.links.get(url).add(description);
        this.links.get(url).addAll(pageLinks);

        System.out.println("Added URL data: " + url + " to index");

        if (words.size() > 0 || pageLinks.size() > 0) {
            saveDataToFiles();
        }
    }

    /**
     * Esta função realiza uma pesquisa por palavras e retorna os URLs associados com os respetivos títulos e descrições.
     * O método calcula a relevância de cada URL com base nas palavras presentes na busca.
     *
     * @param searchWord A string contendo as palavras a serem pesquisadas.
     * @return Uma lista de strings, onde cada string representa um URL, título e descrição associados.
     * @throws FileNotFoundException Se o ficheiro que armazena o índice não for encontrado.
     * @throws IOException Se ocorrer erro ao ler o ficheiro que armazena o índice.
     */
    @Override
    public List<String> searchInIndex(String searchWord) throws RemoteException, FileNotFoundException, IOException {
        String[] words = searchWord.split(" ");

        for (String word : words) {
            word = word.toLowerCase();
            if (!index.containsKey(word)) {
                return new ArrayList<>();
            }
        }

        String firstWord = words[0].toLowerCase();
        ArrayList<String> commonUrls = new ArrayList<>(index.get(firstWord));

        for (int i = 1; i < words.length; i++) {
            String word = words[i].toLowerCase();
            commonUrls.retainAll(index.get(word));
        }

        if (commonUrls.isEmpty()) {
            return new ArrayList<>();
        }

        Map<String, Integer> urlRelevance = new HashMap<>();
        for (String url : links.keySet()) {
            ArrayList<String> linkedUrls = links.get(url);
            for (String linkedUrl : linkedUrls) {
                if (commonUrls.contains(linkedUrl)) {
                    urlRelevance.put(linkedUrl, urlRelevance.getOrDefault(linkedUrl, 0) + 1);
                }
            }
        }

        List<String> results = new ArrayList<>();
        commonUrls.stream()
            .sorted((url1, url2) -> {
                int relevance1 = urlRelevance.getOrDefault(url1, 0);
                int relevance2 = urlRelevance.getOrDefault(url2, 0);
                return Integer.compare(relevance2, relevance1);
            })
            .forEach(url -> {
                ArrayList<String> urlInfo = links.get(url);
                String result = url + ";" + urlInfo.get(0) + ";" + urlInfo.get(1) + ";" + urlRelevance.getOrDefault(url, 0);
                results.add(result);
            });

        return results;
    }

    /**
     * Retorna os links que acederam ao link inserido como parâmetro de entrada.
     *
     * @param url O URL para o qual se deseja encontrar os links associados.
     * @return Uma lista de URLs que acedem ao URL fornecido.
     * @throws FileNotFoundException Se o ficheiro que armazena o índice não for encontrado.
     * @throws IOException Se ocorrer erro ao ler o ficheiro que armazena o índice.
     */
    @Override
    public List<String> findLinksToUrl(String url) throws RemoteException, FileNotFoundException, IOException {
        List<String> results = new ArrayList<>();
        for (String link : this.links.keySet()) {
            ArrayList<String> info = this.links.get(link);
            for (int i = 2; i < info.size(); i++) {
                if (info.get(i).equals(url)) {
                    results.add(link);
                }
            }
        }
        return results;
    }
    /**
     * Identifica os barrels disponíveis no sistema RMI.
     */
    private synchronized void findAvailableBarrels() {
        try {
            Registry registry = LocateRegistry.getRegistry(
                    Configuration.RMI_HOST, Configuration.RMI_PORT
            );
            Set<String> services = Arrays.stream(registry.list())
                    .filter(s -> s.startsWith("Barrel"))
                    .collect(Collectors.toSet());

            Iterator<String> it = availableBarrels.iterator();
            while (it.hasNext()) {
                String name = it.next();
                if (!services.contains(name)) {
                    barrelStatus.remove(name);
                    it.remove();
                } else {
                    try {
                        BarrelHeader stub = (BarrelHeader)
                                Naming.lookup("rmi://" +
                                        Configuration.RMI_HOST + ":" +
                                        Configuration.RMI_PORT + "/" + name
                                );
                        stub.ping();
                    } catch (Exception e) {
                        barrelStatus.remove(name);
                        it.remove();
                    }
                }
            }

            for (String svc : services) {
                if (!barrelStatus.containsKey(svc)) {
                    barrelStatus.put(svc, false);
                    availableBarrels.add(svc);
                }
            }

        } catch (Exception e) {
            System.err.println("Error searching for available barrels: " + e.getMessage());
        }
    }

    /**
     * Seleciona aleatoriamente um barrel disponível.
     *
     * @return Nome do barrel ou null.
     */
    private synchronized String selectRandomAvailableBarrel() {

        List<String> freeBarrels = availableBarrels.stream()
            .filter(barrel -> !barrelStatus.getOrDefault(barrel, true))
            .collect(Collectors.toList());

        if (freeBarrels.isEmpty()) {

            findAvailableBarrels();


            freeBarrels = availableBarrels.stream()
                .filter(barrel -> !barrelStatus.getOrDefault(barrel, true))
                .collect(Collectors.toList());

            if (freeBarrels.isEmpty()) {
                return null;
            }
        }

        // Seleciona um barrel aleatoriamente
        int index = random.nextInt(freeBarrels.size());
        String selectedBarrel = freeBarrels.get(index);
        barrelStatus.put(selectedBarrel, true); // Marca como ocupado
        return selectedBarrel;
    }

    /**
     * Marca um Barrel como disponivel.
     *
     * @param barrelName Nome do Barrel a ser disponibilizado.
     */
    private synchronized void releaseBarrel(String barrelName) {
        barrelStatus.put(barrelName, false);
    }

    /**
     * Le as estatísticas a partir do ficheiro.
     * @param filePath Caminho para o arquivo de estatísticas.
     */
    private synchronized void loadStatisticsFromFile(String filePath) {
        try (BufferedReader reader = new BufferedReader(new FileReader(filePath))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;


                int lastSpace = line.lastIndexOf(' ');
                if (lastSpace <= 0) continue; //

                String phrase = line.substring(0, lastSpace);
                String numberStr = line.substring(lastSpace + 1);

                try {
                    int count = Integer.parseInt(numberStr);
                    globalStatisticsMap.put(phrase, count);
                } catch (NumberFormatException e) {
                    System.err.println("Ignoring invalid line in statistics: " + line);
                }
            }
        } catch (IOException e) {
            System.err.println("Error reading statistics file: " + e.getMessage());
        }
    }

    /**
     * Guarda ordenadamente as estatísticas no ficheiro.
     *
     * @param filePath Caminho para o arquivo de estatísticas.
     */
    private synchronized void saveStatisticsToFile(String filePath) {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(filePath))) {
            List<Map.Entry<String, Integer>> sortedEntries = globalStatisticsMap.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .collect(Collectors.toList());

            for (Map.Entry<String, Integer> entry : sortedEntries) {
                writer.write(entry.getKey() + " " + entry.getValue());
                writer.newLine();
            }
        } catch (IOException e) {
            System.err.println("Error saving statistics file: " + e.getMessage());
        }
    }

    /**
     * Atualiza as estatísticas com um novo termo pesquisado.
     *
     * @param searchTerm O termo a ser adicionado.
     * @throws RemoteException erro na comunicação RMI.
     */
    @Override
    public synchronized void updateStatistics(String searchTerm) {
        searchTerm = searchTerm.toLowerCase().trim();
        if (!searchTerm.isEmpty()) {
            globalStatisticsMap.put(searchTerm, globalStatisticsMap.getOrDefault(searchTerm, 0) + 1);
            saveStatisticsToFile("estatisticas.txt");
        }
    }

    /**
     * Lê as estatísticas e retorna as 10 mais frequentes.
     *
     * @param filePath O caminho do ficheiro de estatísticas.
     * @return Um mapa contendo os 10 termos de pesquisa mais frequentes.
     * @throws RemoteException erro na comunicação RMI.
     */
    @Override
    public Map<String, Integer> readStatisticsFromFile(String filePath) throws RemoteException {
        return globalStatisticsMap.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(10)
            .collect(LinkedHashMap::new, (m, e) -> m.put(e.getKey(), e.getValue()), Map::putAll);
    }

    /**
     * Envia um URL para a Queue.
     *
     * @param url O URL a ser enviada.
     * @throws RemoteException erro na comunicação RMI.
     * @throws IOException erro de I/O.
     * @throws NotBoundException serviço não registado.
     */
    @Override
    public void sendUrlToQueue(String url) throws RemoteException, IOException, NotBoundException  {
        try {
            URLQueueHeader queue = (URLQueueHeader) Naming.lookup("rmi://"+Configuration.RMI_HOST+":"+Configuration.RMI_PORT+"/URLQueue");
            queue.addUrl(url);
            System.out.println("URL sent to the queue via RMI: " + url);
        } catch (Exception e) {
            System.err.println("Failed to send URL to queue via RMI: " + e.getMessage());
        }
    }

    /**
     * Executa uma pesquisa de palavras no index.
     *
     * @param searchWord A palavra ou frase a ser pesquisada.
     * @return Lista de resultados da pesquisa.
     * @throws RemoteException erro na comunicação RMI.
     */
    @Override
    public List<String> searchWords(String searchWord) throws RemoteException {
        try {
            return searchInIndex(searchWord);
        } catch (Exception e) {
            System.err.println("Error searching the centralized index: " + e.getMessage());
            throw new RemoteException("Failed to perform search", e);
        }
    }

    /**
     * Encontra os links que apontam para um URL específica.
     *
     * @param url O URL para o qual se deseja encontrar os links.
     * @return Uma lista de URLs que possuem links para o URL especificado.
     * @throws FileNotFoundException index não encontrado.
     * @throws IOException erro de I/O.
     * @throws NotBoundException serviço não registado.
     */
    @Override
    public List<String> linksToUrl(String url) throws FileNotFoundException, IOException, NotBoundException {
        try {
            return findLinksToUrl(url);
        } catch (Exception e) {
            System.err.println("Error fetching links in centralized index:" + e.getMessage());
            throw new IOException("Failed to fetch links", e);
        }
    }

    /**
     * Liberta recursos ao encerrar o Gateway.
     */
    public void shutdown() {
        saveDataToFiles();

        if (scheduler != null) {
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(60, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
            }
        }

        System.out.println("Gateway terminated.");
    }

    /**
     * Obtém informações sobre os Barrels disponíveis no sistema.
     *
     * @return Um mapa com os nomes dos barrels e suas estatísticas.
     * @throws RemoteException erro na comunicação RMI.
     */
    @Override
    public synchronized Map<String, BarrelStats> getBarrelsInfo() throws RemoteException {
        findAvailableBarrels();
        Map<String, BarrelStats> info = new HashMap<>();
        for (String barrel : availableBarrels) {
            boolean busy = barrelStatus.getOrDefault(barrel, false);
            int count = barrelCounts.getOrDefault(barrel, 0);
            info.put(barrel, new BarrelStats(count, 0.0, busy));
        }
        return info;
    }

    public synchronized void incrementBarrelCount(String barrelName) throws RemoteException {
        barrelCounts.merge(barrelName, 1, Integer::sum);
    }

    /**
     * Método principal que inicia o Gateway e regista o serviço no RMI.
     *
     * @throws IOException erro de I/O.
     * @throws NotBoundException
     */
    public static void main(String[] args) throws IOException, NotBoundException {
        Gateway gateway = new Gateway();

        try {
            try {
                LocateRegistry.createRegistry(Configuration.RMI_PORT);
                System.out.println("RMI Registry created on port " + Configuration.RMI_PORT);
            } catch (RemoteException e) {
                System.out.println("RMI Registry already exists on port " + Configuration.RMI_PORT);
            }

            Naming.rebind("rmi://"+Configuration.RMI_HOST+":"+Configuration.RMI_PORT+"/Gateway", gateway);
            System.out.println("Gateway with centralized index is running.\n");


            final Gateway finalGateway = gateway;
            Runtime.getRuntime().addShutdownHook(new Thread() {
                public void run() {
                    System.out.println("Closing Gateway...");
                    finalGateway.shutdown();
                }
            });

        } catch (Exception e) {
            System.err.println("Error starting Gateway: " + e.getMessage());
            e.printStackTrace();


            if (gateway != null) {
                gateway.shutdown();
            }
        }
    }
}