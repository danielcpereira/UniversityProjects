package com.googol.meta1;
import java.rmi.Naming;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.server.UnicastRemoteObject;
import java.util.LinkedList;
import java.util.Queue;
import java.util.HashSet;
import java.util.Set;

/**
 * Class que implementa a fila de URLs, permitindo adicionar e obter URLs 
 * de forma sincronizada, além de garantir que URLs duplicados não sejam inseridos.
 * Esta classe implementa a interface {@link URLQueueHeader}.
 */
public class URLQueue extends UnicastRemoteObject implements URLQueueHeader {
    private Queue<String> queue;
    private Set<String> visited;

    /**
     * Construtor que inicializa a fila de URLs e o conjunto de URLs visitados.
     * 
     * @throws RemoteException Caso haja falha na inicialização do servidor RMI.
     */
    public URLQueue() throws RemoteException {
        queue = new LinkedList<String>();
        visited = new HashSet<String>();
    }

    /**
     * Adiciona um URL à fila, caso ainda não tenha sido visitado.
     * 
     * @param url O URL a ser adicionado à fila.
     * @throws RemoteException Caso haja falha na comunicação RMI.
     */
    @Override
    public synchronized void addUrl(String url) throws RemoteException {
        if (!visited.contains(url)) {
            queue.add(url);
            visited.add(url);
            System.out.println("URL: " + url + " adicionado à fila");
        }
    }

    /**
     * Obtém e remove o próximo URL da fila. Caso a fila esteja vazia, retorna null.
     * 
     * @return O próximO URL na fila ou null se a fila estiver vazia.
     * @throws RemoteException Caso haja falha na comunicação RMI.
     */
    @Override
    public synchronized String getUrl() throws RemoteException {
        return queue.poll();
    }
    
    /**
     * Método main para iniciar o URLQueue.
     */
    public static void main(String[] args) {
        try {
            try {
                LocateRegistry.createRegistry(Configuration.RMI_PORT);
            } catch (RemoteException e) {
            }
            URLQueue urlQueue = new URLQueue();
            Naming.rebind("rmi://" + Configuration.RMI_HOST + ":" + Configuration.RMI_PORT + "/URLQueue", urlQueue);
            System.out.println("URLQueue is running and registered with RMI.");
        } catch (Exception e) {
            System.err.println("Error initializing URLQueue: " + e.getMessage());
            e.printStackTrace();
        }
    }
}