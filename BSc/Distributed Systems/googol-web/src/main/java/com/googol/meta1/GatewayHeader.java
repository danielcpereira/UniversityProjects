package com.googol.meta1;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.List;
import java.util.Map;

public interface GatewayHeader extends Remote {
    public Map<String, Integer> readStatisticsFromFile(String filePath) throws RemoteException;
    public void sendUrlToQueue(String link) throws RemoteException, IOException, NotBoundException;
    public List<String> linksToUrl(String url) throws FileNotFoundException, IOException, NotBoundException;
    public List<String> searchWords(String searchWord) throws RemoteException;
    public void updateStatistics(String word) throws RemoteException;
    public void addToIndex(String url, String title, String description, List<String> words, List<String> pageLinks) throws RemoteException;
    public List<String> searchInIndex(String searchWord) throws RemoteException, FileNotFoundException, IOException;
    public List<String> findLinksToUrl(String url) throws RemoteException, FileNotFoundException, IOException;
    Map<String, BarrelStats> getBarrelsInfo() throws RemoteException;
    void incrementBarrelCount(String barrelName) throws RemoteException;
}