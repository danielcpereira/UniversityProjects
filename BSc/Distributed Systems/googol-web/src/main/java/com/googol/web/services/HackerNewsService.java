package com.googol.web.services;

import com.googol.web.services.GatewayService;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class HackerNewsService {

    private static final String TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json";
    private static final String ITEM_URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/%d.json";
    private static final String USER_URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/user/%s.json";

    private final RestTemplate restTemplate;
    private final GatewayService gatewayService;

    public HackerNewsService(GatewayService gatewayService) {
        this.restTemplate = new RestTemplate();
        this.gatewayService = gatewayService;
    }

    /**
     * Indexa as top stories que contenham os termos fornecidos
     * e devolve o número de stories efetivamente indexadas.
     */
    public int indexTopStories(String terms) {
        List<Integer> ids = fetchTopStoryIds();
        return indexStoriesByTerms(ids, terms);
    }

    /**
     * Indexa todas as stories de um utilizador do Hacker News
     * e devolve o número de stories efetivamente indexadas.
     */
    public int indexUserStories(String username) {
        List<Integer> ids = fetchUserSubmittedIds(username);
        return indexStoriesByTerms(ids, null);
    }

    private List<Integer> fetchTopStoryIds() {
        Integer[] arr = restTemplate.getForObject(TOP_STORIES_URL, Integer[].class);
        return arr == null ? Collections.emptyList() : Arrays.asList(arr);
    }

    private List<Integer> fetchUserSubmittedIds(String username) {
        Map<?,?> user = restTemplate.getForObject(
                String.format(USER_URL_TEMPLATE, username), Map.class);
        if (user == null || !user.containsKey("submitted")) {
            return Collections.emptyList();
        }
        @SuppressWarnings("unchecked")
        List<Integer> submitted = (List<Integer>) user.get("submitted");
        return submitted;
    }

    /**
     * Faz fetch de cada item, filtra por termos,
     * percorre o HTML do URL, extrai todas as palavras e indexa.
     */
    private int indexStoriesByTerms(List<Integer> ids, String terms) {
        String[] keywords = terms != null ? terms.toLowerCase().split("\\s+") : new String[0];

        int count = 0;
        List<Integer> limited = ids.stream().limit(100).collect(Collectors.toList());
        System.out.println("HackerNews Service: processing " + limited.size() + " items with terms=" + terms);

        for (Integer id : limited) {
            HnItem item = restTemplate.getForObject(String.format(ITEM_URL_TEMPLATE, id), HnItem.class);
            if (item == null || !"story".equals(item.getType()) || item.getUrl() == null) {
                continue;
            }

            if (terms != null) {
                String hnText = (Optional.ofNullable(item.getTitle()).orElse("") + " " + Optional.ofNullable(item.getText()).orElse("")).toLowerCase();
                boolean matches = Arrays.stream(keywords).allMatch(hnText::contains);
                if (!matches) continue;
            }

            String url = item.getUrl();
            System.out.println("HackerNews Service: fetching page " + url);

            String pageText;
            try {
                Document doc = Jsoup.connect(url).userAgent("GoogolBot/1.0").timeout(5000).get();
                pageText = doc.body().text();
            } catch (IOException e) {
                System.err.println("HackerNews Service: failed to fetch " + url + ": " + e.getMessage());
                continue;
            }

            List<String> words = extractWordsFromText(pageText);

            String rawDesc = Optional.ofNullable(item.getText()).orElse("");
            String cleanDesc = rawDesc.replaceAll("<[^>]+>", "");
            if (cleanDesc.length() > 200) {
                cleanDesc = cleanDesc.substring(0, 200);
            }

            gatewayService.addToIndex(url, item.getTitle(), cleanDesc, words, Collections.emptyList());
            count++;
        }

        System.out.println("HackerNews Service: indexed " + count + " stories");
        return count;
    }

    /**
     * Extrai todos os tokens alfanuméricos de um texto, em lower-case.
     */
    private List<String> extractWordsFromText(String text) {
        String[] tokens = text.split("\\W+");
        List<String> result = new ArrayList<>();
        for (String t : tokens) {
            if (t.length() > 1) {
                result.add(t.toLowerCase());
            }
        }
        return result;
    }

    private static class HnItem {
        private String type;
        private String title;
        private String text;
        private String url;

        public String getType() {
            return type;
        }
        public void setType(String type) {
            this.type = type;
        }
        public String getTitle() {
            return title;
        }
        public void setTitle(String title) {
            this.title = title;
        }
        public String getText() {
            return text;
        }
        public void setText(String text) {
            this.text = text;
        }
        public String getUrl() {
            return url;
        }
        public void setUrl(String url) {
            this.url = url;
        }
    }
}
