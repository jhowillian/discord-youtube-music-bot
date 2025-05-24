# Bot de Música no Discord 🎶
=========================

Este bot toca músicas do YouTube em canais de voz do Discord.

## 🎮 Comandos disponíveis
--------------------------
- !play <nome ou URL> – Toca uma música ou playlist do YouTube.
- !skip – Pula para a próxima música na fila.
- !stop – Para a música e desconecta o bot.
- !queue – Mostra a fila de músicas com menu interativo.

## ✏️ Exemplos de uso
---------------------
- '!play https://www.youtube.com/watch?v=jYdaQJzcAcw' → Toca uma música.
- '!play https://www.youtube.com/watch?v=VSj4jZC8oL0&list=RDVSj4jZC8oL0&start_radio=1&rv=VSj4jZC8oL0' → Toca uma playlist.

## 🚀 Como rodar com Docker
---------------------------
### 1. Defina seu token do Discord
No arquivo `docker-compose.yml`, adicione sua chave no ambiente:

```yaml
environment:
  - DISCORD_TOKEN=SEU_TOKEN_AQUI
```

### 2. Execute o bot com Docker

Se estiver usando Docker Compose v2:

```bash
docker compose up --build
```

Ou para versões anteriores:

```bash
docker-compose up --build
```

### 3. Parar o bot

```bash
docker compose down
```

---

## 📸 Imagens de exemplo

### 🎵 Música sendo executada pelo bot
![Bot tocando música](https://cdn.discordapp.com/attachments/1274371226898399287/1375822510209241118/image.png?ex=6833160f&is=6831c48f&hm=384d481f0d2d66d123affa0cb8d9276f4991d7393b8f6332bff311c7610eff0d&)

### 📷 Fila de músicas
![Fila de músicas](https://cdn.discordapp.com/attachments/1274371226898399287/1375822605046780025/image.png?ex=68331626&is=6831c4a6&hm=a314a91bdc49ed832ff9b36458ef2d4431453dd4ac7c7af17b89ca457759e945&)

### 🎚️ Comandos interativos
![Comandos interativos](https://cdn.discordapp.com/attachments/1274371226898399287/1375823370041688084/image.png?ex=683316dc&is=6831c55c&hm=204a8ab8081132ba729385e3e63c9590a2d1c4f51f501b4530dd32bf0005cfc3&)
