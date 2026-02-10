package com.googol.meta1;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.Serializable;
import java.rmi.Naming;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.util.List;

/**
 * Esta class implementa o servidor Barrel, responsável por processar dados e
 * encaminhar para o Gateway.
 * Esta classe implementa a interface {@link BarrelHeader}.
 */
public class Barrel extends UnicastRemoteObject implements BarrelHeader, Serializable {
    private final int barrelId;
    private final String barrelName;

    private volatile boolean busy;
    private final BarrelStats stats;

    /**
     * O Construtor do Barrel inicializa o barrel com seu ID.
     *
     * @param id O id do barrel.
     * @throws RemoteException erro de comunicação via RMI.
     */
    public Barrel(int id) throws RemoteException {
        super();
        this.barrelId = id;
        this.barrelName = "Barrel" + id;
        this.busy = false;
        this.stats = new BarrelStats(0, 0.0, false);
    }

    /**
     * Adiciona dados de um URL, incluindo título, descrição, palavras e links.
     * O método atualiza o índice de palavras e os links associados à URL.
     *
     * @param url O URL da página a ser indexada.
     * @param title O título da página.
     * @param description A descrição da página.
     * @param words A lista de palavras encontrados na página.
     * @param pageLinks A lista de links encontrados na página.
     * @throws RemoteException erro de comunicação via RMI.
     */
    @Override
    public void addData(String url, String title, String description, List<String> words, List<String> pageLinks) throws RemoteException {
        try {
            GatewayHeader gateway = (GatewayHeader) Naming.lookup("rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/Gateway");
            gateway.addToIndex(url, title, description, words, pageLinks);
            gateway.incrementBarrelCount(barrelName);
            System.out.printf("Barrel %d forwarded data from URL: %s\n", barrelId, url);
        } catch (Exception e) {
            System.err.println("Error forwarding data to Gateway: " + e.getMessage());
            throw new RemoteException("Failed to add data to index", e);
        }
    }

    /**
     * Esta função realiza uma procura por palavras e retorna os URLs associados com os respetivos títulos e descrições.
     * O método calcula a relevância de cada URL com base nas palavras presentes na busca.
     *
     * @param searchWord A string que contem as palavras a serem pesquisadas.
     * @return Uma lista de strings, onde cada string representa um URL, título e descrição associados.
     * @throws FileNotFoundException Se o ficheiro que armazena o índice não for encontrado.
     * @throws IOException Se ocorrer erro ao ler o ficheiro que armazena o índice.
     */
    @Override
    public List<String> searchWords(String searchWord) throws FileNotFoundException, IOException {
        System.out.println("Barrel " + barrelId + " forwarding search to: " + searchWord);
        try {
            GatewayHeader gateway = (GatewayHeader) Naming.lookup("rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/Gateway");
            return gateway.searchInIndex(searchWord);
        } catch (Exception e) {
            System.err.println("Error forwarding search to Gateway: " + e.getMessage());
            throw new IOException("Failed to perform index search", e);
        }
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
    public List<String> linksToUrl(String url) throws FileNotFoundException, IOException {
        try {
            GatewayHeader gateway = (GatewayHeader) Naming.lookup("rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/Gateway");
            return gateway.findLinksToUrl(url);
        } catch (Exception e) {
            System.err.println("Error forwarding link query to Gateway: " + e.getMessage());
            throw new IOException("Failed to query links in index", e);
        }
    }

    @Override
    public boolean ping() throws RemoteException {
        return true;
    }

    /**
     * Metodo main para iniciar o servidor Barrel com um ID específico.
     *
     * @param args ID do barrel
     */
    public static void main(String[] args) {
        try {
            int barrelId = 0;
            if (args.length > 0) {
                try {
                    barrelId = Integer.parseInt(args[0]);
                    System.out.println("Starting Barrel with ID: " + barrelId);
                } catch (NumberFormatException e) {
                    System.err.println("Invalid barrel ID. Using default ID: " + barrelId);
                }
            } else {
                System.out.println("No barrel ID provided. Using default ID: " + barrelId);
            }

            Registry registry;
            try {
                registry = LocateRegistry.createRegistry(Configuration.RMI_PORT);
                System.out.println("RMI Registry created on port " + Configuration.RMI_PORT);
            } catch (RemoteException e) {
                registry = LocateRegistry.getRegistry(Configuration.RMI_HOST, Configuration.RMI_PORT);
                System.out.println("RMI Registry already exists on port " + Configuration.RMI_PORT);
            }

            Barrel barrel = new Barrel(barrelId);
            String barrelName = "Barrel" + (barrelId > 0 ? barrelId : "");
            Naming.rebind("rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/" + barrelName, barrel);
            System.out.println(barrelName + " is running and registered in RMI.");


            final Registry reg = registry;
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try {
                    reg.unbind(barrelName);
                    System.out.println("Barrel unbound: " + barrelName);
                } catch (Exception ex) {
                    System.err.println("Error unbinding barrel on shutdown: " + ex.getMessage());
                }
            }));

        } catch (Exception e) {
            System.err.println("Error starting Barrel: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
