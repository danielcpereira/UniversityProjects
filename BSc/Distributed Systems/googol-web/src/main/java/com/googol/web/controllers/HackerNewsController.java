package com.googol.web.controllers;

import com.googol.web.services.HackerNewsService;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;


/**
 * Controlador responsável pelos endpoints que indexam
 * as URLs de stories do HackerNews.
 */
@Controller
@RequestMapping("/hn")
public class HackerNewsController {

    private final HackerNewsService hnService;

    /**
     * Construtor
     */
    public HackerNewsController(HackerNewsService hnService) {
        this.hnService = hnService;
    }

    /**
     * POST
     * Indexa as top stories do HackerNews que contenham os termos
     * fornecidos na query string.
     *
     * @param terms termos de pesquisa a procurar nas top stories
     * @return mensagem que indica quantos URLs foram indexados
     */
    @PostMapping("/index-top")
    @ResponseBody
    public ResponseEntity<String> indexTop(@RequestParam String terms) {
        int count = hnService.indexTopStories(terms);
        if (count > 0) {
            return ResponseEntity.ok("Foram indexadas " + count + " top stories com “ " + terms + " ”");
        } else {
            return ResponseEntity.ok("Nenhuma top story encontrada para “ " + terms + " ”");
        }
    }


    /**
     * POST
     * Indexa todas as stories submetidas por um utilizador do HackerNews.
     *
     * @param username nome de utilizador no Hacker News
     * @return mensagem que indica quantas stories do utilizador foram indexadas
     */
    @PostMapping("/index-user")
    @ResponseBody
    public ResponseEntity<String> indexUser(@RequestParam String username) {
        int count = hnService.indexUserStories(username);
        if (count > 0) {
            return ResponseEntity.ok("Foram indexadas " + count + " stories do utilizador “" + username + "”");
        } else {
            return ResponseEntity.ok("O utilizador “" + username + "” não tem stories para indexar");
        }
    }
}
